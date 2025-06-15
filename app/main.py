"""FastAPI application providing the web interface and API endpoints."""

import os
import uuid
from typing import List

from dotenv import load_dotenv

load_dotenv()

import pdfplumber
from PIL import Image
import pytesseract
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import markdown

from . import db

from .analysis import (
    analyze,
    generate_context_questions,
    generate_questions,
    generate_followups,
    extract_structured_data,
)


UPLOAD_DIR = "uploads"

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("APP_SECRET_KEY", "secret"))

templates = Jinja2Templates(directory="templates")


def get_current_user(request: Request):
    """Return the currently logged in user from the session or ``None``."""
    return request.session.get("user")


def require_user(request: Request):
    """Redirect to the login page if the request is unauthenticated."""
    if not get_current_user(request):
        return RedirectResponse(url="/login", status_code=303)


def require_admin(request: Request):
    """Ensure the user has admin role otherwise redirect to home."""
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/", status_code=303)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the landing page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    """Display the login form."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login_post(
    request: Request, username: str = Form(...), password: str = Form(...)
):
    """Handle login form submission."""
    user = db.verify_user(username, password)
    if user:
        request.session["user"] = user
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Invalid credentials"},
        status_code=400,
    )


@app.get("/logout")
async def logout(request: Request):
    """Log out the current user and redirect to login."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


def save_uploads(files: List[UploadFile], folder: str) -> List[str]:
    """Persist uploaded files to ``folder`` and return their paths."""

    os.makedirs(folder, exist_ok=True)
    paths = []
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".pdf", ".png", ".jpg", ".jpeg"]:
            continue
        content = file.file.read()
        if len(content) > 5 * 1024 * 1024:
            continue
        file_path = os.path.join(folder, file.filename)
        with open(file_path, "wb") as out_file:
            out_file.write(content)
        paths.append(file_path)
    return paths


def extract_text(path: str) -> str:
    """Extract text from a PDF or image file."""
    if path.lower().endswith(".pdf"):
        try:
            with pdfplumber.open(path) as pdf:
                # ``pdfplumber`` returns one object per page; we join them into
                # a single string for analysis.
                return "\n".join([page.extract_text() or "" for page in pdf.pages])
        except Exception as exc:
            raise RuntimeError(f"Failed to read PDF {path}: {exc}")
    elif path.lower().endswith((".png", ".jpg", ".jpeg")):
        try:
            # OCR the image using Tesseract.
            return pytesseract.image_to_string(Image.open(path))
        except Exception as exc:
            raise RuntimeError(f"Failed to OCR image {path}: {exc}")
    else:
        raise RuntimeError(f"Unsupported file type: {path}")




@app.get("/wizard/upload", response_class=HTMLResponse)
async def wizard_upload(request: Request):
    """Show the file upload page."""
    resp = require_user(request)
    if resp:
        return resp
    if "upload_id" not in request.session:
        request.session["upload_id"] = str(uuid.uuid4())
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/wizard/upload")
async def wizard_upload_post(request: Request, files: List[UploadFile] = File(...)):
    """Handle document uploads and perform initial text extraction."""
    resp = require_user(request)
    if resp:
        return resp
    uid = request.session.get("upload_id")
    folder = os.path.join(UPLOAD_DIR, uid)
    paths = save_uploads(files, folder)
    try:
        texts = [extract_text(p) for p in paths]
    except Exception as exc:
        return templates.TemplateResponse(
            "upload.html",
            {"request": request, "error": str(exc)},
            status_code=400,
        )
    combined = "\n".join(texts)
    form = request.session.setdefault("form", {})
    form["files"] = paths
    request.session["extracted_text"] = combined
    form["extracted_text"] = combined
    structured = await extract_structured_data(combined)
    form["company"] = structured.get("company", {})
    form["context"] = structured.get("context", {})
    try:
        context_q = await generate_context_questions(combined)
    except Exception as exc:
        return templates.TemplateResponse(
            "upload.html",
            {"request": request, "error": f"Failed to generate context questions: {exc}"},
            status_code=500,
        )
    request.session["context_questions"] = context_q
    return RedirectResponse(url="/wizard/context", status_code=303)


@app.get("/wizard/context", response_class=HTMLResponse)
async def wizard_context(request: Request):
    """Display short context questions for the user."""
    resp = require_user(request)
    if resp:
        return resp
    questions = request.session.get("context_questions", [])
    return templates.TemplateResponse(
        "short_questions.html",
        {
            "request": request,
            "questions": questions,
            "step": "Step 2 of 5: Provide Context",
            "post_url": "/wizard/context",
        },
    )


@app.post("/wizard/context")
async def wizard_context_post(request: Request):
    """Handle answers to the context questions and fetch yes/no questions."""
    resp = require_user(request)
    if resp:
        return resp
    form = await request.form()
    questions = request.session.get("context_questions", [])
    answers = []
    for i, q in enumerate(questions, 1):
        ans = form.get(f"q{i}")
        if not ans:
            return templates.TemplateResponse(
                "short_questions.html",
                {
                    "request": request,
                    "questions": questions,
                    "step": "Step 2 of 5: Provide Context",
                    "post_url": "/wizard/context",
                    "error": "Please answer all questions",
                },
                status_code=400,
            )
        answers.append({"question": q, "answer": ans})
    request.session["context_answers"] = answers
    data = request.session.get("form", {})
    data["context_answers"] = answers
    try:
        questions = await generate_questions(data)
    except Exception as exc:
        return templates.TemplateResponse(
            "short_questions.html",
            {
                "request": request,
                "questions": questions,
                "step": "Step 2 of 5: Provide Context",
                "post_url": "/wizard/context",
                "error": f"Failed to generate questions: {exc}",
            },
            status_code=500,
        )
    request.session["questions_round1"] = questions
    return RedirectResponse(url="/wizard/questions1", status_code=303)




@app.get("/wizard/questions1", response_class=HTMLResponse)
async def wizard_questions1(request: Request):
    """Display the first set of AI-generated questions."""
    resp = require_user(request)
    if resp:
        return resp
    questions = request.session.get("questions_round1", [])
    return templates.TemplateResponse(
        "questions.html",
        {
            "request": request,
            "questions": questions,
            "step": "Step 3 of 5: Answer 10 Key Questions",
            "post_url": "/wizard/questions1",
        },
    )


@app.post("/wizard/questions1")
async def wizard_questions1_post(request: Request):
    """Process answers to the first question round and fetch follow-ups."""
    resp = require_user(request)
    if resp:
        return resp
    form = await request.form()
    questions = request.session.get("questions_round1", [])
    answers = []
    for i, q in enumerate(questions, 1):
        ans = form.get(f"q{i}")
        if not ans:
            return templates.TemplateResponse(
                "questions.html",
                {
                    "request": request,
                    "questions": questions,
                    "step": "Step 3 of 5: Answer 10 Key Questions",
                    "post_url": "/wizard/questions1",
                    "error": "Please answer all questions",
                },
                status_code=400,
            )
        ctx = form.get(f"q{i}_context", "")
        answers.append({"question": q, "answer": ans, "context": ctx})
    request.session["answers_round1"] = answers
    data = request.session.get("form", {})
    try:
        followups = await generate_followups(data, answers)
    except Exception as exc:
        return templates.TemplateResponse(
            "questions.html",
            {
                "request": request,
                "questions": questions,
                "step": "Step 3 of 5: Answer 10 Key Questions",
                "post_url": "/wizard/questions1",
                "error": f"Failed to generate follow-up questions: {exc}",
            },
            status_code=500,
        )
    request.session["questions_round2"] = followups
    return RedirectResponse(url="/wizard/questions2", status_code=303)


@app.get("/wizard/questions2", response_class=HTMLResponse)
async def wizard_questions2(request: Request):
    """Display the second adaptive question round."""
    resp = require_user(request)
    if resp:
        return resp
    questions = request.session.get("questions_round2", [])
    return templates.TemplateResponse(
        "questions.html",
        {
            "request": request,
            "questions": questions,
            "step": "Step 4 of 5: Answer Follow-Up Questions",
            "post_url": "/wizard/questions2",
        },
    )


@app.post("/wizard/questions2")
async def wizard_questions2_post(request: Request):
    """Handle answers from the second round of questions."""
    resp = require_user(request)
    if resp:
        return resp
    form = await request.form()
    questions = request.session.get("questions_round2", [])
    answers = []
    for i, q in enumerate(questions, 1):
        ans = form.get(f"q{i}")
        if not ans:
            return templates.TemplateResponse(
                "questions.html",
                {
                    "request": request,
                    "questions": questions,
                    "step": "Step 4 of 5: Answer Follow-Up Questions",
                    "post_url": "/wizard/questions2",
                    "error": "Please answer all questions",
                },
                status_code=400,
            )
        ctx = form.get(f"q{i}_context", "")
        answers.append({"question": q, "answer": ans, "context": ctx})
    request.session["answers_round2"] = answers
    return RedirectResponse(url="/wizard/confirm", status_code=303)


@app.get("/wizard/confirm", response_class=HTMLResponse)
async def wizard_confirm(request: Request):
    """Show a summary and let the user trigger the final analysis."""
    resp = require_user(request)
    if resp:
        return resp
    data = request.session.get("form", {})
    return templates.TemplateResponse(
        "confirm.html", {"request": request, "data": data}
    )


@app.post("/wizard/confirm")
async def wizard_confirm_post(request: Request):
    """Run the analysis and display the final markdown report."""
    resp = require_user(request)
    if resp:
        return resp
    data = request.session.get("form", {})
    data["extracted_text"] = request.session.get("extracted_text", "")
    data["context_answers"] = request.session.get("context_answers", [])
    qa = (
        request.session.get("context_answers", [])
        + request.session.get("answers_round1", [])
        + request.session.get("answers_round2", [])
    )
    report_md = await analyze(data, qa)
    html_report = markdown.markdown(report_md)
    request.session.clear()
    return templates.TemplateResponse(
        "report.html", {"request": request, "report": html_report}
    )


@app.get("/admin", response_class=HTMLResponse)
async def admin_index(request: Request):
    """Admin dashboard landing page."""
    resp = require_admin(request)
    if resp:
        return resp
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users(request: Request):
    """List all users and provide management actions."""
    resp = require_admin(request)
    if resp:
        return resp
    users = db.list_users()
    return templates.TemplateResponse(
        "admin_users.html", {"request": request, "users": users}
    )


@app.post("/admin/users/add")
async def admin_users_add(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("user"),
):
    """Create a new user account."""
    resp = require_admin(request)
    if resp:
        return resp
    db.create_user(username, password, role)
    return RedirectResponse(url="/admin/users", status_code=303)


@app.post("/admin/users/delete")
async def admin_users_delete(request: Request, username: str = Form(...)):
    """Delete the specified user account."""
    resp = require_admin(request)
    if resp:
        return resp
    db.delete_user(username)
    return RedirectResponse(url="/admin/users", status_code=303)


@app.get("/admin/logs", response_class=HTMLResponse)
async def admin_logs(request: Request):
    """Display recent submission logs."""
    resp = require_admin(request)
    if resp:
        return resp
    logs = db.get_logs()
    return templates.TemplateResponse(
        "admin_logs.html", {"request": request, "logs": logs}
    )
