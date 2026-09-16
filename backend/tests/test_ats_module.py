import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.models.auth import User
from app.models.resume import Resume
from app.models.ats import ATSReport
from app.services.ats import ATSService
from app.core.dependencies import get_current_active_user, get_ats_service, get_resume_service


# ==============================================================================
# 1. Unit Tests for ATSService Heuristics & Algorithms
# ==============================================================================

def test_clean_text_to_words():
    svc = ATSService(ats_repo=None, resume_repo=None)
    text = "The quick brown fox jumped over the lazy dog and designed a microservice."
    words = svc.clean_text_to_words(text)
    # Stop words like "the", "and", "a", "over" should be filtered out
    assert "quick" in words
    assert "brown" in words
    assert "designed" in words
    assert "microservice" in words
    assert "the" not in words
    assert "and" not in words


def test_extract_keywords():
    svc = ATSService(ats_repo=None, resume_repo=None)
    text = "FastAPI is awesome. FastAPI uses Docker. Docker is lightweight."
    keywords = svc.extract_keywords(text)
    assert "fastapi" in keywords
    assert "docker" in keywords
    assert "awesome" in keywords


def test_count_syllables_in_word():
    svc = ATSService(ats_repo=None, resume_repo=None)
    assert svc.count_syllables_in_word("the") == 1
    assert svc.count_syllables_in_word("fastapi") == 3  # f-a-s-t-a-p-i (heuristic will approximate)
    assert svc.count_syllables_in_word("implemented") == 4
    assert svc.count_syllables_in_word("code") == 1  # silent final e
    assert svc.count_syllables_in_word("") == 0


def test_analyze_readability():
    svc = ATSService(ats_repo=None, resume_repo=None)
    text = "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.8+ based on standard Python type hints."
    res = svc.analyze_readability(text)
    assert res.flesch_reading_ease > 0
    assert res.grade_level in ["5th Grade", "6th Grade", "7th Grade", "8th-9th Grade", "10th-12th Grade", "College Level", "Graduate Level"]
    assert res.readability_rating in ["EASY", "STANDARD", "DIFFICULT", "VERY_DIFFICULT"]


def test_analyze_grammar():
    svc = ATSService(ats_repo=None, resume_repo=None)
    text = "i designed the system. It was responsible for the database.  Double spacing present."
    res = svc.analyze_grammar(text)
    assert res.errors_detected > 0
    # Lowercase 'i', passive 'was responsible for', and double spaces should be flagged
    assert any("lowercase 'i'" in iss.lower() for iss in res.issues)
    assert any("double-spacing" in iss.lower() for iss in res.issues)
    assert any("passive/weak" in iss.lower() for iss in res.issues)


def test_analyze_action_verbs():
    svc = ATSService(ats_repo=None, resume_repo=None)
    text = "Spearheaded the design, optimized PostgreSQL queries, and implemented the CI/CD pipeline."
    res = svc.analyze_action_verbs(text)
    assert res.action_verbs_count >= 3
    assert "spearheaded" in res.verbs_used
    assert "optimized" in res.verbs_used
    assert "implemented" in res.verbs_used


def test_analyze_formatting():
    svc = ATSService(ats_repo=None, resume_repo=None)
    mock_resume = Resume(
        template_code="creative_fancy",
        content={
            "personal_info": {
                "photo_url": "http://img.com/avatar.png"
            }
        }
    )
    res = svc.analyze_formatting(mock_resume)
    assert res.has_charts_or_images is True
    assert res.has_unsupported_fonts is True
    assert len(res.issues) == 2


def test_analyze_section_completeness():
    svc = ATSService(ats_repo=None, resume_repo=None)
    mock_resume = Resume(
        content={
            "personal_info": {"name": "Alice"},
            "experience": [{"role": "Eng"}],
            "education": [{"degree": "BSc"}],
            "skills": ["Python"]
        }
    )
    res = svc.analyze_section_completeness(mock_resume)
    assert res.completeness_percentage == 100.0
    assert "Personal Info" in res.present_sections
    assert len(res.missing_essential_sections) == 0


def test_analyze_resume_against_jd():
    svc = ATSService(ats_repo=None, resume_repo=None)
    mock_resume = Resume(
        template_code="standard_scannable",
        content={
            "personal_info": {
                "name": "Alice",
                "summary": "Spearheaded FastAPI software architecture."
            },
            "experience": [
                {
                    "role": "Engineer",
                    "highlights": ["Designed microservices with Docker and Kubernetes."]
                }
            ],
            "skills": ["FastAPI", "Docker", "Python", "Kubernetes"]
        }
    )
    jd = "We are seeking an Engineer who knows FastAPI, Docker, and Kubernetes. Led architecture optimization."
    report = svc.analyze_resume_against_jd(mock_resume, jd)
    assert report.ats_score > 30
    assert len(report.keyword_matching.matched_keywords) > 0
    assert report.benchmark.rating in ["BELOW_AVERAGE", "AVERAGE", "ABOVE_AVERAGE", "OUTSTANDING"]


# ==============================================================================
# 2. Integration / API Endpoint Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_endpoint_ats_analyze(client):
    user_id = uuid.uuid4()
    resume_id = uuid.uuid4()
    mock_user = User(id=user_id, email="bob@test.com", username="bob", password_hash="xyz", status="ACTIVE")
    
    # Mock resume
    mock_resume = Resume(
        id=resume_id,
        user_id=user_id,
        title="Software Engineer CV",
        content={
            "personal_info": {"name": "Bob", "summary": "Full stack developer."},
            "experience": [{"role": "React Dev", "highlights": ["Created web applications."]}],
            "education": [{"degree": "BSc in CS"}],
            "skills": ["React", "JavaScript"]
        }
    )

    # Mock ATS report record in DB
    mock_db_report = ATSReport(
        id=uuid.uuid4(),
        user_id=user_id,
        resume_id=resume_id,
        job_title="Frontend Engineer",
        job_description="Looking for a React developer with JS skills",
        ats_score=85,
        created_at=datetime.utcnow(),
        report_data={
            "ats_score": 85,
            "keyword_matching": {
                "matched_keywords": ["react", "javascript"],
                "missing_keywords": [],
                "keyword_match_percentage": 100.0
            },
            "formatting_analysis": {
                "has_unsupported_fonts": False,
                "has_poor_margins": False,
                "has_complex_tables": False,
                "has_charts_or_images": False,
                "issues": []
            },
            "readability_analysis": {
                "flesch_reading_ease": 75.0,
                "grade_level": "7th Grade",
                "readability_rating": "EASY"
            },
            "grammar_analysis": {
                "errors_detected": 0,
                "issues": [],
                "suggestions": []
            },
            "action_verb_analysis": {
                "action_verbs_count": 5,
                "verbs_used": ["created"],
                "suggestions": []
            },
            "section_completeness": {
                "present_sections": ["Personal Info", "Experience", "Education", "Skills"],
                "missing_essential_sections": [],
                "completeness_percentage": 100.0
            },
            "ai_suggestions": ["Keep up the great work!"],
            "benchmark": {
                "industry_average_score": 66.5,
                "user_percentile": 82.5,
                "rating": "ABOVE_AVERAGE"
            }
        }
    )

    mock_resume_svc = MagicMock()
    mock_resume_svc.get_by_id = AsyncMock(return_value=mock_resume)

    mock_ats_svc = MagicMock()
    mock_ats_svc.create_ats_report = AsyncMock(return_value=mock_db_report)

    # Override dependencies
    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_resume_service] = lambda: mock_resume_svc
    client.app.dependency_overrides[get_ats_service] = lambda: mock_ats_svc

    payload = {
        "resume_id": str(resume_id),
        "job_description": "Looking for a React developer with JS skills",
        "job_title": "Frontend Engineer"
    }

    response = client.post("/api/v1/ats/analyze", json=payload)
    client.app.dependency_overrides.clear()

    if response.status_code != 201:
        print("ANALYZE FAIL RESPONSE:", response.status_code, response.text)

    assert response.status_code == 201
    res_data = response.json()
    assert res_data["ats_score"] == 85
    assert "report_data" in res_data
    assert res_data["report_data"]["keyword_matching"]["matched_keywords"] == ["react", "javascript"]


@pytest.mark.asyncio
async def test_endpoint_ats_compare(client):
    user_id = uuid.uuid4()
    resume_a_id = uuid.uuid4()
    resume_b_id = uuid.uuid4()
    mock_user = User(id=user_id, email="bob@test.com", username="bob", password_hash="xyz", status="ACTIVE")

    mock_resume_a = Resume(id=resume_a_id, user_id=user_id, title="CV A", content={})
    mock_resume_b = Resume(id=resume_b_id, user_id=user_id, title="CV B", content={})

    mock_resume_svc = MagicMock()
    # Simple side effect mock for get_by_id
    async def get_by_id_mock(rid):
        if rid == resume_a_id:
            return mock_resume_a
        if rid == resume_b_id:
            return mock_resume_b
        return None
    mock_resume_svc.get_by_id.side_effect = get_by_id_mock

    # Mock compare response
    mock_comp_response = {
        "resume_a_id": str(resume_a_id),
        "resume_b_id": str(resume_b_id),
        "common_skills": ["python"],
        "unique_skills_a": ["fastapi"],
        "unique_skills_b": ["django"],
        "ats_score_a": 80,
        "ats_score_b": 70,
        "score_comparison": {
            "overall": {
                "score_a": 80.0,
                "score_b": 70.0,
                "comparison_notes": "Resume A is better."
            }
        },
        "comparison_summary": "Resume A wins."
    }

    mock_ats_svc = MagicMock()
    mock_ats_svc.compare_two_resumes = AsyncMock(return_value=mock_comp_response)

    # Dependency overrides
    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_resume_service] = lambda: mock_resume_svc
    client.app.dependency_overrides[get_ats_service] = lambda: mock_ats_svc

    payload = {
        "resume_a_id": str(resume_a_id),
        "resume_b_id": str(resume_b_id),
        "job_description": "Python Developer FastAPI Django"
    }

    response = client.post("/api/v1/ats/compare", json=payload)
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["ats_score_a"] == 80
    assert res_data["ats_score_b"] == 70
    assert "common_skills" in res_data


@pytest.mark.asyncio
async def test_endpoint_ats_get_report(client):
    user_id = uuid.uuid4()
    report_id = uuid.uuid4()
    resume_id = uuid.uuid4()
    mock_user = User(id=user_id, email="bob@test.com", username="bob", password_hash="xyz", status="ACTIVE")

    mock_db_report = ATSReport(
        id=report_id,
        user_id=user_id,
        resume_id=resume_id,
        job_title="Frontend Engineer",
        job_description="Looking for a React developer with JS skills",
        ats_score=85,
        created_at=datetime.utcnow(),
        report_data={
            "ats_score": 85,
            "keyword_matching": {
                "matched_keywords": ["react"],
                "missing_keywords": [],
                "keyword_match_percentage": 100.0
            },
            "formatting_analysis": {
                "has_unsupported_fonts": False,
                "has_poor_margins": False,
                "has_complex_tables": False,
                "has_charts_or_images": False,
                "issues": []
            },
            "readability_analysis": {
                "flesch_reading_ease": 75.0,
                "grade_level": "7th Grade",
                "readability_rating": "EASY"
            },
            "grammar_analysis": {
                "errors_detected": 0,
                "issues": [],
                "suggestions": []
            },
            "action_verb_analysis": {
                "action_verbs_count": 5,
                "verbs_used": ["created"],
                "suggestions": []
            },
            "section_completeness": {
                "present_sections": ["Personal Info", "Experience"],
                "missing_essential_sections": [],
                "completeness_percentage": 100.0
            },
            "ai_suggestions": [],
            "benchmark": {
                "industry_average_score": 66.5,
                "user_percentile": 82.5,
                "rating": "ABOVE_AVERAGE"
            }
        }
    )

    mock_ats_svc = MagicMock()
    mock_ats_svc.get_report = AsyncMock(return_value=mock_db_report)

    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_ats_service] = lambda: mock_ats_svc

    response = client.get(f"/api/v1/ats/reports/{report_id}")
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["id"] == str(report_id)
    assert res_data["ats_score"] == 85


@pytest.mark.asyncio
async def test_endpoint_export_pdf(client):
    user_id = uuid.uuid4()
    report_id = uuid.uuid4()
    resume_id = uuid.uuid4()
    mock_user = User(id=user_id, email="bob@test.com", username="bob", password_hash="xyz", status="ACTIVE")

    mock_db_report = ATSReport(
        id=report_id,
        user_id=user_id,
        resume_id=resume_id,
        job_title="Frontend Engineer",
        job_description="Looking for a React developer with JS skills",
        ats_score=85,
        created_at=datetime.utcnow(),
        report_data={
            "ats_score": 85,
            "keyword_matching": {
                "matched_keywords": ["react"],
                "missing_keywords": [],
                "keyword_match_percentage": 100.0
            },
            "formatting_analysis": {
                "has_unsupported_fonts": False,
                "has_poor_margins": False,
                "has_complex_tables": False,
                "has_charts_or_images": False,
                "issues": []
            },
            "readability_analysis": {
                "flesch_reading_ease": 75.0,
                "grade_level": "7th Grade",
                "readability_rating": "EASY"
            },
            "grammar_analysis": {
                "errors_detected": 0,
                "issues": [],
                "suggestions": []
            },
            "action_verb_analysis": {
                "action_verbs_count": 5,
                "verbs_used": ["created"],
                "suggestions": []
            },
            "section_completeness": {
                "present_sections": ["Personal Info", "Experience"],
                "missing_essential_sections": [],
                "completeness_percentage": 100.0
            },
            "ai_suggestions": [],
            "benchmark": {
                "industry_average_score": 66.5,
                "user_percentile": 82.5,
                "rating": "ABOVE_AVERAGE"
            }
        }
    )

    mock_ats_svc = MagicMock()
    mock_ats_svc.get_report = AsyncMock(return_value=mock_db_report)

    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_ats_service] = lambda: mock_ats_svc

    response = client.get(f"/api/v1/ats/reports/{report_id}/pdf")
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-1.4")


@pytest.mark.asyncio
async def test_endpoint_delete_report(client):
    user_id = uuid.uuid4()
    report_id = uuid.uuid4()
    mock_user = User(id=user_id, email="bob@test.com", username="bob", password_hash="xyz", status="ACTIVE")

    mock_ats_svc = MagicMock()
    mock_ats_svc.delete_report = AsyncMock(return_value=True)

    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_ats_service] = lambda: mock_ats_svc

    response = client.delete(f"/api/v1/ats/reports/{report_id}")
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
