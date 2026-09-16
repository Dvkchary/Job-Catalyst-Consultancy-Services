import uuid
import pytest
import datetime
from unittest.mock import AsyncMock, MagicMock

from app.models.auth import User, Role, Permission, UserSession
from app.models.admin import AuditLog, SystemConfiguration, FeatureFlag, ResumeTemplate, JobSource
from app.db.admin_repositories import (
    AdminRepository,
    AuditRepository,
    ConfigurationRepository,
    FeatureFlagRepository,
    ResumeTemplateRepository,
    JobSourceRepository
)
from app.services.admin import (
    AdminService,
    AuditService,
    ConfigurationService,
    MonitoringService
)
from app.core.dependencies import (
    get_current_active_user,
    require_role,
    get_admin_service,
    get_audit_service,
    get_configuration_service,
    get_monitoring_service
)


@pytest.mark.asyncio
async def test_admin_repository_search_users():
    """
    Tests that AdminRepository searches active accounts and returns matches with their roles.
    """
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    
    user1 = User(id=uuid.uuid4(), username="john_doe", email="john@test.com", status="ACTIVE")
    user1.roles = [Role(name="ADMIN")]
    
    mock_res = MagicMock()
    mock_res.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[user1])))
    mock_db.execute.return_value = mock_res

    repo = AdminRepository(db=mock_db)
    results = await repo.search_users(search_query="john")
    
    assert len(results) == 1
    assert results[0].username == "john_doe"
    assert results[0].roles[0].name == "ADMIN"


@pytest.mark.asyncio
async def test_audit_repository_search():
    """
    Validates filtering log sequences chronologically by system category.
    """
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()

    log_entry = AuditLog(
        id=uuid.uuid4(),
        category="Admin Action",
        action="UPDATE_USER",
        description="Changed status of candidate to active"
    )

    mock_res = MagicMock()
    mock_res.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[log_entry])))
    mock_db.execute.return_value = mock_res

    repo = AuditRepository(db=mock_db)
    results = await repo.search_audit_logs(category="Admin Action")
    
    assert len(results) == 1
    assert results[0].action == "UPDATE_USER"


@pytest.mark.asyncio
async def test_configuration_repository_save():
    """
    Verifies saving system dynamic variables.
    """
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()

    mock_res = MagicMock()
    mock_res.scalar_or_none = MagicMock(return_value=None)
    mock_db.execute.return_value = mock_res

    repo = ConfigurationRepository(db=mock_db)
    config = await repo.save_config_value(
        key="app_max_upload_size",
        category="Application",
        value={"size_mb": 15},
        description="Upload limit parameter"
    )

    assert config.config_key == "app_max_upload_size"
    assert config.config_value["size_mb"] == 15


@pytest.mark.asyncio
async def test_monitoring_service_checks():
    """
    Verifies general system components check out healthy.
    """
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    
    # DB mock returns 1 for health
    mock_res = MagicMock()
    mock_res.scalar = MagicMock(return_value=1)
    mock_db.execute.return_value = mock_res

    svc = MonitoringService(db=mock_db)
    health = await svc.check_health()
    
    assert health.db_connected is True
    assert health.redis_connected is True
    assert health.status == "healthy"


@pytest.mark.asyncio
async def test_admin_service_dashboard_overview():
    """
    Ensures AdminService compiles active user counts, estimated AI tokens, and sessions.
    """
    mock_admin_repo = MagicMock()
    mock_admin_repo.count = AsyncMock(return_value=10)
    mock_admin_repo.get_active_session_count = AsyncMock(return_value=4)
    mock_admin_repo.get_user_count_last_24h = AsyncMock(return_value=6)

    # Return empty log checklist
    mock_audit_repo = MagicMock()
    mock_audit_repo.get_multi = AsyncMock(return_value=[])
    mock_audit_svc = AuditService(audit_repo=mock_audit_repo)

    mock_monitoring_svc = MagicMock()
    mock_monitoring_svc.check_health = AsyncMock(return_value=MagicMock(
        db_connected=True, redis_connected=True, status="healthy", cpu_usage_percent=5.0, memory_usage_percent=20.0
    ))

    mock_template_repo = MagicMock()
    mock_job_source_repo = MagicMock()
    mock_db = MagicMock()

    svc = AdminService(
        admin_repo=mock_admin_repo,
        audit_svc=mock_audit_svc,
        monitoring_svc=mock_monitoring_svc,
        template_repo=mock_template_repo,
        job_source_repo=mock_job_source_repo,
        db_session=mock_db
    )

    overview = await svc.compile_dashboard_overview()
    
    assert overview.total_users == 10
    assert overview.active_sessions == 4
    assert overview.total_ai_tokens_used == 145000
    assert len(overview.recent_activities) == 1
    assert overview.recent_activities[0].action == "Bootstrap"


# =====================================================================
# API / CONTROLLER ENDPOINT TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_endpoint_admin_overview_api(client):
    """
    Verifies GET /api/v1/admin/overview endpoint.
    """
    mock_user = User(id=uuid.uuid4(), email="admin@test.com", username="admin_user", status="ACTIVE")
    mock_user.roles = [Role(name="ADMIN")]

    mock_overview = {
        "total_users": 150,
        "active_users_last_24h": 45,
        "active_sessions": 12,
        "total_revenue_usd": 2998.50,
        "total_ai_tokens_used": 2175000,
        "total_ai_cost_usd": 4.35,
        "system_health": {
            "status": "healthy",
            "cpu_usage_percent": 11.5,
            "memory_usage_percent": 42.0,
            "db_connected": True,
            "redis_connected": True,
            "queue_backlog": 0,
            "active_workers": 2
        },
        "recent_activities": [
            {
                "id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "username": "admin_user",
                "category": "Admin Action",
                "action": "CREATE_FEATURE_FLAG",
                "description": "Created progressive feature flag rollout",
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        ]
    }

    mock_admin_svc = MagicMock()
    mock_admin_svc.compile_dashboard_overview = AsyncMock(return_value=mock_overview)

    # Setup overrides for authentication and services
    client.app.dependency_overrides[require_role("ADMIN")] = lambda: mock_user
    client.app.dependency_overrides[get_admin_service] = lambda: mock_admin_svc

    response = client.get("/api/v1/admin/overview")
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] == 150
    assert data["system_health"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_endpoint_rbac_matrix_api(client):
    """
    Verifies GET /api/v1/admin/rbac/matrix endpoint.
    """
    mock_user = User(id=uuid.uuid4(), email="admin@test.com", username="admin_user", status="ACTIVE")
    mock_user.roles = [Role(name="ADMIN")]

    mock_matrix = {
        "roles": [
            {
                "id": str(uuid.uuid4()),
                "name": "ADMIN",
                "description": "Full privileges",
                "permissions": [
                    {"id": str(uuid.uuid4()), "name": "user:write", "description": "Update users"}
                ]
            }
        ],
        "all_permissions": [
            {"id": str(uuid.uuid4()), "name": "user:write", "description": "Update users"}
        ]
    }

    mock_admin_svc = MagicMock()
    mock_admin_svc.get_rbac_matrix = AsyncMock(return_value=mock_matrix)

    client.app.dependency_overrides[require_role("ADMIN")] = lambda: mock_user
    client.app.dependency_overrides[get_admin_service] = lambda: mock_admin_svc

    response = client.get("/api/v1/admin/rbac/matrix")
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert len(data["roles"]) == 1
    assert data["roles"][0]["name"] == "ADMIN"


@pytest.mark.asyncio
async def test_endpoint_monitoring_health_api(client):
    """
    Verifies GET /api/v1/admin/monitoring/health endpoint.
    """
    mock_user = User(id=uuid.uuid4(), email="admin@test.com", username="admin_user", status="ACTIVE")
    mock_user.roles = [Role(name="ADMIN")]

    mock_health = {
        "status": "healthy",
        "cpu_usage_percent": 8.5,
        "memory_usage_percent": 30.1,
        "db_connected": True,
        "redis_connected": True,
        "queue_backlog": 0,
        "active_workers": 4
    }

    mock_monitoring_svc = MagicMock()
    mock_monitoring_svc.check_health = AsyncMock(return_value=mock_health)

    client.app.dependency_overrides[require_role("ADMIN")] = lambda: mock_user
    client.app.dependency_overrides[get_monitoring_service] = lambda: mock_monitoring_svc

    response = client.get("/api/v1/admin/monitoring/health")
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["db_connected"] is True
    assert data["status"] == "healthy"
