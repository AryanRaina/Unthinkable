from __future__ import annotations

from typing import Iterable, List, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models


def create_job(session: Session, title: str, description: str, required_skills: Sequence[str]) -> models.JobDescription:
    job = models.JobDescription(title=title, description=description, required_skills=list(required_skills))
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def list_jobs(session: Session) -> List[models.JobDescription]:
    return list(session.scalars(select(models.JobDescription)))


def get_job(session: Session, job_id: int) -> models.JobDescription | None:
    return session.get(models.JobDescription, job_id)


def delete_job(session: Session, job: models.JobDescription) -> None:
    session.delete(job)
    session.commit()


def update_job(
    session: Session,
    job: models.JobDescription,
    *,
    title: str | None = None,
    description: str | None = None,
    required_skills: Sequence[str] | None = None,
) -> models.JobDescription:
    if title is not None:
        job.title = title
    if description is not None:
        job.description = description
    if required_skills is not None:
        job.required_skills = list(required_skills)
    session.commit()
    session.refresh(job)
    return job


def create_resume(
    session: Session,
    *,
    candidate_name: str | None,
    contact_email: str | None,
    contact_phone: str | None,
    raw_text: str,
    skills: Sequence[str],
    experience_years: float | None,
    education_entries: Sequence[dict],
    structured_data: dict,
) -> models.Resume:
    resume = models.Resume(
        candidate_name=candidate_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        raw_text=raw_text,
        skills=list(skills),
        experience_years=experience_years,
        education_entries=list(education_entries),
        structured_data=structured_data,
    )
    session.add(resume)
    session.commit()
    session.refresh(resume)
    return resume


def list_resumes(session: Session) -> List[models.Resume]:
    return list(session.scalars(select(models.Resume)))


def get_resume(session: Session, resume_id: int) -> models.Resume | None:
    return session.get(models.Resume, resume_id)


def delete_resume(session: Session, resume: models.Resume) -> None:
    session.delete(resume)
    session.commit()


def upsert_match(session: Session, resume: models.Resume, job: models.JobDescription, score: float, reasoning: str, llm_model: str | None) -> models.MatchResult:
    existing = session.scalar(
        select(models.MatchResult).where(
            models.MatchResult.resume_id == resume.id,
            models.MatchResult.job_id == job.id,
        )
    )
    if existing:
        existing.score = score
        existing.reasoning = reasoning
        existing.llm_model = llm_model
        session.commit()
        session.refresh(existing)
        return existing

    match = models.MatchResult(
        resume=resume,
        job=job,
        score=score,
        reasoning=reasoning,
        llm_model=llm_model,
    )
    session.add(match)
    session.commit()
    session.refresh(match)
    return match


def list_matches_for_job(session: Session, job_id: int) -> List[models.MatchResult]:
    return list(session.scalars(select(models.MatchResult).where(models.MatchResult.job_id == job_id)))


def list_matches_for_resume(session: Session, resume_id: int) -> List[models.MatchResult]:
    return list(session.scalars(select(models.MatchResult).where(models.MatchResult.resume_id == resume_id)))
