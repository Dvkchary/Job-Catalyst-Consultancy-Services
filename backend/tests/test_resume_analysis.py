import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.models.auth import User
from app.models.resume import Resume
from app.schemas.resume import ResumeContentSchema
from app.services.resume_analysis import ResumeAnalysisService
from app.core.dependencies import get_current_active_user, get_resume_service


# ==============================================================================
# 1. Unit Tests for ResumeAnalysisService (Heuristics)
# ==============================================================================

def test_parse_date_heuristics():
    # Standard format
    d = ResumeAnalysisService.parse_date("2022-05-15")
    assert d is not None
    assert d.year == 2022
    assert d.month == 5

    # Short format
    d = ResumeAnalysisService.parse_date("2020-08")
    assert d is not None
    assert d.year == 2020
    assert d.month == 8

    # Year only
    d = ResumeAnalysisService.parse_date("2018")
    assert d is not None
    assert d.year == 2018

    # Present / Current ongoing
    d = ResumeAnalysisService.parse_date("Present")
    assert d is not None
    assert d.year == datetime.now().year

    # Invalid / empty string handling
    assert ResumeAnalysisService.parse_date(None) is None
    assert ResumeAnalysisService.parse_date("") is None


def test_calculate_duration_years():
    start = datetime(2020, 1, 1)
    end = datetime(2022, 1, 1)
    duration = ResumeAnalysisService.calculate_duration_years(start, end)
    # Approx 2 years
    assert abs(duration - 2.0) < 0.1

    # End before start
    assert ResumeAnalysisService.calculate_duration_years(end, start) == 0.0


def test_resume_completeness_and_quality_scoring_excellent():
    # Highly complete mock resume data matching excellent criteria
    content = {
        "personal_info": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@test.com",
            "phone": "+1-555-123-4567",
            "summary": "Experienced software architect focusing on FastAPI and Docker microservices with AWS.",
            "job_title": "Senior Solutions Architect"
        },
        "education": [
            {
                "school": "MIT",
                "degree": "Master of Science",
                "field_of_study": "Computer Science",
                "start_date": "2015-09",
                "end_date": "2017-06",
                "description": "Graduated with honors."
            }
        ],
        "experience": [
            {
                "company": "Tech Giant Corp",
                "title": "Lead Software Engineer",
                "start_date": "2020-01",
                "end_date": "Present",
                "current": True,
                "description": "- Designed scalable API architectures using FastAPI.\n- Managed dockerized Kubernetes deployments.\n- Optimized PostgreSQL query performance by 40%."
            },
            {
                "company": "Startup Hub",
                "title": "Software Engineer",
                "start_date": "2017-07",
                "end_date": "2019-12",
                "current": False,
                "description": "- Built React client web portals.\n- Integrated AWS microservices."
            }
        ],
        "skills": [
            {"name": "Python", "level": "EXPERT", "category": "Languages"},
            {"name": "FastAPI", "level": "EXPERT", "category": "Frameworks"},
            {"name": "Docker", "level": "INTERMEDIATE", "category": "DevOps"},
            {"name": "AWS", "level": "INTERMEDIATE", "category": "DevOps"},
            {"name": "PostgreSQL", "level": "EXPERT", "category": "Databases"},
            {"name": "React", "level": "INTERMEDIATE", "category": "Frontend"}
        ]
    }

    report = ResumeAnalysisService.analyze_resume_quality(content)

    assert report.health_score >= 80.0
    assert report.rating in ["EXCELLENT", "GOOD"]
    assert report.completeness_percentage >= 95.0
    assert report.statistics.total_words > 0
    assert report.statistics.total_sentences > 0
    assert report.date_analysis.is_chronological is True
    assert report.date_analysis.total_years_experience >= 6.0


def test_resume_quality_critical_poor():
    # Extremely sparse data failing basic heuristics
    content = {
        "personal_info": {
            "first_name": "",
            "last_name": "Smith",
            "email": "not-an-email",
            "phone": "",
            "summary": "Short."
        }
    }

    report = ResumeAnalysisService.analyze_resume_quality(content)

    assert report.health_score < 50.0
    assert report.rating == "CRITICAL"
    assert report.completeness_percentage < 40.0
    
    # Check that issues were flagged
    issue_categories = [i.category for i in report.issues]
    assert "COMPLETENESS" in issue_categories
    assert "FORMATTING" in issue_categories


def test_date_validation_overlapping_and_order():
    # Non-chronological with overlap
    content = {
        "personal_info": {
            "first_name": "Jane",
            "last_name": "Miller",
            "email": "jane@example.com"
        },
        "experience": [
            {
                "company": "Company B (older job listed first)",
                "title": "Developer",
                "start_date": "2015-01",
                "end_date": "2018-01",
                "description": "Short description of accomplishments."
            },
            {
                "company": "Company A (newer job listed second)",
                "title": "Senior Developer",
                "start_date": "2017-01",
                "end_date": "2022-01",
                "description": "Another short description."
            }
        ]
    }

    report = ResumeAnalysisService.analyze_resume_quality(content)

    assert report.date_analysis.is_chronological is False
    assert len(report.date_analysis.overlapping_intervals) > 0
    assert report.date_analysis.overlapping_intervals[0]["company_a"] == "Company B (older job listed first)"
    assert report.date_analysis.overlapping_intervals[0]["company_b"] == "Company A (newer job listed second)"


def test_duplicate_section_detection():
    content = {
        "personal_info": {
            "first_name": "Bob",
            "last_name": "Builder",
            "email": "bob@build.com"
        },
        "education": [
            {"school": "MIT", "degree": "BS", "field_of_study": "CS", "start_date": "2010"},
            {"school": "MIT", "degree": "BS", "field_of_study": "EE", "start_date": "2012"}  # Duplicate school + degree
        ],
        "skills": [
            {"name": "Python", "level": "EXPERT"},
            {"name": "python", "level": "BEGINNER"}  # Duplicate skill name
        ]
    }

    report = ResumeAnalysisService.analyze_resume_quality(content)
    
    # Duplicate entries detected key fields list
    assert len(report.duplicate_entries_detected) > 0
    
    dup_msgs = [i.message.lower() for i in report.issues if i.category == "DUPLICATE"]
    assert any("duplicate skill" in m for m in dup_msgs)
    assert any("duplicate education" in m for m in dup_msgs)


def test_keyword_extraction_and_spelling_hook():
    content = {
        "personal_info": {
            "first_name": "Alice",
            "last_name": "In Wonderland",
            "email": "alice@wonder.com",
            "summary": "i am a software engineer skilled in react, fastapi, and docker. spearheaded team."
        },
        "skills": [
            {"name": "js", "level": "EXPERT"},
            {"name": "postgres", "level": "EXPERT"}
        ]
    }

    report = ResumeAnalysisService.analyze_resume_quality(content)

    # Keyword check
    keywords = [k.keyword for k in report.keywords]
    assert "FastAPI" in keywords or "fastapi" in keywords or "React" in keywords or "Docker" in keywords
    assert "Spearheaded" in keywords or "spearheaded" in keywords

    # Spell casing normalization recommendation checks
    normalized_names = [s.original for s in report.normalized_skills]
    assert "js" in normalized_names
    assert "postgres" in normalized_names

    # Lowercase 'i' grammar issue
    grammars = [i.category for i in report.issues if i.category == "GRAMMAR"]
    assert "GRAMMAR" in grammars


# ==============================================================================
# 2. Integration / API Endpoint Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_endpoint_analyze_adhoc_resume(client):
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, email="6309vs@gmail.com", username="john_doe", password_hash="xyz", status="ACTIVE")

    # Override current active user dependency
    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user

    payload = {
        "personal_info": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@test.com",
            "summary": "Innovative engineer utilizing FastAPI and Docker for backend microservices."
        },
        "skills": [
            {"name": "Python", "level": "EXPERT"}
        ]
    }

    response = client.post("/api/v1/resume-analysis/analyze", json=payload)
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    res_data = response.json()
    assert "health_score" in res_data
    assert "rating" in res_data
    assert "score_breakdown" in res_data
    assert "statistics" in res_data


@pytest.mark.asyncio
async def test_endpoint_analyze_existing_resume_by_id(client):
    resume_id = uuid.uuid4()
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, email="6309vs@gmail.com", username="john_doe", password_hash="xyz", status="ACTIVE")

    # Mock resume database record
    mock_resume = Resume(
        id=resume_id,
        user_id=user_id,
        title="My Sample CV",
        content={
            "personal_info": {
                "first_name": "Bob",
                "last_name": "Sponge",
                "email": "bob@krab.com",
                "summary": "Sponge cook utilizing React and Docker."
            }
        }
    )

    # Mock Resume Service
    mock_svc = MagicMock()
    mock_svc.get_by_id = AsyncMock(return_value=mock_resume)

    # Override dependencies
    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_resume_service] = lambda: mock_svc

    response = client.get(f"/api/v1/resume-analysis/{resume_id}")
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["resume_id"] == str(resume_id)
    assert res_data["health_score"] > 0
    assert "statistics" in res_data


@pytest.mark.asyncio
async def test_endpoint_skills_normalization(client):
    mock_user = User(id=uuid.uuid4(), email="6309vs@gmail.com", username="john_doe", password_hash="xyz", status="ACTIVE")
    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user

    payload = {
        "skills": ["js", "postgres", "custom_tech"]
    }

    response = client.post("/api/v1/resume-analysis/skills/normalize", json=payload)
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    res_data = response.json()
    assert len(res_data) == 3
    # Check normalized outcomes
    assert res_data[0]["original"] == "js"
    assert res_data[0]["normalized"] == "JavaScript"
    assert res_data[1]["original"] == "postgres"
    assert res_data[1]["normalized"] == "PostgreSQL"
    assert res_data[2]["original"] == "custom_tech"
    assert res_data[2]["normalized"] == "custom_tech"
