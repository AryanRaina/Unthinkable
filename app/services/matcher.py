from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple, Dict
import json

from ..config import get_settings
from .parser import ParsedResume

try:  # pragma: no cover - optional dependency at runtime
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

_LOGGER = logging.getLogger(__name__)

_MATCH_PROMPT = """
You are an expert technical recruiter. Compare the following resume with the job description.
Respond in JSON with the following fields: score (0-10 float) and reasoning (2-3 bullet summary).
Resume JSON:
{resume_json}
Job Description:
{job_description}
Job Title: {job_title}
Required Skills: {required_skills}
""".strip()


@dataclass
class JobProfile:
    title: str
    description: str
    required_skills: Sequence[str]


class LLMMatcher:
    """Wrapper that delegates to OpenAI when available, else uses heuristics."""

    def __init__(self) -> None:
        settings = get_settings()
        api_key = settings.openai_api_key
        self.model = settings.llm_model
        self._client = OpenAI(api_key=api_key) if api_key and OpenAI else None
        if not api_key:
            _LOGGER.info("OPENAI_API_KEY not set; defaulting to heuristic matcher.")
        elif not OpenAI:
            _LOGGER.warning("openai package not available; install requirements to enable LLM scoring.")
        elif self._client is None:
            _LOGGER.warning("Failed to initialise OpenAI client; check credentials and dependencies.")

    async def score(self, resume: ParsedResume, job: JobProfile) -> Tuple[float, str, str | None]:
        """Return (score, reasoning, model_used)."""

        if self._client:
            try:
                payload = _MATCH_PROMPT.format(
                    resume_json=json.dumps(resume.as_dict(), ensure_ascii=False),
                    job_description=job.description,
                    job_title=job.title,
                    required_skills=json.dumps(list(job.required_skills), ensure_ascii=False),
                )
                response = await asyncio.to_thread(self._call_openai, payload)
                if response:
                    score, reasoning, model_used = response
                    _LOGGER.info("LLM %s scored resume at %.2f", model_used, score)
                    return score, reasoning, model_used
            except Exception as exc:  # pragma: no cover - network failure path
                _LOGGER.warning("Falling back to heuristic matcher: %s", exc)

        score, reasoning = heuristic_match(resume, job)
        _LOGGER.info("Using heuristic matcher for %s", resume.candidate_name or "unknown candidate")
        return score, reasoning, None

    def _call_openai(self, prompt: str) -> Tuple[float, str, str]:  # pragma: no cover - exercised only with API key
        assert self._client is not None
        result = self._client.responses.create(
            model=self.model,
            input=prompt,
            temperature=0.2,
        )
        text_chunks: List[str] = []
        for item in getattr(result, "output", []):  # type: ignore[attr-defined]
            for chunk in getattr(item, "content", []):
                chunk_text = getattr(chunk, "text", None)
                if chunk_text:
                    text_chunks.append(chunk_text)
                elif isinstance(chunk, dict) and "text" in chunk:
                    text_chunks.append(str(chunk["text"]))
        content = "".join(text_chunks).strip()
        parsed = _parse_json_response(content)
        score = float(parsed.get("score", 0))
        reasoning_field = parsed.get("reasoning")
        if isinstance(reasoning_field, list):
            reasoning = "\n".join(str(line).strip() for line in reasoning_field if str(line).strip())
        else:
            reasoning = str(reasoning_field or "No reasoning provided.")
        return score, reasoning, self.model


def _parse_json_response(text: str) -> Dict[str, object]:
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    _LOGGER.warning("Could not parse LLM response as JSON: %s", text)
    return {}


def heuristic_match(resume: ParsedResume, job: JobProfile) -> Tuple[float, str]:
    """Deterministic fallback that scores using skills and experience overlap."""

    skill_score = _skill_overlap(resume.skills, job.required_skills)
    resume_experience = resume.experience_years or 0.0
    required_experience = _estimate_required_experience(job.description)
    experience_score = _experience_alignment(resume_experience, required_experience)
    overall = round((0.7 * skill_score + 0.3 * experience_score) * 10, 2)

    reasoning_lines = [
        f"Skill match: {skill_score * 100:.0f}% overlap",
        f"Experience: {resume_experience:.1f} years vs requirement {required_experience:.1f} years",
    ]
    if resume.candidate_name:
        reasoning_lines.insert(0, f"Candidate: {resume.candidate_name}")

    return overall, "\n".join(reasoning_lines)


def _skill_overlap(resume_skills: Iterable[str], required: Iterable[str]) -> float:
    resume_set = {skill.lower() for skill in resume_skills}
    required_set = {skill.lower() for skill in required}
    if not required_set:
        return 1.0 if resume_set else 0.0
    overlap = resume_set.intersection(required_set)
    return len(overlap) / len(required_set)


def _estimate_required_experience(text: str) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:\+\s*)?(?:years?|yrs?) of experience", text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return 3.0


def _experience_alignment(resume_years: float, required_years: float) -> float:
    if required_years <= 0:
        return 1.0
    ratio = resume_years / required_years if required_years else 1.0
    return max(0.0, min(ratio, 1.0))


def shortlist_matches(matches: Sequence[Tuple[float, str, int]], limit: int) -> List[Tuple[float, str, int]]:
    """Sort matches by score descending, filter by minimum threshold, and truncate."""

    filtered = [item for item in matches if item[0] >= 7.0]
    return sorted(filtered, key=lambda item: item[0], reverse=True)[:limit]
