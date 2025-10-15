from app.services.matcher import JobProfile, heuristic_match
from app.services.parser import ParsedResume


def test_heuristic_match_scores_overlap():
    resume = ParsedResume(
        raw_text="",
        candidate_name="Jane Doe",
        skills=["python", "fastapi", "aws"],
        experience_years=5,
    )
    job = JobProfile(
        title="Backend Engineer",
        description="Looking for 4 years of experience building cloud APIs.",
        required_skills=["python", "fastapi", "docker"],
    )

    score, reasoning = heuristic_match(resume, job)

    assert score > 0
    assert "Skill match" in reasoning
    assert "Candidate" in reasoning
