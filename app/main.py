"""FastAPI application providing the web interface and API endpoints."""

import os
import uuid
from typing import List
import subprocess

from dotenv import load_dotenv

load_dotenv()

import pdfplumber
from PIL import Image
import pytesseract
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
import bleach
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import markdown

from . import db

from .analysis import analyze_document


UPLOAD_DIR = "uploads"

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("APP_SECRET_KEY", "secret"))

templates = Jinja2Templates(directory="templates")


def get_last_updated() -> str:
    """Return the timestamp of the last Git commit."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    try:
        out = subprocess.check_output(
            [
                "git",
                "log",
                "-1",
                "--format=%cd",
                "--date=format:%Y-%m-%d-%H:%M",
            ],
            cwd=repo_root,
        )
        return out.decode().strip()
    except Exception:
        return ""


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
    last_updated = get_last_updated()
    return templates.TemplateResponse(
        "index.html", {"request": request, "last_updated": last_updated}
    )


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
        # ``UploadFile.filename`` may include directory components from the
        # client's system. ``basename`` prevents directory traversal attacks.
        name = os.path.basename(file.filename)
        ext = os.path.splitext(name)[1].lower()
        if ext not in [".pdf", ".png", ".jpg", ".jpeg"]:
            continue
        content = file.file.read()
        if len(content) > 5 * 1024 * 1024:
            continue
        name = f"{uuid.uuid4().hex}_{name}"
        file_path = os.path.join(folder, name)
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
    # Ensure an upload ID exists so the POST handler always has a valid path
    # even if the user skips directly to the upload form. ``setdefault`` avoids
    # overwriting an existing value.
    request.session.setdefault("upload_id", str(uuid.uuid4()))
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/wizard/upload")
async def wizard_upload_post(request: Request, files: List[UploadFile] = File(...)):
    """Handle document uploads and immediately run the analysis."""
    resp = require_user(request)
    if resp:
        return resp
    uid = str(uuid.uuid4())
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
    try:
        report_md = await analyze_document(combined)
    except Exception as exc:
        return templates.TemplateResponse(
            "upload.html",
            {"request": request, "error": str(exc)},
            status_code=500,
        )
    html_report = markdown.markdown(report_md)
    html_report = bleach.clean(
        html_report,
        tags=bleach.sanitizer.ALLOWED_TAGS + ["p", "h1", "h2", "h3", "table", "tr", "th", "td"],
        attributes={"a": ["href", "title"], "img": ["src", "alt"]},
    )
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
