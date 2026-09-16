import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.models.auth import User
from app.models.dashboard import DashboardWidget, ExecutiveReport
from app.models.resume import Resume
from app.models.ats import ATSReport
from app.models.interview import InterviewSession
from app.models.job import SavedJob
from app.models.career import CareerProfile, CareerRoadmap, CareerRecommendation
from app.schemas.dashboard import ReportGenerateRequest, WidgetBulkLayoutUpdate
from app.services.dashboard import (
    DashboardService,
    PlatformAnalyticsService,
    ReportService,
    ExportService
)
from app.core.dependencies import (
    get_current_active_user,
    get_dashboard_service,
    get_platform_analytics_service,
    get_report_service,
    get_export_service
)


@pytest.mark.asyncio
async def test_dashboard_widget_repository_or_defaults():
    """
    Ensures default workspace layouts populate when no widgets are found.
    """
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    
    # Return empty list on first check, so defaults are generated
    mock_scalars = MagicMock()
    mock_scalars.all = MagicMock(return_value=[])
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=mock_scalars)
    mock_db.execute.return_value = mock_result

    from app.db.dashboard_repositories import DashboardWidgetRepository
    repo = DashboardWidgetRepository(db=mock_db)
    
    user_id = uuid.uuid4()
    widgets = await repo.get_or_create_default_widgets(user_id=user_id)
    
    assert len(widgets) > 0
    assert widgets[0].user_id == user_id
    assert widgets[0].is_visible is True


@pytest.mark.asyncio
async def test_analytics_repository_metrics_and_heuristic_fallbacks():
    """
    Tests AnalyticsRepository joins and averages mock datasets.
    """
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    
    # Mock return values for multi queries
    mock_scalars = MagicMock()
    mock_scalars.all = MagicMock(return_value=[])
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=mock_scalars)
    mock_result.scalar = MagicMock(return_value=12) # For counts
    mock_db.execute.return_value = mock_result

    from app.db.dashboard_repositories import AnalyticsRepository
    repo = AnalyticsRepository(db=mock_db)
    
    user_id = uuid.uuid4()
    res_analytics = await repo.get_resume_analytics(user_id)
    job_analytics = await repo.get_job_analytics(user_id)
    int_analytics = await repo.get_interview_analytics(user_id)
    
    assert "resume_views" in res_analytics
    assert job_analytics["applications_submitted"] == 12
    assert "average_score" in int_analytics


@pytest.mark.asyncio
async def test_dashboard_service_summary_assembly():
    """
    Verifies DashboardService merges sub-logs chronologically.
    """
    mock_widget_repo = MagicMock()
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()

    # Empty mock returns
    mock_scalars = MagicMock()
    mock_scalars.all = MagicMock(return_value=[])
    mock_result = MagicMock()
    mock_result.scalar_or_none = MagicMock(return_value=None)
    mock_result.scalars = MagicMock(return_value=mock_scalars)
    mock_db.execute.return_value = mock_result

    svc = DashboardService(widget_repo=mock_widget_repo, db_session=mock_db)
    user_id = uuid.uuid4()
    summary = await svc.get_summary(user_id)

    assert summary.welcome_message.startswith("Welcome back")
    assert len(summary.quick_actions) == 3
    assert "target_ready_percentage" in summary.career_progress


@pytest.mark.asyncio
async def test_report_service_growth_areas_and_actions():
    """
    Verifies ReportService correctly highlights gaps and generates customized action cards.
    """
    mock_report_repo = MagicMock()
    mock_report_repo.create = AsyncMock(side_effect=lambda x: ExecutiveReport(id=uuid.uuid4(), **x))
    
    mock_analytics_repo = MagicMock()
    mock_analytics_repo.get_resume_analytics = AsyncMock(return_value={"resume_score_history": [{"score": 65}]})
    mock_analytics_repo.get_job_analytics = AsyncMock(return_value={"applications_submitted": 1})
    mock_analytics_repo.get_interview_analytics = MagicMock(return_value={"average_score": 60.0, "success_rate": 0.0})
    mock_analytics_repo.get_career_analytics = MagicMock(return_value={"career_score": 62.0})
    mock_analytics_repo.get_ai_analytics = MagicMock(return_value={"estimated_cost": 0.05})

    mock_db = MagicMock()
    
    svc = ReportService(report_repo=mock_report_repo, analytics_repo=mock_analytics_repo, db_session=mock_db)
    
    user_id = uuid.uuid4()
    payload = ReportGenerateRequest(report_type="Weekly")
    report = await svc.generate_report(user_id=user_id, payload=payload)

    assert report.report_type == "Weekly"
    content = report.content_json
    assert "growth_areas" in content
    assert len(content["action_items"]) > 0


@pytest.mark.asyncio
async def test_export_service_base64_renders():
    """
    Tests ExportService builds valid document structures and encodes them.
    """
    mock_report = ExecutiveReport(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        report_type="Monthly",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow(),
        content_json={
            "metadata": {"generated_at": datetime.utcnow().isoformat()},
            "kpi_overview": {"resume_score_average": 82.5, "career_readiness_score": 75.0},
            "strengths": ["Strong candidate base."],
            "growth_areas": ["Needs behavioral practice."],
            "action_items": ["Optimizations."]
        },
        export_meta={}
    )

    mock_report_repo = MagicMock()
    mock_report_repo.get = AsyncMock(return_value=mock_report)

    svc = ExportService(report_repo=mock_report_repo)
    user_id = mock_report.user_id
    
    pdf_res = await svc.export_pdf_b64(user_id=user_id, report_id=mock_report.id)
    excel_res = await svc.export_excel_b64(user_id=user_id, report_id=mock_report.id)

    assert pdf_res.media_type == "application/pdf"
    assert len(pdf_res.content_b64) > 0
    assert excel_res.media_type == "text/csv"
    assert len(excel_res.content_b64) > 0


@pytest.mark.asyncio
async def test_endpoint_get_dashboard_summary(client):
    """
    Verifies GET /api/v1/dashboard/summary response.
    """
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, email="bob@test.com", username="bob", password_hash="hash", status="ACTIVE")

    mock_summary = {
        "welcome_message": "Welcome back, Bob!",
        "daily_summary": "Today you saved 3 jobs.",
        "weekly_summary": "Focus on certifications.",
        "monthly_summary": "High progress tracker.",
        "quick_actions": [],
        "recent_activity": [],
        "career_progress": {"total_scans": 2, "target_ready_percentage": 80.0}
    }

    mock_svc = MagicMock()
    mock_svc.get_summary = AsyncMock(return_value=mock_summary)

    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_dashboard_service] = lambda: mock_svc

    response = client.get("/api/v1/dashboard/summary")
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["welcome_message"] == "Welcome back, Bob!"
    assert "career_progress" in data


@pytest.mark.asyncio
async def test_endpoint_widgets_bulk_update(client):
    """
    Verifies PUT /api/v1/dashboard/widgets/layout responds to coordinate mutations.
    """
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, email="bob@test.com", username="bob", password_hash="hash", status="ACTIVE")

    widget_id = uuid.uuid4()
    mock_widgets = [
        DashboardWidget(
            id=widget_id,
            user_id=user_id,
            widget_key="ats_scores",
            title="ATS Scores",
            is_visible=True,
            layout_x=2,
            layout_y=2,
            layout_w=4,
            layout_h=3,
            settings_json={}
        )
    ]

    mock_svc = MagicMock()
    mock_svc.update_bulk_layouts = AsyncMock(return_value=mock_widgets)

    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_dashboard_service] = lambda: mock_svc

    payload = [
        {
            "id": str(widget_id),
            "layout_x": 2,
            "layout_y": 2,
            "layout_w": 4,
            "layout_h": 3
        }
    ]

    response = client.put("/api/v1/dashboard/widgets/layout", json=payload)
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["layout_x"] == 2
    assert data[0]["widget_key"] == "ats_scores"
