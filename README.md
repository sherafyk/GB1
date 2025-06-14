# GB1 Due Diligence App

This project provides a FastAPI-based web application for AI-driven risk analysis of international companies.

## Requirements
* Docker and Docker Compose

## Quick Start
1. Clone the repository.
2. Copy `.env.sample` to `.env` and set your variables.
3. Build and run the service:
   ```bash
   docker-compose up --build
   ```
4. Open `http://localhost:57802` in your browser to see the landing page.
   From there you can launch the multi-step data collection wizard.

## Development
Run the app directly with uvicorn:
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 57802
```
