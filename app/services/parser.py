from __future__ import annotations

import io
import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from pdfminer.high_level import extract_text

_SKILL_KEYWORDS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "c++",
    "c#",
    "go",
    "sql",
    "nosql",
    "mysql",
    "postgresql",
    "mongodb",
    "redis",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "terraform",
    "linux",
    "git",
    "html",
    "css",
    "react",
    "angular",
    "node",
    "fastapi",
    "django",
    "flask",
    "pandas",
    "numpy",
    "spark",
    "hadoop",
    "machine learning",
    "deep learning",
    "nlp",
    "data analysis",
    "data engineering",
    "scala",
    "rust",
    "php",
    "ruby",
}

_SECTION_HEADERS = {
    "experience": {"experience", "work experience", "employment", "professional experience"},
    "education": {"education", "academic", "academics", "qualifications"},
    "skills": {"skills", "technical skills", "core competencies"},
    "projects": {"projects", "notable projects"},
}

_EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_PATTERN = re.compile(r"\+?\d[\d\s().-]{7,}\d")
_YEAR_PATTERN = re.compile(r"(\d{4})")
_EXPERIENCE_YEARS_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:\+\s*)?(?:years?|yrs?)", re.IGNORECASE)


@dataclass
class ParsedResume:
    raw_text: str
    candidate_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    skills: List[str] = field(default_factory=list)
    experience_years: float | None = None
    education_entries: List[Dict[str, str]] = field(default_factory=list)
    sections: Dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, object]:
        return {
            "candidate_name": self.candidate_name,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "skills": self.skills,
            "experience_years": self.experience_years,
            "education_entries": self.education_entries,
            "sections": self.sections,
        }

    @classmethod
    def from_storage(cls, raw_text: str, data: Dict[str, object]) -> "ParsedResume":
        sections_obj = data.get("sections")
        sections = sections_obj if isinstance(sections_obj, dict) else {}
        experience = data.get("experience_years")
        experience_years = None
        if isinstance(experience, (int, float)):
            experience_years = float(experience)
        elif isinstance(experience, str):
            try:
                experience_years = float(experience)
            except ValueError:
                experience_years = None
        return cls(
            raw_text=raw_text,
            candidate_name=data.get("candidate_name") if isinstance(data.get("candidate_name"), str) else None,
            contact_email=data.get("contact_email") if isinstance(data.get("contact_email"), str) else None,
            contact_phone=data.get("contact_phone") if isinstance(data.get("contact_phone"), str) else None,
            skills=list(data.get("skills", [])) if isinstance(data.get("skills"), list) else [],
            experience_years=experience_years,
            education_entries=list(data.get("education_entries", [])) if isinstance(data.get("education_entries"), list) else [],
            sections=sections,  # type: ignore[arg-type]
        )


def load_bytes_to_text(data: bytes, filename: str) -> str:
    """Convert uploaded file bytes into plain text."""

    lowered = filename.lower()
    if lowered.endswith(".pdf"):
        with io.BytesIO(data) as buffer:
            return extract_text(buffer)
    if lowered.endswith((".txt", ".md")):
        return data.decode("utf-8", errors="ignore")
    raise ValueError("Unsupported resume format. Provide PDF or text file.")


def parse_resume_text(text: str) -> ParsedResume:
    """Extract structured data from unstructured resume text."""

    normalized = text.replace("\r", "")
    sections, order = _split_into_sections(normalized)

    email = _find_first(_EMAIL_PATTERN, normalized)
    phone = _find_first(_PHONE_PATTERN, normalized)
    candidate_name = _infer_name(normalized)
    skills = sorted(_match_skills(normalized))
    experience_years = _estimate_experience_years(normalized)
    education_entries = _extract_education(sections.get("education", ""))

    parsed = ParsedResume(
        raw_text=normalized,
        candidate_name=candidate_name,
        contact_email=email,
        contact_phone=phone,
        skills=skills,
        experience_years=experience_years,
        education_entries=education_entries,
        sections=sections,
    )

    if "skills" not in sections and skills:
        parsed.sections["skills"] = ", ".join(skills)
    if "experience" not in sections and experience_years is not None:
        parsed.sections["experience"] = f"Estimated {experience_years:g} years of experience"

    parsed.sections["section_order"] = order

    return parsed


def _split_into_sections(text: str) -> Tuple[Dict[str, str], List[str]]:
    sections: Dict[str, List[str]] = {}
    current = "summary"
    order: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        normalized = stripped.lower()
        matched_section = None
        for section_key, keywords in _SECTION_HEADERS.items():
            if normalized in keywords or normalized.rstrip(":") in keywords:
                matched_section = section_key
                break
        if matched_section:
            current = matched_section
            if current not in sections:
                sections[current] = []
                order.append(current)
            continue
        sections.setdefault(current, []).append(stripped)
        if current not in order:
            order.append(current)
    joined_sections = {key: "\n".join(values) for key, values in sections.items()}
    return joined_sections, order


def _find_first(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(0) if match else None


def _infer_name(text: str) -> str | None:
    # Use the first non-empty line as a proxy if it looks like a name.
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if _EMAIL_PATTERN.match(stripped.lower()):
            continue
        if any(keyword in stripped.lower() for keyword in ("resume", "curriculum vitae")):
            continue
        if len(stripped.split()) <= 5:
            return stripped
    return None


def _match_skills(text: str) -> List[str]:
    lowered = text.lower()
    found = {skill for skill in _SKILL_KEYWORDS if skill in lowered}
    return sorted(found)


def _estimate_experience_years(text: str) -> float | None:
    matches = _EXPERIENCE_YEARS_PATTERN.findall(text)
    if not matches:
        return None
    numbers = [float(match) for match in matches]
    return max(numbers)


def _extract_education(education_section: str) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    if not education_section:
        return results
    for block in education_section.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        entry: Dict[str, str] = {"summary": block}
        years = _YEAR_PATTERN.findall(block)
        if years:
            entry["years"] = "-".join(sorted(set(years)))
        results.append(entry)
    return results


def parsed_resume_to_json(parsed: ParsedResume) -> str:
    """Serialize parsed resume to JSON for storage."""

    return json.dumps(parsed.as_dict(), ensure_ascii=False)
