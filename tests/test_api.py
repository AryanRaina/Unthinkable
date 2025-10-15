from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_resume_match_flow():
    job_payload = {
        "title": "Data Engineer",
        "description": "We need 3 years of experience with Python, SQL, and AWS.",
        "required_skills": ["python", "sql", "aws"],
    }
    job_resp = client.post("/jobs", json=job_payload)
    assert job_resp.status_code == 201
    job_id = job_resp.json()["id"]

    resume_text = """
    John Smith
    Email: john.smith@example.com
    Skills
    Python, SQL, AWS, Docker
    Experience
    4 years of experience building ETL pipelines on AWS.
    """.strip()

    resume_payload = {
        "candidate_name": "John Smith",
        "raw_text": resume_text,
    }
    resume_resp = client.post("/resumes", json=resume_payload)
    assert resume_resp.status_code == 201
    resume_id = resume_resp.json()["id"]

    match_resp = client.post(f"/jobs/{job_id}/match")
    assert match_resp.status_code == 200
    data = match_resp.json()

    assert data["job_id"] == job_id
    shortlisted = data["shortlisted"]
    assert shortlisted
    top = shortlisted[0]
    assert top["resume_id"] == resume_id
    assert top["resume"]["candidate_name"] == "John Smith"
    assert 0 <= top["score"] <= 10


def test_update_job_details():
    job_payload = {
        "title": "Backend Engineer",
        "description": "Build APIs and services.",
        "required_skills": ["python", "fastapi"],
    }
    job_resp = client.post("/jobs", json=job_payload)
    assert job_resp.status_code == 201
    job_id = job_resp.json()["id"]

    update_payload = {
        "title": "Senior Backend Engineer",
        "description": "Design and build APIs, mentor engineers, own service reliability.",
        "required_skills": ["python", "fastapi", "aws"],
    }
    update_resp = client.patch(f"/jobs/{job_id}", json=update_payload)
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["title"] == update_payload["title"]
    assert data["description"] == update_payload["description"]
    assert data["required_skills"] == update_payload["required_skills"]


def test_shortlist_filters_low_scores(monkeypatch):
    from app import repositories
    from app.services import matcher

    job_payload = {
        "title": "QA Analyst",
        "description": "Manual and automated testing experience required.",
        "required_skills": ["testing", "automation"],
    }
    job_resp = client.post("/jobs", json=job_payload)
    assert job_resp.status_code == 201
    job_id = job_resp.json()["id"]

    resume_payload = {
        "candidate_name": "Low Score Candidate",
        "raw_text": "Testing background with basic exposure.",
    }
    resume_resp = client.post("/resumes", json=resume_payload)
    assert resume_resp.status_code == 201

    def fake_score(_resume, _job):
        return 5.5, "Below threshold", "mock"

    monkeypatch.setattr(matcher.LLMMatcher, "score", lambda self, resume, job: fake_score(resume, job))
    match_resp = client.post(f"/jobs/{job_id}/match")
    assert match_resp.status_code == 200
    data = match_resp.json()
    assert data["shortlisted"] == []
