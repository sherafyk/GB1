import os
import uuid
from typing import List

import pdfplumber
from PIL import Image
import pytesseract
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import markdown

from .analysis import analyze


UPLOAD_DIR = "uploads"

app = FastAPI()
app.add_middleware(
    SessionMiddleware, secret_key=os.getenv("APP_SECRET_KEY", "secret")
)

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def save_uploads(files: List[UploadFile], folder: str) -> List[str]:
    os.makedirs(folder, exist_ok=True)
    paths = []
    for file in files:
        file_path = os.path.join(folder, file.filename)
        with open(file_path, "wb") as out_file:
            out_file.write(file.file.read())
        paths.append(file_path)
    return paths


def extract_text(path: str) -> str:
    if path.lower().endswith(".pdf"):
        try:
            with pdfplumber.open(path) as pdf:
                return "\n".join([page.extract_text() or "" for page in pdf.pages])
        except Exception:
            return ""
    elif path.lower().endswith((".png", ".jpg", ".jpeg")):
        try:
            return pytesseract.image_to_string(Image.open(path))
        except Exception:
            return ""
    return ""


@app.get("/wizard/company", response_class=HTMLResponse)
async def wizard_company(request: Request):
    data = request.session.get("form", {}).get("company", {})
    return templates.TemplateResponse("company.html", {"request": request, "data": data})


@app.post("/wizard/company")
async def wizard_company_post(request: Request,
                              name: str = Form(...),
                              registration: str = Form(...),
                              address: str = Form(...),
                              country: str = Form(...),
                              directors: str = Form(...)):
    request.session.setdefault("form", {})["company"] = {
        "name": name,
        "registration": registration,
        "address": address,
        "country": country,
        "directors": directors,
    }
    if "upload_id" not in request.session:
        request.session["upload_id"] = str(uuid.uuid4())
    return RedirectResponse(url="/wizard/context", status_code=303)


@app.get("/wizard/context", response_class=HTMLResponse)
async def wizard_context(request: Request):
    data = request.session.get("form", {}).get("context", {})
    return templates.TemplateResponse("context.html", {"request": request, "data": data})


@app.post("/wizard/context")
async def wizard_context_post(request: Request,
                              transaction_type: str = Form(...),
                              description: str = Form(...),
                              notes: str = Form("")):
    request.session.setdefault("form", {})["context"] = {
        "transaction_type": transaction_type,
        "description": description,
        "notes": notes,
    }
    return RedirectResponse(url="/wizard/upload", status_code=303)


@app.get("/wizard/upload", response_class=HTMLResponse)
async def wizard_upload(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/wizard/upload")
async def wizard_upload_post(request: Request, files: List[UploadFile] = File(...)):
    uid = request.session.get("upload_id")
    folder = os.path.join(UPLOAD_DIR, uid)
    paths = save_uploads(files, folder)
    texts = [extract_text(p) for p in paths]
    request.session.setdefault("form", {})["files"] = paths
    request.session["extracted_text"] = "\n".join(texts)
    return RedirectResponse(url="/wizard/review", status_code=303)


@app.get("/wizard/review", response_class=HTMLResponse)
async def wizard_review(request: Request):
    data = request.session.get("form", {})
    extracted = request.session.get("extracted_text", "")
    return templates.TemplateResponse("review.html", {"request": request, "data": data, "extracted": extracted})


@app.post("/wizard/review")
async def wizard_review_post(request: Request):
    return RedirectResponse(url="/wizard/confirm", status_code=303)


@app.get("/wizard/confirm", response_class=HTMLResponse)
async def wizard_confirm(request: Request):
    data = request.session.get("form", {})
    return templates.TemplateResponse("confirm.html", {"request": request, "data": data})


@app.post("/wizard/confirm")
async def wizard_confirm_post(request: Request):
    data = request.session.get("form", {})
    data["extracted_text"] = request.session.get("extracted_text", "")
    report_md = await analyze(data)
    html_report = markdown.markdown(report_md)
    request.session.clear()
    return templates.TemplateResponse(
        "report.html", {"request": request, "report": html_report}
    )
