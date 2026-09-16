import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.models.auth import User
from app.models.resume import Resume
from app.models.ats import ATSReport
from app.schemas.matching import MatchResumeRequest, CompareResumeRequest
from app.services.matching import ScoringService, RecommendationService, MatchingService
from app.core.dependencies import get_current_active_user, get_matching_service


def test_scoring_service_calculate_scores():
    """
    Validates heuristic algorithms of the ScoringService under typical inputs.
    """
    resume_skills = ["Python", "FastAPI", "PostgreSQL", "React", "TypeScript", "Docker"]
    resume_experience = [
        MagicMock(start_date="2021-01-01", end_date="2023-12-31")
    ]
    resume_education = [
        MagicMock(degree="Bachelor of Science in Computer Science")
    ]
    
    jd_text = "Looking for a Software Engineer with Python, FastAPI, and PostgreSQL. Required 2 years of experience."
    job_title = "FastAPI Software Engineer"

    (
        score_breakdown,
        skill_gap,
        exp_match,
        edu_match,
        loc_match,
        visa_match,
        salary_match
    ) = ScoringService.calculate_scores(
        resume_skills=resume_skills,
        resume_experience=resume_experience,
        resume_education=resume_education,
        jd_text=jd_text,
        job_title=job_title
    )

    # Validate overall structures
    assert score_breakdown.overall_match > 0.0
    assert score_breakdown.skill_score > 50.0
    assert score_breakdown.experience_score >= 60.0
    assert score_breakdown.education_score == 100.0
    
    # Check skill gaps
    assert "Python" in skill_gap.matching_skills
    assert "Fastapi" in skill_gap.matching_skills
    assert "Postgresql" in skill_gap.matching_skills


def test_recommendation_service_generate_recommendations():
    """
    Verifies RecommendationsService outputs are correctly customized to input gaps.
    """
    recs = RecommendationService.generate_recommendations(
        missing_skills=["Kubernetes", "AWS"],
        job_title="DevOps Engineer"
    )

    assert len(recs.resume_improvements) > 0
    assert "Kubernetes" in recs.skills_to_add
    assert "AWS" in recs.skills_to_add
    assert len(recs.projects_to_add) > 0


@pytest.mark.asyncio
async def test_matching_service_orchestrate(client):
    """
    Validates MatchingService logic flow and interaction with repositories.
    """
    user_id = uuid.uuid4()
    resume_id = uuid.uuid4()
    
    mock_resume = Resume(
        id=resume_id,
        user_id=user_id,
        title="Software Resume",
        content={
            "skills": ["Python", "FastAPI"],
            "experience": [],
            "education": []
        }
    )

    mock_db_report = ATSReport(
        id=uuid.uuid4(),
        user_id=user_id,
        resume_id=resume_id,
        job_title="Backend Engineer",
        job_description="FastAPI role",
        ats_score=85,
        report_data={}
    )

    # Setup Mocks
    mock_match_repo = MagicMock()
    mock_match_repo.create_match_report = AsyncMock(return_value=mock_db_report)
    mock_analysis_repo = MagicMock()
    mock_history_repo = MagicMock()
    
    mock_resume_repo = MagicMock()
    mock_resume_repo.get = AsyncMock(return_value=mock_resume)
    mock_job_repo = MagicMock()

    service = MatchingService(
        match_repo=mock_match_repo,
        analysis_repo=mock_analysis_repo,
        history_repo=mock_history_repo,
        resume_repo=mock_resume_repo,
        job_repo=mock_job_repo
    )

    report = await service.match_resume_to_job(
        user_id=user_id,
        resume_id=resume_id,
        job_id=None,
        job_description="Python FastAPI role"
    )

    assert report.resume_id == resume_id
    assert report.job_title == "Target Position"
    assert report.match_score_breakdown.overall_match > 0.0
    assert mock_match_repo.create_match_report.called


@pytest.mark.asyncio
async def test_endpoint_match_resume(client):
    """
    Tests POST /matching/match endpoint.
    """
    user_id = uuid.uuid4()
    resume_id = uuid.uuid4()
    mock_user = User(id=user_id, email="alice@test.com", username="alice", password_hash="hash", status="ACTIVE")

    mock_report_response = MatchingReportResponse(
        id=uuid.uuid4(),
        resume_id=resume_id,
        job_title="Backend Developer",
        match_score_breakdown={
            "overall_match": 88.5,
            "ats_score": 90.0,
            "skill_score": 85.0,
            "experience_score": 80.0,
            "education_score": 100.0,
            "location_score": 100.0,
            "visa_score": 100.0,
            "salary_score": 95.0,
            "confidence_score": 90.0
        },
        skill_gap_analysis={
            "missing_skills": [],
            "matching_skills": ["Python", "FastAPI"],
            "recommended_skills": [],
            "learning_suggestions": [],
            "certification_suggestions": []
        },
        experience_matching={
            "years_match": True,
            "relevant_match": True,
            "domain_match": True,
            "project_match": True,
            "candidate_years": 4.5,
            "required_years": 3.0
        },
        education_matching={
            "degree_match": True,
            "major_match": True,
            "required_education": "Bachelor's",
            "candidate_education": ["Bachelor's"]
        },
        location_matching={
            "remote_match": True,
            "preferred_match": True,
            "relocation_needed": False,
            "workplace_setting": "Remote"
        },
        visa_matching={
            "sponsorship_match": True,
            "work_auth_match": True,
            "sponsorship_required_by_candidate": False,
            "sponsorship_offered_by_company": False
        },
        salary_analysis={
            "salary_match_score": 95.0,
            "market_salary_range": "$120k",
            "salary_match_notes": "Perfect"
        },
        ai_recommendations={
            "resume_improvements": [],
            "skills_to_add": [],
            "projects_to_add": [],
            "keywords_to_add": [],
            "certifications": []
        },
        explainability={
            "why_matched": "Great overlap",
            "why_not_matched": "None",
            "strengths": [],
            "weaknesses": []
        }
    )

    mock_matching_svc = MagicMock()
    mock_matching_svc.match_resume_to_job = AsyncMock(return_value=mock_report_response)

    # Override dependencies
    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_matching_service] = lambda: mock_matching_svc

    payload = {
        "resume_id": str(resume_id),
        "job_description": "FastAPI engineer",
        "job_title": "Backend Developer"
    }

    response = client.post("/api/v1/matching/match", json=payload)
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["resume_id"] == str(resume_id)
    assert res_data["match_score_breakdown"]["overall_match"] == 88.5


@pytest.mark.asyncio
async def test_endpoint_analyze_job(client):
    """
    Tests POST /matching/analyze endpoint.
    """
    user_id = uuid.uuid4()
    resume_id = uuid.uuid4()
    mock_user = User(id=user_id, email="alice@test.com", username="alice", password_hash="hash", status="ACTIVE")

    mock_report_response = MatchingReportResponse(
        id=uuid.uuid4(),
        resume_id=resume_id,
        job_title="Frontend Engineer",
        match_score_breakdown={
            "overall_match": 82.0,
            "ats_score": 85.0,
            "skill_score": 80.0,
            "experience_score": 80.0,
            "education_score": 100.0,
            "location_score": 100.0,
            "visa_score": 100.0,
            "salary_score": 90.0,
            "confidence_score": 85.0
        },
        skill_gap_analysis={
            "missing_skills": [],
            "matching_skills": ["React"],
            "recommended_skills": [],
            "learning_suggestions": [],
            "certification_suggestions": []
        },
        experience_matching={
            "years_match": True,
            "relevant_match": True,
            "domain_match": True,
            "project_match": True,
            "candidate_years": 5.0,
            "required_years": 3.0
        },
        education_matching={
            "degree_match": True,
            "major_match": True,
            "required_education": "Bachelor's",
            "candidate_education": ["Bachelor's"]
        },
        location_matching={
            "remote_match": True,
            "preferred_match": True,
            "relocation_needed": False,
            "workplace_setting": "Remote"
        },
        visa_matching={
            "sponsorship_match": True,
            "work_auth_match": True,
            "sponsorship_required_by_candidate": False,
            "sponsorship_offered_by_company": False
        },
        salary_analysis={
            "salary_match_score": 90.0,
            "market_salary_range": "$110k",
            "salary_match_notes": "Good"
        },
        ai_recommendations={
            "resume_improvements": [],
            "skills_to_add": [],
            "projects_to_add": [],
            "keywords_to_add": [],
            "certifications": []
        },
        explainability={
            "why_matched": "Great",
            "why_not_matched": "None",
            "strengths": [],
            "weaknesses": []
        }
    )

    mock_matching_svc = MagicMock()
    mock_matching_svc.analyze_job_requirements = AsyncMock(return_value=mock_report_response)

    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_matching_service] = lambda: mock_matching_svc

    response = client.post(
        f"/api/v1/matching/analyze?resume_id={str(resume_id)}&job_title=Frontend Engineer&job_description=React role"
    )
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["match_score_breakdown"]["overall_match"] == 82.0


@pytest.mark.asyncio
async def test_endpoint_compare_resumes(client):
    """
    Tests POST /matching/compare endpoint.
    """
    user_id = uuid.uuid4()
    resume_a_id = uuid.uuid4()
    resume_b_id = uuid.uuid4()
    mock_user = User(id=user_id, email="alice@test.com", username="alice", password_hash="hash", status="ACTIVE")

    mock_compare_response = {
        "comparison_summary": "Resume A matches better",
        "winner": "Resume A",
        "score_difference": 12.0,
        "resume_a": {
            "id": str(resume_a_id),
            "score_breakdown": {
                "overall_match": 85.0
            },
            "strengths": [],
            "weaknesses": [],
            "missing_skills": []
        },
        "resume_b": {
            "id": str(resume_b_id),
            "score_breakdown": {
                "overall_match": 73.0
            },
            "strengths": [],
            "weaknesses": [],
            "missing_skills": []
        }
    }

    mock_matching_svc = MagicMock()
    mock_matching_svc.compare_two_resumes = AsyncMock(return_value=mock_compare_response)

    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_matching_service] = lambda: mock_matching_svc

    payload = {
        "resume_a_id": str(resume_a_id),
        "resume_b_id": str(resume_b_id),
        "job_description": "Backend engineer position"
    }

    response = client.post("/api/v1/matching/compare", json=payload)
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["winner"] == "Resume A"
    assert res_data["score_difference"] == 12.0


@pytest.mark.asyncio
async def test_endpoint_matching_history(client):
    """
    Tests GET /matching/history endpoint.
    """
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, email="alice@test.com", username="alice", password_hash="hash", status="ACTIVE")

    mock_history = [
        MatchHistoryItem(
            id=uuid.uuid4(),
            resume_id=uuid.uuid4(),
            job_title="Software Engineer",
            company_name="Tech Corp",
            overall_match=91.0,
            created_at=datetime.utcnow()
        )
    ]

    mock_matching_svc = MagicMock()
    mock_matching_svc.get_user_match_history = AsyncMock(return_value=mock_history)

    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_matching_service] = lambda: mock_matching_svc

    response = client.get("/api/v1/matching/history?limit=10&skip=0")
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    res_data = response.json()
    assert len(res_data) == 1
    assert res_data[0]["overall_match"] == 91.0
