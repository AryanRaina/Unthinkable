from app.services import parser


def test_parse_resume_text_extracts_skills_and_contact():
    sample = """
    Jane Doe
    Email: jane.doe@example.com
    Phone: +1 555 0100

    Skills
    Python, FastAPI, AWS, Docker

    Experience
    Senior Engineer at ExampleCorp (2018-2024)
    Worked on deploying FastAPI microservices on AWS with Docker and Kubernetes.
    Over 6 years of experience leading cloud-native teams.

    Education
    B.S. Computer Science, Example University, 2017
    """.strip()

    parsed = parser.parse_resume_text(sample)

    assert parsed.candidate_name == "Jane Doe"
    assert "python" in parsed.skills
    assert "fastapi" in parsed.skills
    assert parsed.contact_email == "jane.doe@example.com"
    assert parsed.contact_phone.endswith("0100")
    assert parsed.experience_years == 6
    assert parsed.education_entries
