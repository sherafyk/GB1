# AGENTS.md

**Purpose:**
This file instructs OpenAI Codex (and any human developer) on how to build a turnkey, secure, and responsive web app for AI-driven due diligence of international companies. The project is divided into four clear sections for iterative, chunked development.
**Goal:**
A self-hosted, dark-themed, Python-based web app that processes company data and documents, analyzes risk using OpenAI models, and outputs actionable reports.

---

## Section 1: Project Bootstrap & Core Architecture

**Objective:**
Initialize the repository, set up the backend framework, core file structure, and ensure Dockerized deployment for easy setup on any server (Debian 12 + Apache preferred).

**Instructions:**

1. **Initialize the Repository**

   * Set up a new Git repository.
   * Add a `.gitignore` file (Python, Docker, OS-generated files).

2. **Backend Framework**

   * Use FastAPI as the Python backend (simple, async, excellent OpenAI support).
   * Add necessary requirements:
     `fastapi`, `uvicorn[standard]`, `python-multipart`, `aiofiles`, `pydantic`, `httpx`, `jinja2`, `openai`, `python-dotenv`, `tqdm` (for progress), `pdfplumber`, `pytesseract`, `Pillow`, `textract` (for file parsing), `sqlite3` (for lightweight DB).
   * Add a basic `main.py` file with FastAPI “Hello World”.

3. **Core File Structure**

   * Root-level folders:

     * `/app` (all Python code)
     * `/static` (css, images, icons)
     * `/templates` (Jinja2 for initial HTML, wizard form, report)
     * `/uploads` (temporary file storage)
     * `/models` (prompt templates, future AI logic)
     * `/tests` (unit/integration tests)
   * Add a sample `.env` file for environment variables (API keys, SMTP settings, etc.).

4. **Dockerization**

   * Write a `Dockerfile` that builds a minimal FastAPI app.
   * Write a `docker-compose.yml` with one service for the app, mapped to port 57802 (internally) and 57802 (host).
   * Include documentation in `README.md` for building and running via Docker.

5. **Initial Commit**

   * Confirm all basic setup, app can run with `docker-compose up` and serve a root landing page.

---

## Section 2: User Interface & Data Collection Wizard

**Objective:**
Build a modern, responsive, dark-mode UI using Jinja2 and TailwindCSS (no heavy JS frameworks for MVP), with a multi-step wizard for collecting company info, deal context, and uploading files.

**Instructions:**

1. **UI Theming**

   * Install and configure TailwindCSS for dark mode by default.
   * Create base layout template (`base.html`), with a modern, professional look (header, sidebar optional, dark background, legible fonts, accent colors for buttons/alerts).

2. **Wizard Structure**

   * Multi-step form (Jinja2 + basic JavaScript for navigation, or one route per step).
   * Steps:

     1. Company details (name, registration, address, country, directors/owners)
     2. Deal context (type of transaction, description, unstructured notes)
     3. Document upload (support PDF, image; allow multiple files; show upload progress)
     4. Data review/edit (auto-extracted data shown; allow user to confirm/correct)
     5. Confirmation (submit for AI analysis)

3. **File Handling**

   * Store uploaded files in `/uploads` (use unique IDs/folders per submission).
   * Implement PDF/image text extraction using `pdfplumber`, `pytesseract`, and/or `textract`.
   * Clean up files after processing (or set up periodic cleanup for temp storage).

4. **Input Validation**

   * Validate required fields on each step (front- and backend).
   * Show user-friendly error messages.
   * Sanitize all user input.

5. **Responsiveness**

   * Ensure forms and report pages are mobile-friendly.
   * Test in Chrome, Firefox, Safari.

---

## Section 3: AI Risk Analysis Engine & Prompt Workflow

**Objective:**
Design and implement the backend logic for AI-driven risk analysis using modular, tiered prompts and OpenAI API calls. Ensure explainability and scoring, returning markdown output.

**Instructions:**

1. **Prompt Design**

   * Use clear, modular prompt templates for:

     * Company info chunk
     * Deal context chunk
     * Extracted document chunk
     * Enriched web/public data chunk
   * Prompts should instruct the model to score risk (0-100), provide a rationale, and recommend practical next steps.
   * Example (use/adapt for each chunk):

     ```
     Analyze the following company information for fraud and business risk. Assign a risk score (0-100), explain your reasoning in plain English, and suggest practical next steps for due diligence.
     ```

2. **Model Selection & API Integration**

   * Start with `gpt-4o` or `gpt-3.5-turbo` for all chunks; make model configurable per chunk.
   * Securely load OpenAI API key from environment variable.
   * Asynchronously call models for each input chunk, then aggregate results.

3. **Scoring & Aggregation**

   * For each chunk, collect:

     * Risk score (0-100)
     * 2-3 sentence rationale
     * Next steps
   * Aggregate chunk scores to compute an overall risk score (weighted or simple average).
   * Generate a markdown report with:

     * Section for each chunk
     * Overall risk score and visual indicator (progress bar, color-coded)
     * Human-readable summary and actionable next steps

4. **Explainability**

   * Ensure all outputs are at 11th grade reading level.
   * Summarize final determination clearly (e.g., “This company is high risk because X, Y, Z. You should request audited financials before proceeding.”)
   * Include a disclaimer: “This is an AI-driven risk analysis. Use in conjunction with human judgment.”

5. **Email & History**

   * Email the markdown report to the user/admin via SMTP.
   * Log each submission and output in the database for future search and review.

---

## Section 4: Security, Admin Panel, & Deployment

**Objective:**
Implement user authentication, basic admin controls, and finalize deployment for production use. Document the process for turnkey setup.

**Instructions:**

1. **User Authentication**

   * Implement a simple login system with two roles: Admin, User.
   * Store passwords hashed (use bcrypt or similar).
   * Allow user registration/invite only via admin.

2. **Admin Panel**

   * Simple interface to:

     * Manage users (add, delete, change roles)
     * View submission logs
     * Re-run AI analysis on past entries (future)
     * Configure API keys and model selection (env or .env editable)

3. **Security Best Practices**

   * Sanitize all inputs and outputs to prevent injection.
   * Restrict file types for upload (PDF, PNG, JPG).
   * Limit file size uploads.
   * Use HTTPS for all production deployments.
   * Ensure all sensitive settings (API keys, SMTP credentials) are stored in `.env` and never checked into version control.
   * Regularly delete temp uploads.

4. **Deployment**

   * Build and run the app with Docker Compose (`docker-compose up -d`).
   * Serve via Apache reverse proxy (sample `apache.conf` provided).
   * Document all steps in `README.md` (clone, set env, build, run, open in browser).
   * Provide sample `.env` for required variables:

     * `OPENAI_API_KEY`
     * `SMTP_HOST`
     * `SMTP_USER`
     * `SMTP_PASS`
     * `FROM_EMAIL`
     * `APP_SECRET_KEY`

---

# Summary Table

| Section                  | Agent Role     | Key Outputs                          |
| ------------------------ | -------------- | ------------------------------------ |
| Project Bootstrap & Core | Infra Agent    | Repo, FastAPI, Docker setup          |
| UI & Data Collection     | UI Agent       | Tailwind/Jinja2 dark wizard, uploads |
| AI Engine & Prompts      | AI Agent       | Modular prompts, scoring, markdown   |
| Security/Admin/Deploy    | Security Agent | Auth, admin, production deploy       |

---

**Note to Codex:**
Follow each section in sequence. At the end of each, validate working state (minimal viable function), commit code, and prompt for the next section.

---
That’s an excellent and practical addition. This interactive Q\&A loop will make your risk engine far more robust—allowing the AI to dig deeper, clarify uncertainties, and surface hidden red flags using an adaptive, two-round questioning system. Here’s how you should specify and document this “Dynamic Questioning” system for Codex (and for future contributors).

Below is an **addendum** for your AGENTS.md file. This describes the Q\&A loop, data handling, UI/UX, and how the logic should work—written for direct inclusion as **Section 5** or as a detailed sub-section of the AI Risk Analysis Engine.

---

## Section 5: Dynamic Interactive Q\&A Module

**Objective:**
Enhance the risk analysis workflow by having the AI generate and present two rounds of 10 yes/no questions to the user. These questions should maximize discovery of material risk factors, resolve uncertainties, and allow the model to probe deeper based on user context.

**Instructions:**

### 1. **Initial Analysis and Question Generation**

* After the user submits company details, deal notes, and document uploads, run the initial AI risk assessment as specified in Section 3.
* **Prompt the AI**:
  “Based on your analysis of the following company data and context, generate a list of the 10 most important yes/no questions for the user to answer. These should be designed to extract any missing or clarifying information that would materially affect the risk assessment. Phrase each question in clear, plain English suitable for a non-expert user.”
* Parse the AI’s response into a clean, numbered list of 10 yes/no questions.

### 2. **User Response Interface**

* **Display the 10 questions** as a vertical list.
* For each question, provide:

  * Two radio buttons: **Yes** | **No**
  * A small text box underneath labeled:
    *“Optional: Add more context or clarification (if needed)”*
* Validate all 10 questions are answered (yes or no); optional text box can be empty.
* Allow the user to submit all answers in one batch.

### 3. **Follow-Up Questions (Adaptive Loop)**

* After the user submits the first 10 answers, pass both the original context and all user answers (including optional text) to the AI.
* **Prompt the AI**:
  “Given the company information, previous analysis, and the user’s answers to the first 10 yes/no questions (with optional clarifications), generate 10 additional yes/no questions that would further clarify the risk or address remaining uncertainties. These can follow up on previous answers or introduce new lines of inquiry as needed. Phrase each question clearly and simply.”
* Display the new 10 questions to the user with the same yes/no radio and optional text box format.

### 4. **Integration with Final Risk Assessment**

* After both rounds of user input, compile all original data, extracted documents, and the 20 Q\&A responses into the final AI analysis.
* Instruct the AI to update its risk score, rationale, and next steps based on the full information set.
* The markdown report should include a summary table showing all 20 questions and user responses.

### 5. **User Experience & Flow**

* Use a step-by-step “wizard” UX:

  1. Initial data upload and review
  2. **Q\&A Round 1** (10 questions)
  3. **Q\&A Round 2** (10 adaptive follow-ups)
  4. Final risk analysis and markdown report
* Clearly indicate progress (e.g., “Step 2 of 4: Answer 10 Key Questions”) so users know what to expect.

### 6. **Best Practices**

* Ensure questions are phrased neutrally, without bias or leading language.
* If the AI generates unclear or repetitive questions, allow the user to flag or skip (future enhancement).
* Log all user responses with timestamp for audit and review.

---

**Sample Prompts for Codex Integration:**

* *“Given all submitted data, what are the 10 most important yes/no questions to clarify risk?”*
* *“Based on these user answers, what 10 additional yes/no questions would resolve further uncertainty?”*

---

**UI/UX Example (Jinja2/Tailwind):**

```html
{% for q in questions %}
  <div class="mb-6 p-4 bg-gray-800 rounded-xl shadow">
    <label class="block text-lg text-gray-200 font-semibold mb-2">{{ loop.index }}. {{ q.text }}</label>
    <div class="flex gap-8 mb-2">
      <label><input type="radio" name="q{{loop.index}}" value="Yes" required> Yes</label>
      <label><input type="radio" name="q{{loop.index}}" value="No" required> No</label>
    </div>
    <textarea name="q{{loop.index}}_context" rows="2" class="w-full rounded-md bg-gray-900 text-gray-200 p-2" placeholder="Optional: Add more context..."></textarea>
  </div>
{% endfor %}
```

---

**Summary Table for AGENTS.md**

| Step                       | Description                                                                                    |
| -------------------------- | ---------------------------------------------------------------------------------------------- |
| Q\&A Round 1               | AI generates 10 yes/no questions after initial data upload; user answers with yes/no/context.  |
| Q\&A Round 2               | AI generates 10 more adaptive questions based on previous responses; user answers as above.    |
| Final Analysis Integration | AI uses all 20 Q\&A + original data to issue final risk score, rationale, and recommendations. |
| User Flow                  | Wizard-style: Upload → Q\&A1 → Q\&A2 → Report.                                                 |

---

**End of Section 5: Dynamic Interactive Q\&A Module**

**End of AGENTS.md**
