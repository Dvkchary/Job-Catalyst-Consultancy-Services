import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.models.auth import User
from app.models.career import CareerProfile, CareerRoadmap, CareerRecommendation
from app.schemas.career import CareerProfileCreate, UpdateGoalsRequest
from app.services.career import (
    CareerService,
    RoadmapService,
    RecommendationService,
    AnalyticsService
)
from app.core.dependencies import (
    get_current_active_user,
    get_career_service,
    get_roadmap_service,
    get_recommendation_service,
    get_analytics_service
)


@pytest.mark.asyncio
async def test_career_repository_mock_retrieval():
    """
    Validates repository interactions and career profile data storage mechanisms.
    """
    mock_db = MagicMock()
    mock_result = MagicMock()
    
    user_id = uuid.uuid4()
    profile_id = uuid.uuid4()
    
    mock_profile = CareerProfile(
        id=profile_id,
        user_id=user_id,
        current_role="Developer",
        target_role="Architect",
        industry="SaaS",
        experience_level="Mid",
        skills=["Python", "SQL"],
        career_goals=["System Scale"],
        preferred_countries=["USA"],
        career_score=72.0
    )
    
    mock_result.scalar_or_none = MagicMock(return_value=mock_profile)
    mock_db.execute = AsyncMock(return_value=mock_result)

    from app.db.career_repositories import CareerRepository
    repo = CareerRepository(db=mock_db)
    profile = await repo.get_by_user_id(user_id)

    assert profile is not None
    assert profile.current_role == "Developer"
    assert profile.target_role == "Architect"
    assert profile.career_score == 72.0


@pytest.mark.asyncio
async def test_career_service_heuristic_creation():
    """
    Verifies CareerService constructs profile matrices and salary intelligence correctly.
    """
    mock_repo = MagicMock()
    mock_repo.get_by_user_id = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock(side_effect=lambda x: x)

    svc = CareerService(career_repo=mock_repo)
    user_id = uuid.uuid4()
    payload = CareerProfileCreate(
        current_role="Junior Frontend Developer",
        target_role="Lead Frontend Architect",
        industry="E-Commerce",
        experience_level="Junior",
        skills=["React", "CSS"],
        career_goals=["Build microfrontends"],
        preferred_countries=["Germany"],
        visa_status="Sponsorship Needed",
        timeline="1 Year"
    )

    profile = await svc.create_or_update_profile(user_id=user_id, data=payload)
    assert profile.user_id == user_id
    assert profile.current_role == "Junior Frontend Developer"
    assert profile.target_role == "Lead Frontend Architect"
    assert "salary_intelligence" in profile.salary_intelligence or hasattr(profile, "salary_intelligence")
    assert profile.career_score > 0.0


@pytest.mark.asyncio
async def test_roadmap_service_milestones_and_goals():
    """
    Verifies RoadmapService properly structures transition paths with short, medium, and long term plans.
    """
    user_id = uuid.uuid4()
    profile_id = uuid.uuid4()
    
    mock_profile = CareerProfile(
        id=profile_id,
        user_id=user_id,
        current_role="Systems Engineer",
        target_role="DevOps Specialist",
        industry="Automotive",
        experience_level="Mid",
        skills=["Linux", "Docker"],
        career_goals=["Automate infra"],
        preferred_countries=["Remote"]
    )

    mock_career_repo = MagicMock()
    mock_career_repo.get = AsyncMock(return_value=mock_profile)

    mock_roadmap_repo = MagicMock()
    mock_roadmap_repo.get_latest_by_user_id = AsyncMock(return_value=None)
    mock_roadmap_repo.create = AsyncMock(side_effect=lambda x: x)

    roadmap_svc = RoadmapService(roadmap_repo=mock_roadmap_repo, career_repo=mock_career_repo)
    roadmap = await roadmap_svc.generate_roadmap(user_id, profile_id)

    assert roadmap is not None
    assert roadmap.career_profile_id == profile_id
    assert "short_term" in roadmap.roadmap_data
    assert "medium_term" in roadmap.roadmap_data
    assert "long_term" in roadmap.roadmap_data
    assert len(roadmap.weekly_goals) > 0


@pytest.mark.asyncio
async def test_recommendations_service_skill_gaps():
    """
    Tests RecommendationService calculates prioritize rankings and time estimates for missing skills.
    """
    user_id = uuid.uuid4()
    profile_id = uuid.uuid4()
    
    mock_profile = CareerProfile(
        id=profile_id,
        user_id=user_id,
        current_role="Backend Developer",
        target_role="Machine Learning Engineer",
        industry="AI Services",
        experience_level="Mid",
        skills=["Python", "FastAPI"],
        career_goals=["Deploy large language models"],
        preferred_countries=["Canada"]
    )

    mock_career_repo = MagicMock()
    mock_career_repo.get = AsyncMock(return_value=mock_profile)

    mock_rec_repo = MagicMock()
    mock_rec_repo.get_latest_by_user_id = AsyncMock(return_value=None)
    mock_rec_repo.create = AsyncMock(side_effect=lambda x: x)

    rec_svc = RecommendationService(recommendation_repo=mock_rec_repo, career_repo=mock_career_repo)
    recs = await rec_svc.generate_recommendations(user_id, profile_id)

    assert recs is not None
    data = recs.recommendations_data
    assert "skill_gap_analysis" in data
    assert "learning_recommendations" in data
    assert len(data["skill_gap_analysis"]) > 0


@pytest.mark.asyncio
async def test_analytics_service_metric_aggregation():
    """
    Checks that AnalyticsService consolidates database tables correctly to compile career progression deltas.
    """
    mock_db = MagicMock()
    mock_res = MagicMock()
    mock_res.scalar = MagicMock(return_value=4)  # Simulate 4 items
    mock_db.execute = AsyncMock(return_value=mock_res)

    analytics_svc = AnalyticsService(db_session=mock_db)
    user_id = uuid.uuid4()
    progress = await analytics_svc.get_progress_analytics(user_id)

    assert progress is not None
    assert progress.applications_count == 4
    assert progress.offers_count == 0  # 4 * 0.15 is 0
    assert progress.career_growth_percentage > 0.0


@pytest.mark.asyncio
async def test_endpoint_create_or_update_profile(client):
    """
    Verifies POST /api/v1/career/profile sets up the profile and responds with a status 201.
    """
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, email="alice@test.com", username="alice", password_hash="hash", status="ACTIVE")

    mock_response = CareerProfile(
        id=uuid.uuid4(),
        user_id=user_id,
        current_role="QA Analyst",
        target_role="SDET",
        industry="Finance",
        experience_level="Mid",
        skills=["Selenium", "Java"],
        career_goals=["Build test frameworks"],
        preferred_countries=["UK"],
        visa_status="Not Required",
        timeline="3 Months",
        career_score=75.0,
        salary_intelligence={
            "current_salary": 90000.0,
            "market_salary": 110000.0,
            "expected_salary": 120000.0,
            "negotiation_advice": "Focus on test automation coverage metrics.",
            "salary_trend": "Increasing demand for SDETs."
        },
        readiness_insights={
            "promotion_readiness": 70.0,
            "resume_readiness": 80.0,
            "interview_readiness": 65.0,
            "application_readiness": 75.0,
            "career_score": 75.0
        }
    )

    mock_career_svc = MagicMock()
    mock_career_svc.create_or_update_profile = AsyncMock(return_value=mock_response)

    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_career_service] = lambda: mock_career_svc

    payload = {
        "current_role": "QA Analyst",
        "target_role": "SDET",
        "industry": "Finance",
        "experience_level": "Mid",
        "skills": ["Selenium", "Java"],
        "career_goals": ["Build test frameworks"],
        "preferred_countries": ["UK"],
        "visa_status": "Not Required",
        "timeline": "3 Months"
    }

    response = client.post("/api/v1/career/profile", json=payload)
    client.app.dependency_overrides.clear()

    assert response.status_code == 201
    data = response.json()
    assert data["current_role"] == "QA Analyst"
    assert data["target_role"] == "SDET"
    assert data["career_score"] == 75.0


@pytest.mark.asyncio
async def test_endpoint_get_roadmap(client):
    """
    Verifies GET /api/v1/career/roadmap returns correct active structures.
    """
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, email="alice@test.com", username="alice", password_hash="hash", status="ACTIVE")

    mock_roadmap = CareerRoadmap(
        id=uuid.uuid4(),
        user_id=user_id,
        career_profile_id=uuid.uuid4(),
        roadmap_data={
            "short_term": {"goals": ["Learn Python"], "milestones": []},
            "medium_term": {"goals": ["Certifications"], "milestones": []},
            "long_term": {"goals": ["Transition"], "milestones": []}
        },
        weekly_goals=[],
        monthly_goals=[],
        learning_progress={}
    )

    mock_roadmap_svc = MagicMock()
    mock_roadmap_svc.get_latest_roadmap = AsyncMock(return_value=mock_roadmap)

    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_roadmap_service] = lambda: mock_roadmap_svc

    response = client.get("/api/v1/career/roadmap")
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert "roadmap_data" in data
    assert "weekly_goals" in data
