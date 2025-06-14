import os
import json
import asyncio
import smtplib
from email.message import EmailMessage

import openai

from .db import log_submission
from models import prompts

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")


def _call_openai(prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


async def analyze_chunk(kind: str, content: str) -> dict:
    prompt = prompts.PROMPTS[kind].format(data=content)

    def run():
        try:
            text = _call_openai(prompt)
            return json.loads(text)
        except Exception:
            return {"score": 50, "rationale": "N/A", "next_steps": "N/A"}

    return await asyncio.to_thread(run)


async def generate_questions(data: dict) -> list:
    prompt = prompts.PROMPTS["question_gen"].format(data=json.dumps(data))

    def run():
        return _call_openai(prompt)

    text = await asyncio.to_thread(run)
    questions = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = line.lstrip("0123456789.- ")
        questions.append(line)
    return questions[:10]


async def generate_followups(data: dict, answers: list) -> list:
    payload = json.dumps({"data": data, "answers": answers})
    prompt = prompts.PROMPTS["followup_gen"].format(data=payload)

    def run():
        return _call_openai(prompt)

    text = await asyncio.to_thread(run)
    questions = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = line.lstrip("0123456789.- ")
        questions.append(line)
    return questions[:10]


async def extract_structured_data(text: str) -> dict:
    prompt = prompts.PROMPTS["extract"].format(data=text[:4000])

    def run():
        try:
            resp = _call_openai(prompt)
            return json.loads(resp)
        except Exception:
            return {"company": {}, "context": {}}

    return await asyncio.to_thread(run)


async def analyze(data: dict, qa: list | None = None) -> str:
    chunks = {
        "company": json.dumps(data.get("company", {})),
        "context": json.dumps(data.get("context", {})),
    }
    if data.get("extracted_text"):
        chunks["documents"] = data["extracted_text"][:4000]
    if qa:
        chunks["qa"] = json.dumps(qa)

    results = {}
    for kind, text in chunks.items():
        results[kind] = await analyze_chunk(kind, text)

    overall = sum(r["score"] for r in results.values()) / len(results)

    md_lines = ["# Risk Analysis Report", f"**Overall Risk Score:** {overall:.1f}", ""]
    name_map = {"company": "Company Info", "context": "Deal Context", "documents": "Documents", "qa": "Q&A"}
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
            md_lines.append(f"| {i} | {item['question']} | {item['answer']} | {item.get('context','')} |")
        md_lines.append("")

    md_lines.append("_This is an AI-driven risk analysis. Use in conjunction with human judgment._")
    report = "\n".join(md_lines)

    if qa:
        data = dict(data)
        data["qa"] = qa
    log_submission(data, report, overall)
    await send_email(report)

    return report


async def send_email(report: str):
    host = os.getenv("SMTP_HOST")
    user = os.getenv("SMTP_USER")
    pwd = os.getenv("SMTP_PASS")
    from_addr = os.getenv("FROM_EMAIL")
    to_addr = os.getenv("FROM_EMAIL")

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

    await asyncio.to_thread(run)
