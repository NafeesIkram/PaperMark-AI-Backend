# PaperMark AI Backend

Standalone FastAPI backend for PaperMark AI.

Current scope: manual questions, manual/model answers, manual student answers, semantic evaluation, exact evaluation, rubric/point-based evaluation, required concepts, formula verification, custom rules, and multiple students.

PDF/OCR, database, authentication, file storage, and production deployment are intentionally left for later.

## Setup

Open Command Prompt in this folder:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your Gemini API key.

Run:

```bash
uvicorn main:app --reload
```

API: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs

Endpoint:
POST /api/evaluate

If `customApiKey` is supplied in a request, it is used for that request only. Otherwise `GEMINI_API_KEY` from `.env` is used. This backend does not persist custom keys.

Frontend and backend are separate projects.
