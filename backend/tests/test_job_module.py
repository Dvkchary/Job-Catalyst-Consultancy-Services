import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.models.auth import User
from app.models.job import Company, Job, SavedJob, SavedSearch, SearchHistory
from app.schemas.job import (
    CompanyCreate,
    CompanyUpdate,
    JobCreate,
    JobUpdate,
    SavedJobCreate,
    SavedSearchCreate,
    SavedSearchUpdate
)
from app.services.job_engine import CompanyService, JobService, SearchService, ImportService
from app.core.dependencies import (
    get_company_service,
    get_job_service,
    get_search_service,
    get_import_service,
    get_current_active_user
)


# ==============================================================================
# 1. Unit Tests for Services and Business Logic
# ==============================================================================

@pytest.mark.asyncio
async def test_company_service_create_and_fetch():
    company_repo = MagicMock()
    company_repo.get_by_name = AsyncMock(return_value=None)
    company_repo.create = AsyncMock(return_value=Company(id=uuid.uuid4(), name="Google", industry="Tech"))

    svc = CompanyService(company_repo)
    new_comp = await svc.create_company(CompanyCreate(name="Google", industry="Tech"))

    assert new_comp.name == "Google"
    assert new_comp.industry == "Tech"
    company_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_job_service_creation_resolves_company():
    job_repo = MagicMock()
    job_repo.create = AsyncMock(return_value=Job(id=uuid.uuid4(), title="Python Dev", company_name="Google"))
    
    company_repo = MagicMock()
    company_repo.get_by_name = AsyncMock(return_value=Company(id=uuid.uuid4(), name="Google"))

    saved_job_repo = MagicMock()

    svc = JobService(job_repo, company_repo, saved_job_repo)
    job_in = JobCreate(
        title="Python Dev",
        company_name="Google",
        location="Remote",
        description="Great role",
        source="LinkedIn"
    )
    job = await svc.create_job(job_in)

    assert job.title == "Python Dev"
    assert job.company_name == "Google"
    company_repo.get_by_name.assert_called_once_with("Google")


@pytest.mark.asyncio
async def test_job_service_bookmark_workflow():
    job_repo = MagicMock()
    job_repo.get = AsyncMock(return_value=Job(id=uuid.uuid4()))
    
    company_repo = MagicMock()
    
    saved_job_repo = MagicMock()
    saved_job_repo.get_by_user_and_job = AsyncMock(return_value=None)
    saved_job_repo.create = AsyncMock(return_value=SavedJob(id=uuid.uuid4(), folder="Wishlist"))

    svc = JobService(job_repo, company_repo, saved_job_repo)
    user_id = uuid.uuid4()
    job_id = uuid.uuid4()
    
    bookmark = await svc.save_job(user_id, SavedJobCreate(job_id=job_id, folder="Wishlist"))
    assert bookmark.folder == "Wishlist"
    saved_job_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_search_service_executes_query():
    job_repo = MagicMock()
    job_repo.search_jobs = AsyncMock(return_value=[Job(id=uuid.uuid4(), title="Staff Engineer")])
    job_repo.count_search_results = AsyncMock(return_value=1)

    saved_search_repo = MagicMock()
    search_history_repo = MagicMock()
    search_history_repo.create = AsyncMock()

    svc = SearchService(job_repo, saved_search_repo, search_history_repo)
    user_id = uuid.uuid4()

    items, total = await svc.execute_search(
        user_id=user_id,
        keyword="Staff",
        location="SF"
    )

    assert total == 1
    assert items[0].title == "Staff Engineer"
    # Ensure audit log is recorded
    search_history_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_import_service_normalizes_and_deduplicates():
    job_service = MagicMock()
    job_service.update_job = AsyncMock(return_value=Job(id=uuid.uuid4(), title="Manager (Updated)"))
    job_service.create_job = AsyncMock()

    job_repo = MagicMock()
    # Mocking existing record to test update/deduplication flow
    job_repo.get_by_source_id = AsyncMock(return_value=Job(id=uuid.uuid4(), title="Manager"))

    svc = ImportService(job_service, job_repo)
    payload = {
        "id": "ext-101",
        "title": "Manager",
        "company": "Netflix",
        "workplace": "Remote",
        "description": "Lead the team"
    }

    job, is_new = await svc.import_job_listing("LinkedIn", payload)
    
    assert is_new is False
    assert job.title == "Manager (Updated)"
    job_service.update_job.assert_called_once()


# ==============================================================================
# 2. Integration / API Endpoint Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_endpoint_list_companies(client):
    mock_company_svc = MagicMock()
    mock_company_svc.list_companies = AsyncMock(return_value=[
        Company(
            id=uuid.uuid4(),
            name="Apple",
            industry="Tech",
            locations=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ])

    app = client.app
    app.dependency_overrides[get_company_service] = lambda: mock_company_svc

    response = client.get("/api/v1/jobs/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Apple"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_endpoint_search_jobs(client):
    mock_search_svc = MagicMock()
    mock_search_svc.execute_search = AsyncMock(return_value=(
        [Job(
            id=uuid.uuid4(),
            company_name="Stripe",
            title="Backend Lead",
            location="Remote",
            employment_type="Full-time",
            currency="USD",
            experience_level="Mid-level",
            remote_status="Onsite",
            visa_sponsorship=False,
            skills=[],
            benefits=[],
            description="Great team",
            source="LinkedIn",
            posted_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )],
        1
    ))

    # Mock user auth to bypass dependency
    mock_user = User(id=uuid.uuid4(), email="auth@test.com", username="auth", status="ACTIVE")
    app = client.app
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    app.dependency_overrides[get_search_service] = lambda: mock_search_svc

    response = client.get("/api/v1/jobs?keyword=Backend&location=Remote")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Backend Lead"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_endpoint_bookmark_job(client):
    mock_job_svc = MagicMock()
    job_id = uuid.uuid4()
    saved_id = uuid.uuid4()
    mock_job_svc.save_job = AsyncMock(return_value=SavedJob(
        id=saved_id,
        user_id=uuid.uuid4(),
        job_id=job_id,
        folder="Tech Jobs",
        created_at=datetime.utcnow(),
        job=Job(
            id=job_id,
            company_name="Microsoft",
            title="Azure Architect",
            location="Seattle",
            employment_type="Full-time",
            currency="USD",
            experience_level="Mid-level",
            remote_status="Onsite",
            visa_sponsorship=False,
            skills=[],
            benefits=[],
            description="Cloud architect role",
            source="LinkedIn",
            posted_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ))

    mock_user = User(id=uuid.uuid4(), email="bookmark@test.com", username="bookmarker", status="ACTIVE")
    app = client.app
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    app.dependency_overrides[get_job_service] = lambda: mock_job_svc

    response = client.post("/api/v1/jobs/saved", json={"job_id": str(job_id), "folder": "Tech Jobs"})
    assert response.status_code == 201
    data = response.json()
    assert data["folder"] == "Tech Jobs"
    assert data["job"]["company_name"] == "Microsoft"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_endpoint_ingest_external_job(client):
    mock_import_svc = MagicMock()
    mock_job = Job(
        id=uuid.uuid4(),
        company_name="Nvidia",
        title="CUDA Researcher",
        location="Santa Clara",
        description="Accelerate computing",
        source="Greenhouse",
        posted_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    mock_import_svc.import_job_listing = AsyncMock(return_value=(mock_job, True))

    mock_user = User(id=uuid.uuid4(), email="importer@test.com", username="ingester", status="ACTIVE")
    app = client.app
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    app.dependency_overrides[get_import_service] = lambda: mock_import_svc

    payload = {
        "source": "Greenhouse",
        "raw_payload": {
            "id": "nv-9009",
            "title": "CUDA Researcher",
            "company": "Nvidia",
            "location": "Santa Clara",
            "description": "Accelerate computing"
        }
    }

    response = client.post("/api/v1/jobs/import", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["is_new_listing"] is True
    assert data["title"] == "CUDA Researcher"

    app.dependency_overrides.clear()
