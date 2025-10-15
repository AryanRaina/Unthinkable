# Smart Resume Screener

Smart Resume Screener ingests resumes, structures the data, and ranks candidates against job descriptions using either an OpenAI model or a deterministic heuristic. It ships as a FastAPI backend with a Vite + React dashboard for recruiters.

# Demo Video

<p align="center">
  <a href="https://youtu.be/DbvOis2-RuA" target="_blank">
    <img src="https://img.youtube.com/vi/4SvEMh8TU8E/0.jpg" alt="Watch the video" />
  </a>
</p>

## System Architecture

```
┌───────────┐     HTTP      ┌────────────┐    SQLAlchemy     ┌──────────────┐
│ React UI  │ ───────────▶ │ FastAPI API│ ────────────────▶ │ SQLite (DB)  │
└────┬──────┘               │  /app      │                   └────┬─────────┘
             │                      └────┬───────┘                        │
             │  Fetch/Axios               │Repositories                    │
             │                            ▼                                │
             │                    ┌──────────────────┐                     │
             └───────────────────▶│ Services Layer   │◀─────┐              │
                                                                              │ parser / matcher │      │ LLM fallback │
                                                                              └──────────────────┘      ▼              │
                                                                                                                                                      OpenAI API       │
                                                                                                                                                 (heuristic alt.)  │
```

- **Frontend (`frontend/`)**: React + TypeScript SPA built with Vite. Provides job management, resume intake (file and text), shortlist visualization, and destructive actions (delete job/resume).
- **API layer (`app/main.py`)**: FastAPI routes expose CRUD for jobs and resumes, matching endpoints, and health checks. DELETE routes rely on SQLAlchemy cascades to clean up associated match results.
- **Repository layer (`app/repositories.py`)**: Encapsulates database operations, keeps transactions scoped, and centralizes eager loading.
- **Services**:
      - `parser.py` parses PDF or raw text into the `ParsedResume` dataclass (skills, experience, education, contacts).
      - `matcher.py` orchestrates LLM scoring or falls back to `heuristic_match` when the OpenAI client is unavailable.
- **Database (`app/models.py`)**: SQLite schema with `JobDescription`, `Resume`, and `MatchResult` tables. Foreign keys have ON DELETE cascades to remove orphaned matches automatically.
- **Tests (`tests/`)**: Cover parser accuracy, heuristic scoring, repository behavior, and end-to-end API flows via TestClient.

### Match Pipeline Walkthrough

1. User runs “Refresh shortlist” from the UI → `POST /jobs/{job_id}/match`.
2. API loads job + all resumes through repositories.
3. For each resume the matcher:
       - Prepares `JobProfile` + `ParsedResume` payloads.
       - Calls OpenAI Responses API with the match prompt (if configured) on a background thread.
       - Falls back to `heuristic_match` when OpenAI is unavailable or throws.
4. Scores below 7.0 are filtered, results sorted, truncated to the configured shortlist size.
5. Matches persist to the database and return to the client. The UI caches shortlists per job for instant switching.

## Prompt Library

### Primary Match Prompt

```
You are an expert technical recruiter. Compare the following resume with the job description.
Respond in JSON with the following fields: score (0-10 float) and reasoning (2-3 bullet summary).
Resume JSON:
{resume_json}
Job Description:
{job_description}
Job Title: {job_title}
Required Skills: {required_skills}
```

- **Persona**: Technical recruiter focused on transparent scoring.
- **Output contract**: Strict JSON with `score` and `reasoning`. A JSON parser with regex fallback (`_parse_json_response`) safeguards against minor LLM formatting drift.
- **Temperature**: 0.2 to reduce hallucinations and keep scores deterministic.
- **Post-processing**: `reasoning` arrays are joined into newline-delimited bullet text before storage.

### Guardrails and Fallbacks

- Missing `OPENAI_API_KEY` or runtime failures trigger the deterministic heuristic (`heuristic_match`).
- Heuristic scoring weights: 70% required-skill overlap, 30% experience alignment (regex extraction of “X years of experience”).
- The shortlist uses a configurable size (`SHORTLIST_SIZE`, default 5) and enforces a minimum score threshold of 7.0.

## REST API Surface

| Method & Path             | Description                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| `GET /healthz`            | Health check with database connectivity info.                               |
| `POST /jobs`              | Create a job description (title, description, required skills).             |
| `GET /jobs`               | List jobs sorted by creation date.                                          |
| `PATCH /jobs/{id}`        | Update title/description/skills for a job.                                   |
| `DELETE /jobs/{id}`       | Remove a job, cascade deleting shortlist history and UI state caches.       |
| `POST /resumes`           | Submit raw text resumes.                                                     |
| `POST /resumes/upload`    | Upload files (PDF/TXT) for parsing.                                          |
| `GET /resumes`            | List parsed resumes.                                                         |
| `GET /resumes/{id}`       | Fetch a single resume with structured fields.                               |
| `DELETE /resumes/{id}`    | Delete a resume and remove it from all stored shortlists.                    |
| `POST /jobs/{id}/match`   | Run scoring pipeline; persists shortlist entries.                            |
| `GET /jobs/{id}/matches`  | Retrieve previously saved shortlist entries.                                 |

## Environment & Configuration

Required configuration lives in `.env` (FastAPI) and `frontend/.env` (React). Key variables:

```
DATABASE_URL=sqlite:///./smart_resume.db
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
SHORTLIST_SIZE=5
LOG_LEVEL=INFO
FRONTEND_API_BASE=http://127.0.0.1:8000
```

- Omit `OPENAI_API_KEY` to run the heuristic-only mode.
- Adjust `SHORTLIST_SIZE` to change the number of candidates returned per match request.

## Local Development

### Backend setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Interactive docs: `http://127.0.0.1:8000/docs`.

### Frontend setup

```powershell
cd frontend
npm install
npm run dev
```

Visit the printed Vite URL (default `http://127.0.0.1:5173`). Configure API origin through `frontend/.env`.

### Testing

```powershell
pytest
```

## Operational Notes

- **Data lifecycle**: Deleting a job via the UI or API cascades to `MatchResult` rows. Removing a resume clears it from all cached shortlists.
- **Caching**: The frontend memoizes match results by job to avoid unnecessary re-requests until a new shortlist is run.
- **Logging**: FastAPI logs requests; matcher logs whether LLM or heuristic was used for traceability.

## Roadmap Ideas

- Integrate authentication and role-based access for multi-recruiter teams.
- Introduce embeddings or vector stores to pre-filter resumes before LLM scoring.
- Add asynchronous job queues (Celery/RQ) for large resume batches.
- Export shortlists to CSV or ATS integrations.

## Demo Checklist

1. Start FastAPI (`uvicorn app.main:app --reload`) and hit `/healthz` in the browser.
2. Create a job via the dashboard and inspect the persisted entry in the sidebar.
3. Upload a resume (file or text) and review parsed fields in the Resume Intake confirmation.
4. Run the shortlist, highlight the LLM reasoning (or heuristic fallback), and optionally delete a resume to prove cascade removal.
