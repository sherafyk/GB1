"""High level analysis helpers used throughout the application.

The functions in this module wrap calls to the OpenAI API to perform risk
scoring, question generation and document parsing. All OpenAI interactions are
executed in worker threads so that the FastAPI event loop remains responsive.
If the ``OPENAI_API_KEY`` environment variable is not set the functions will
log a warning and return fallback values.
"""

import os
import json
import asyncio
import smtplib
import logging
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

# Fallback questions are used if the OpenAI API call fails so the UI still
# displays something useful. These cover common due diligence topics.
FALLBACK_QUESTIONS = [
    "Is the company's registration current and valid?",
    "Are any directors or owners politically exposed persons?",
    "Is the company's address located in a high-risk jurisdiction?",
    "Has the company or its owners been involved in litigation?",
    "Has the company filed audited financial statements recently?",
    "Are there any outstanding tax or regulatory issues?",
    "Has negative media coverage been identified?",
    "Is the beneficial ownership structure transparent?",
    "Have any sanctions lists flagged the company or owners?",
    "Are there undisclosed related-party transactions?",
]

import openai

from .db import log_submission
from models import prompts


logger = logging.getLogger(__name__)

# Configure the OpenAI library. If the API key is missing we log a warning so it
# is obvious why AI features may not work.
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logger.warning("OPENAI_API_KEY is not set; AI analysis will be disabled")

MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")


def _call_openai(prompt: str) -> str:
    """Helper that sends ``prompt`` to OpenAI and returns the raw text response."""
    try:
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        # Any API failure is logged with stack trace so issues can be debugged
        logger.error("OpenAI API call failed: %s", exc, exc_info=True)
        raise


async def analyze_chunk(kind: str, content: str) -> dict:
    """Analyze a single piece of content using the template for ``kind``."""

    # The prompt templates live in :mod:`models.prompts`. ``kind`` selects which
    # template to use (company, context, etc.). The ``content`` is inserted into
    # that template before sending to the language model.
    prompt = prompts.PROMPTS[kind].format(data=content)

    def run():
        try:
            text = _call_openai(prompt)
            # Each analysis prompt should return a JSON document. If parsing
            # fails we fall back to neutral values so the workflow continues.
            return json.loads(text)
        except Exception:
            return {"score": 50, "rationale": "N/A", "next_steps": "N/A"}

    # ``openai`` calls are blocking so we offload them to a thread to keep the
    # FastAPI event loop responsive.
    return await asyncio.to_thread(run)


async def generate_questions(data: dict) -> list:
    """Generate the first round of 10 yes/no questions based on ``data``."""

    text = data.get("extracted_text", "")
    prompt = prompts.PROMPTS["question_gen"].format(data=text[:4000])

    def run():
        try:
            return _call_openai(prompt)
        except Exception as exc:
            logger.error("Failed to generate questions: %s", exc, exc_info=True)
            return ""

    # ``openai`` call is executed in a worker thread so the API remains async.
    text = await asyncio.to_thread(run)

    # The response is expected to be a numbered list. We clean each line and
    # strip any leading digits or punctuation to get just the question text.
    questions = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = line.lstrip("0123456789.- ")
        questions.append(line)
    # If the API call failed or returned nothing, fall back to generic questions
    # so the workflow can continue.
    if not questions:
        questions = FALLBACK_QUESTIONS.copy()

    # Only return the first 10 items to guard against prompt injection or
    # unexpected long replies.
    return questions[:10]


async def generate_followups(data: dict, answers: list) -> list:
    """Generate the second round of adaptive questions based on user answers."""

    payload = json.dumps({"text": data.get("extracted_text", ""), "answers": answers})
    prompt = prompts.PROMPTS["followup_gen"].format(data=payload)

    def run():
        try:
            return _call_openai(prompt)
        except Exception as exc:
            logger.error(
                "Failed to generate follow-up questions: %s", exc, exc_info=True
            )
            return ""

    text = await asyncio.to_thread(run)
    questions = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = line.lstrip("0123456789.- ")
        questions.append(line)
    if not questions:
        questions = FALLBACK_QUESTIONS.copy()
    return questions[:10]


async def extract_structured_data(text: str) -> dict:
    """Use the language model to pull structured fields from raw ``text``."""

    prompt = prompts.PROMPTS["extract"].format(data=text[:4000])

    def run():
        try:
            resp = _call_openai(prompt)
            return json.loads(resp)
        except Exception as exc:
            logger.error("Structured data extraction failed: %s", exc, exc_info=True)
            return {"company": {}, "context": {}}

    return await asyncio.to_thread(run)


async def analyze(data: dict, qa: list | None = None) -> str:
    """Run the full multi-part analysis and return a markdown report."""

    chunks = {
        "company": json.dumps(data.get("company", {})),
        "context": json.dumps(data.get("context", {})),
    }
    if data.get("extracted_text"):
        chunks["documents"] = data["extracted_text"][:4000]
    if qa:
        chunks["qa"] = json.dumps(qa)

    # Run each analysis chunk sequentially. Each chunk produces a score,
    # rationale and next steps which are later combined into the report.
    results = {}
    for kind, text in chunks.items():
        results[kind] = await analyze_chunk(kind, text)

    # Average all scores for a simple overall rating.
    overall = sum(r["score"] for r in results.values()) / len(results)

    md_lines = ["# Risk Analysis Report", f"**Overall Risk Score:** {overall:.1f}", ""]
    name_map = {
        "company": "Company Info",
        "context": "Deal Context",
        "documents": "Documents",
        "qa": "Q&A",
    }
    for kind, res in results.items():
        md_lines.append(f"## {name_map.get(kind, kind.title())}")
        md_lines.append(f"- **Score:** {res['score']}")
        md_lines.append(f"- **Rationale:** {res['rationale']}")
        md_lines.append(f"- **Next Steps:** {res['next_steps']}")
        md_lines.append("")

    if qa:
        md_lines.append("## Q&A Summary")
        md_lines.append("| # | Question | Answer | Context |")
        md_lines.append("|---|----------|-------|---------|")
        for i, item in enumerate(qa, 1):
            md_lines.append(
                f"| {i} | {item['question']} | {item['answer']} | {item.get('context','')} |"
            )
        md_lines.append("")

    md_lines.append(
        "_This is an AI-driven risk analysis. Use in conjunction with human judgment._"
    )
    report = "\n".join(md_lines)

    if qa:
        data = dict(data)
        data["qa"] = qa
    # Persist the submission and email the report if SMTP settings are present.
    log_submission(data, report, overall)
    await send_email(report)

    return report


async def send_email(report: str) -> None:
    """Send ``report`` via SMTP if credentials are configured."""

    host = os.getenv("SMTP_HOST")
    user = os.getenv("SMTP_USER")
    pwd = os.getenv("SMTP_PASS")
    from_addr = os.getenv("FROM_EMAIL")
    to_addr = os.getenv("FROM_EMAIL")

    # All four pieces of information must be present, otherwise we silently skip
    # sending email. This keeps the application functional even without SMTP.
    if not all([host, user, pwd, from_addr]):
        return

    msg = EmailMessage()
    msg["Subject"] = "GB1 Risk Analysis Report"
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(report)

    def run():
        with smtplib.SMTP(host) as s:
            s.starttls()
            s.login(user, pwd)
            s.send_message(msg)

    # ``smtplib`` is blocking; run in a thread to avoid blocking the event loop.
    await asyncio.to_thread(run)
