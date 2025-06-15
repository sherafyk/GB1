# Gene Due Diligence App

This project was created for the enterprise client **Gene**. Gene is a self‑hosted web application that assists with the risk analysis of international companies. The app is built with **FastAPI** and uses OpenAI models to evaluate uploaded information and produce a markdown report. It is designed to run via Docker but can also be executed directly with Uvicorn for development.

## Features

- Multi‑step wizard to collect company details, deal context and documents
- Automatic text extraction from PDF and image uploads
- AI generated yes/no questions to clarify risk factors (two rounds of ten questions)
- Markdown risk report with overall score, rationale and next steps
- Email delivery of the report (optional SMTP configuration)
- User authentication with an admin panel to manage users and view submission logs
- SQLite database for storing submissions and users

## Repository Layout

```
app/            FastAPI application code
models/         Prompt templates for OpenAI
templates/      Jinja2 templates for the UI
static/         Static assets (CSS/JS)
uploads/        Temporary storage for uploaded files
tests/          Test suite (currently empty)
Dockerfile      Build instructions for the container image
docker-compose.yml  Docker Compose configuration
.env.sample     Example environment variables
apache.conf.sample  Example Apache reverse proxy config
```

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- An OpenAI API key
- Optional: SMTP credentials if you want the report emailed

## Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd GB1
   ```
2. **Create a `.env` file** based on `.env.sample` and fill in the required values:
   ```ini
   OPENAI_API_KEY=your-key
   SMTP_HOST=smtp.example.com
   SMTP_USER=username
   SMTP_PASS=password
   FROM_EMAIL=reports@example.com
  APP_SECRET_KEY=change-me
  # Optional: override where the SQLite DB is stored
  DB_PATH=/app/data/app.db
  ```
  Only `OPENAI_API_KEY` and `APP_SECRET_KEY` are mandatory. Email settings are optional but required for outbound reports.
   Create a local `data/` directory (next to `docker-compose.yml`) if it does not exist. The SQLite file will be stored here.
3. **Build and run the container**
   ```bash
   docker-compose up -d --build
   ```
   The app listens on port **57802** by default and stores uploaded files in the `uploads/` folder. A `data/` directory is mounted into the container for the SQLite database so data persists between runs.
4. **Create an initial admin user**
   ```bash
   docker-compose run app python -m app.create_user admin yourpassword --role admin
   ```
   After the container starts you can visit `http://localhost:57802/login` and sign in.

## Using the Application

1. Log in with your credentials.
2. Click **Start New Assessment** on the landing page to upload your documents.
3. After upload the AI extracts the text and immediately presents ten yes/no questions.
4. Answer the questions (and a second adaptive round) then confirm to run the analysis.
5. When analysis completes you will see the markdown report in the browser. If SMTP is configured it is also emailed to the address specified in `.env`.
6. Admin users can manage accounts and view submission logs under `/admin`.

## Development Workflow

To run the app without Docker:
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 57802
```
Hot reloading is enabled with `--reload` for a faster development cycle.

### Apache Reverse Proxy

For production deployments you can place the app behind Apache. `apache.conf.sample` shows a minimal configuration:
```apache
ProxyPass / http://localhost:57802/
ProxyPassReverse / http://localhost:57802/
```
Ensure HTTPS is configured in front of Apache for secure traffic.

## Updating and Maintenance

Pull the latest changes and rebuild the container:
```bash
git pull
docker-compose down
docker-compose up -d --build
```
View runtime logs with:
```bash
docker logs gb1-app-1 --tail=100
```

## Troubleshooting

- **Cannot log in** &ndash; confirm you created a user and that the database file in `data/` is writable by the container.
- **No email delivered** &ndash; verify SMTP settings in `.env` and check container logs for errors.
- **OpenAI errors** &ndash; ensure `OPENAI_API_KEY` is valid and your account has access to the chosen model.
- **No AI output** &ndash; the application logs a warning if `OPENAI_API_KEY` is missing. Ensure it is set and check logs for API errors.
- **File extraction issues** &ndash; PDF and image extraction rely on `pdfplumber` and `pytesseract`. The Docker image installs the `tesseract-ocr` package so OCR works out of the box. If running locally, ensure Tesseract is installed on your system.
- **Changing the port** &ndash; edit `docker-compose.yml` and the `CMD` in `Dockerfile` if you need a different port.

## Contributing

Pull requests are welcome. Please ensure any new features include adequate documentation and, where possible, tests placed under `tests/`.

