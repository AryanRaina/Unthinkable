from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ResumeBase(BaseModel):
    candidate_name: Optional[str] = Field(default=None, description="Full name parsed or supplied.")
    contact_email: Optional[str] = Field(default=None)
    contact_phone: Optional[str] = Field(default=None)
    skills: List[str] = Field(default_factory=list)
    experience_years: Optional[float] = None
    education_entries: List[Dict[str, Any]] = Field(default_factory=list)
    structured_data: Dict[str, Any] = Field(default_factory=dict)


class ResumeCreate(ResumeBase):
    raw_text: str = Field(..., description="Full resume as plain text.")


class ResumeRead(ResumeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class JobCreate(BaseModel):
    title: str
    description: str
    required_skills: List[str] = Field(default_factory=list)


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None


class JobRead(JobCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class MatchCreate(BaseModel):
    resume_id: int
    job_id: int


class MatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resume_id: int
    job_id: int
    score: float
    reasoning: str
    llm_model: Optional[str] = None
    created_at: datetime
    resume: Optional[ResumeRead] = None


class MatchResponse(BaseModel):
    job: JobRead
    matches: List[MatchRead]


class ShortlistResponse(BaseModel):
    job_id: int
    shortlisted: List[MatchRead]
