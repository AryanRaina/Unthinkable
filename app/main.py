from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import repositories, schemas
from .config import get_settings
from .database import Base, engine, get_session
from .services.matcher import JobProfile, LLMMatcher, shortlist_matches
from .services.parser import ParsedResume, load_bytes_to_text, parse_resume_text

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Smart Resume Screener", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/healthz")
def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "database": settings.database_url}


@app.post("/jobs", response_model=schemas.JobRead, status_code=201)
def create_job(payload: schemas.JobCreate, session: Session = Depends(get_session)) -> schemas.JobRead:
    job = repositories.create_job(session, payload.title, payload.description, payload.required_skills)
    return schemas.JobRead.model_validate(job)


@app.get("/jobs", response_model=List[schemas.JobRead])
def list_jobs(session: Session = Depends(get_session)) -> List[schemas.JobRead]:
    jobs = repositories.list_jobs(session)
    return [schemas.JobRead.model_validate(job) for job in jobs]


@app.patch("/jobs/{job_id}", response_model=schemas.JobRead)
def update_job(job_id: int, payload: schemas.JobUpdate, session: Session = Depends(get_session)) -> schemas.JobRead:
    job = repositories.get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    updates = payload.model_dump(exclude_unset=True)
    if updates:
        job = repositories.update_job(session, job, **updates)
    return schemas.JobRead.model_validate(job)


@app.delete("/jobs/{job_id}", status_code=204)
def delete_job(job_id: int, session: Session = Depends(get_session)) -> Response:
    job = repositories.get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    repositories.delete_job(session, job)
    return Response(status_code=204)


@app.post("/resumes", response_model=schemas.ResumeRead, status_code=201)
def create_resume(payload: schemas.ResumeCreate, session: Session = Depends(get_session)) -> schemas.ResumeRead:
    parsed = parse_resume_text(payload.raw_text)
    if payload.candidate_name:
        parsed.candidate_name = payload.candidate_name
    resume = repositories.create_resume(
        session,
        candidate_name=parsed.candidate_name,
        contact_email=parsed.contact_email,
        contact_phone=parsed.contact_phone,
        raw_text=parsed.raw_text,
        skills=parsed.skills,
        experience_years=parsed.experience_years,
        education_entries=parsed.education_entries,
        structured_data=parsed.as_dict(),
    )
    return _resume_to_schema(resume)


@app.post("/resumes/upload", response_model=schemas.ResumeRead, status_code=201)
async def upload_resume(
    file: UploadFile = File(...),
    candidate_name: Optional[str] = Form(default=None),
    session: Session = Depends(get_session),
) -> schemas.ResumeRead:
    data = await file.read()
    try:
        text = load_bytes_to_text(data, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    parsed = parse_resume_text(text)
    if candidate_name:
        parsed.candidate_name = candidate_name
    resume = repositories.create_resume(
        session,
        candidate_name=parsed.candidate_name,
        contact_email=parsed.contact_email,
        contact_phone=parsed.contact_phone,
        raw_text=parsed.raw_text,
        skills=parsed.skills,
        experience_years=parsed.experience_years,
        education_entries=parsed.education_entries,
        structured_data=parsed.as_dict(),
    )
    return _resume_to_schema(resume)


@app.get("/resumes", response_model=List[schemas.ResumeRead])
def list_resumes(session: Session = Depends(get_session)) -> List[schemas.ResumeRead]:
    resumes = repositories.list_resumes(session)
    return [_resume_to_schema(resume) for resume in resumes]


@app.get("/resumes/{resume_id}", response_model=schemas.ResumeRead)
def read_resume(resume_id: int, session: Session = Depends(get_session)) -> schemas.ResumeRead:
    resume = repositories.get_resume(session, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return _resume_to_schema(resume)


@app.post("/jobs/{job_id}/match", response_model=schemas.ShortlistResponse)
async def match_job(
    job_id: int,
    session: Session = Depends(get_session),
    shortlist_size: Optional[int] = None,
) -> schemas.ShortlistResponse:
    job = repositories.get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    matcher = LLMMatcher()
    resumes = repositories.list_resumes(session)
    shortlist_limit = shortlist_size or get_settings().max_shortlist
    scored: list[tuple[float, str, int, str | None]] = []
    for resume in resumes:
        stored = dict(resume.structured_data) if isinstance(resume.structured_data, dict) else {}
        if resume.candidate_name and not stored.get("candidate_name"):
            stored["candidate_name"] = resume.candidate_name
        parsed = ParsedResume.from_storage(resume.raw_text, stored)
        parsed.contact_email = parsed.contact_email or resume.contact_email
        parsed.contact_phone = parsed.contact_phone or resume.contact_phone
        parsed.skills = parsed.skills or resume.skills
        parsed.experience_years = parsed.experience_years or resume.experience_years
        score, reasoning, model_used = await matcher.score(
            parsed,
            JobProfile(title=job.title, description=job.description, required_skills=job.required_skills),
        )
        match = repositories.upsert_match(session, resume, job, score, reasoning, model_used)
        scored.append((match.score, match.reasoning, match.id, match.llm_model))

    matches = repositories.list_matches_for_job(session, job.id)
    shortlist = shortlist_matches(
        [(match.score, match.reasoning, match.id) for match in matches],
        shortlist_limit,
    )
    shortlist_records = [
        next(match for match in matches if match.id == match_id)
        for _, _, match_id in shortlist
    ]
    return schemas.ShortlistResponse(
        job_id=job.id,
        shortlisted=[schemas.MatchRead.model_validate(match) for match in shortlist_records],
    )


@app.get("/jobs/{job_id}/matches", response_model=List[schemas.MatchRead])
def list_matches(job_id: int, session: Session = Depends(get_session)) -> List[schemas.MatchRead]:
    job = repositories.get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    matches = repositories.list_matches_for_job(session, job_id)
    return [schemas.MatchRead.model_validate(match) for match in matches]


def _resume_to_schema(resume) -> schemas.ResumeRead:
    stored = dict(resume.structured_data) if isinstance(resume.structured_data, dict) else {}
    if resume.candidate_name and not stored.get("candidate_name"):
        stored["candidate_name"] = resume.candidate_name
    parsed = ParsedResume.from_storage(resume.raw_text, stored)
    parsed.candidate_name = parsed.candidate_name or resume.candidate_name
    parsed.contact_email = parsed.contact_email or resume.contact_email
    parsed.contact_phone = parsed.contact_phone or resume.contact_phone
    parsed.skills = parsed.skills or resume.skills
    parsed.experience_years = parsed.experience_years or resume.experience_years
    parsed.education_entries = parsed.education_entries or resume.education_entries

    return schemas.ResumeRead.model_validate(
        {
            "id": resume.id,
            "candidate_name": parsed.candidate_name,
            "contact_email": parsed.contact_email,
            "contact_phone": parsed.contact_phone,
            "skills": parsed.skills,
            "experience_years": parsed.experience_years,
            "education_entries": parsed.education_entries,
            "structured_data": parsed.as_dict(),
            "created_at": resume.created_at,
        }
    )


@app.delete("/resumes/{resume_id}", status_code=204)
def delete_resume(resume_id: int, session: Session = Depends(get_session)) -> Response:
    resume = repositories.get_resume(session, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    repositories.delete_resume(session, resume)
    return Response(status_code=204)
