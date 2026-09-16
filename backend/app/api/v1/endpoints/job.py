import logging
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import (
    get_current_active_user,
    get_job_service,
    get_search_service,
    get_company_service,
    get_import_service
)
from app.models.auth import User
from app.schemas.job import (
    CompanyCreate,
    CompanyUpdate,
    CompanyOut,
    JobCreate,
    JobUpdate,
    JobOut,
    JobSearchResponse,
    SavedJobCreate,
    SavedJobOut,
    SavedSearchCreate,
    SavedSearchUpdate,
    SavedSearchOut,
    SearchHistoryOut
)
from app.services.job_engine import (
    CompanyService,
    JobService,
    SearchService,
    ImportService
)

logger = logging.getLogger("app.api.job")

router = APIRouter(prefix="/jobs", tags=["Enterprise Job Engine"])


# ==============================================================================
# 1. Company Endpoints
# ==============================================================================

@router.get("/companies", response_model=List[CompanyOut], status_code=status.HTTP_200_OK)
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    company_svc: CompanyService = Depends(get_company_service)
) -> List[Any]:
    """
    List registered corporate profiles and industries.
    """
    return await company_svc.list_companies(skip=skip, limit=limit)


@router.get("/companies/{id}", response_model=CompanyOut, status_code=status.HTTP_200_OK)
async def get_company_by_id(
    id: uuid.UUID,
    company_svc: CompanyService = Depends(get_company_service)
) -> Any:
    """
    Fetch a corporate profile by its unique ID.
    """
    company = await company_svc.get_company(id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile not found."
        )
    return company


@router.post("/companies", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
async def create_company_profile(
    payload: CompanyCreate,
    current_user: User = Depends(get_current_active_user),
    company_svc: CompanyService = Depends(get_company_service)
) -> Any:
    """
    Register a new corporate profile.
    """
    try:
        return await company_svc.create_company(payload)
    except Exception as e:
        logger.error(f"Failed to create company: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register corporate profile: {str(e)}"
        )


@router.put("/companies/{id}", response_model=CompanyOut, status_code=status.HTTP_200_OK)
async def update_company_profile(
    id: uuid.UUID,
    payload: CompanyUpdate,
    current_user: User = Depends(get_current_active_user),
    company_svc: CompanyService = Depends(get_company_service)
) -> Any:
    """
    Update details on a corporate profile.
    """
    company = await company_svc.update_company(id, payload)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile not found or unavailable."
        )
    return company


# ==============================================================================
# 2. Ingestion/Import Endpoints
# ==============================================================================

@router.post("/import", status_code=status.HTTP_200_OK)
async def import_job_from_source(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    import_svc: ImportService = Depends(get_import_service)
) -> Dict[str, Any]:
    """
    Directly ingest and index a job feed entry from standard providers.
    Triggers automated enterprise deduplication checks.
    """
    source = payload.get("source")
    raw_payload = payload.get("raw_payload")

    if not source or not raw_payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both 'source' and 'raw_payload' fields must be provided."
        )

    try:
        job, is_new = await import_svc.import_job_listing(source, raw_payload)
        return {
            "status": "success",
            "message": "Job ingested successfully.",
            "is_new_listing": is_new,
            "job_id": str(job.id),
            "title": job.title,
            "company_name": job.company_name
        }
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        logger.error(f"Job ingestion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"External ingestion crashed: {str(e)}"
        )


# ==============================================================================
# 3. Main Job Endpoints
# ==============================================================================

@router.get("", response_model=JobSearchResponse, status_code=status.HTTP_200_OK)
async def search_and_filter_jobs(
    keyword: Optional[str] = Query(None, description="Keywords to match in title, description, or industry"),
    location: Optional[str] = Query(None, description="Geographic location filter"),
    employment_type: Optional[str] = Query(None, description="Employment type (Full-time, Part-time, Contract, etc.)"),
    experience_level: Optional[str] = Query(None, description="Experience level (Entry, Mid-level, Senior, Executive)"),
    remote_status: Optional[str] = Query(None, description="Onsite, Hybrid, or Remote style"),
    visa_sponsorship: Optional[bool] = Query(None, description="Filter jobs providing visa sponsorships"),
    min_salary: Optional[float] = Query(None, description="Minimum salary bracket"),
    skills: Optional[List[str]] = Query(None, description="Skill requirements to match"),
    sort_by: str = Query("posted_at", description="Field to sort by (posted_at, salary_max, title)"),
    sort_desc: bool = Query(True, description="Sort descending if true"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_active_user),  # Optional auth to capture history
    search_svc: SearchService = Depends(get_search_service)
) -> Any:
    """
    Search active jobs with multi-layered criteria. Automatically registers Search History audits.
    """
    user_id = current_user.id if current_user else None
    items, total = await search_svc.execute_search(
        user_id=user_id,
        keyword=keyword,
        location=location,
        employment_type=employment_type,
        experience_level=experience_level,
        remote_status=remote_status,
        visa_sponsorship=visa_sponsorship,
        min_salary=min_salary,
        skills=skills,
        sort_by=sort_by,
        sort_desc=sort_desc,
        skip=skip,
        limit=limit
    )
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/saved", response_model=List[SavedJobOut], status_code=status.HTTP_200_OK)
async def list_saved_bookmarks(
    folder: Optional[str] = Query(None, description="Filter bookmarks inside a specific folder"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    job_svc: JobService = Depends(get_job_service)
) -> List[Any]:
    """
    Retrieve current user's job bookmarks, optionally filtered by folder name.
    """
    return await job_svc.list_saved_jobs(user_id=current_user.id, folder=folder, skip=skip, limit=limit)


@router.post("/saved", response_model=SavedJobOut, status_code=status.HTTP_201_CREATED)
async def bookmark_job_listing(
    payload: SavedJobCreate,
    current_user: User = Depends(get_current_active_user),
    job_svc: JobService = Depends(get_job_service)
) -> Any:
    """
    Add a job listing to bookmarks folder.
    """
    try:
        return await job_svc.save_job(user_id=current_user.id, save_in=payload)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err)
        )
    except Exception as e:
        logger.error(f"Failed to bookmark job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bookmark job listing: {str(e)}"
        )


@router.delete("/saved/{job_id}", status_code=status.HTTP_200_OK)
async def remove_job_bookmark(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    job_svc: JobService = Depends(get_job_service)
) -> dict:
    """
    Delete a saved job bookmark.
    """
    deleted = await job_svc.unsave_job(user_id=current_user.id, job_id=job_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark association not found."
        )
    return {"status": "success", "message": "Job bookmark removed successfully."}


@router.get("/saved-searches", response_model=List[SavedSearchOut], status_code=status.HTTP_200_OK)
async def list_saved_searches(
    current_user: User = Depends(get_current_active_user),
    search_svc: SearchService = Depends(get_search_service)
) -> List[Any]:
    """
    Retrieve user's saved searches and automated alert configurations.
    """
    return await search_svc.list_saved_searches(user_id=current_user.id)


@router.post("/saved-searches", response_model=SavedSearchOut, status_code=status.HTTP_201_CREATED)
async def create_saved_search_alert(
    payload: SavedSearchCreate,
    current_user: User = Depends(get_current_active_user),
    search_svc: SearchService = Depends(get_search_service)
) -> Any:
    """
    Save current search criteria and configure notification flags.
    """
    try:
        return await search_svc.create_saved_search(user_id=current_user.id, search_in=payload)
    except Exception as e:
        logger.error(f"Failed to save search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save search query: {str(e)}"
        )


@router.put("/saved-searches/{id}", response_model=SavedSearchOut, status_code=status.HTTP_200_OK)
async def update_saved_search_preferences(
    id: uuid.UUID,
    payload: SavedSearchUpdate,
    current_user: User = Depends(get_current_active_user),
    search_svc: SearchService = Depends(get_search_service)
) -> Any:
    """
    Update preferences for a saved search query or toggle notifications.
    """
    saved_search = await search_svc.update_saved_search(user_id=current_user.id, search_id=id, search_in=payload)
    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found or unauthorized access."
        )
    return saved_search


@router.delete("/saved-searches/{id}", status_code=status.HTTP_200_OK)
async def delete_saved_search(
    id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    search_svc: SearchService = Depends(get_search_service)
) -> dict:
    """
    Delete a saved search alert configuration.
    """
    deleted = await search_svc.delete_saved_search(user_id=current_user.id, search_id=id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found or unauthorized deletion request."
        )
    return {"status": "success", "message": "Saved search query deleted."}


@router.get("/history", response_model=List[SearchHistoryOut], status_code=status.HTTP_200_OK)
async def get_search_queries_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    search_svc: SearchService = Depends(get_search_service)
) -> List[Any]:
    """
    Retrieve user's audit log of recent search queries and keywords.
    """
    return await search_svc.get_search_history(user_id=current_user.id, limit=limit)


@router.get("/{id}", response_model=JobOut, status_code=status.HTTP_200_OK)
async def get_job_by_id(
    id: uuid.UUID,
    job_svc: JobService = Depends(get_job_service)
) -> Any:
    """
    Fetch details of a single job listing.
    """
    job = await job_svc.get_job(id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job listing not found."
        )
    return job


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job_listing(
    payload: JobCreate,
    current_user: User = Depends(get_current_active_user),
    job_svc: JobService = Depends(get_job_service)
) -> Any:
    """
    Manually create a new job listing.
    """
    try:
        return await job_svc.create_job(payload)
    except Exception as e:
        logger.error(f"Failed to create job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job listing: {str(e)}"
        )


@router.put("/{id}", response_model=JobOut, status_code=status.HTTP_200_OK)
async def update_job_listing(
    id: uuid.UUID,
    payload: JobUpdate,
    current_user: User = Depends(get_current_active_user),
    job_svc: JobService = Depends(get_job_service)
) -> Any:
    """
    Modify details on an existing job listing.
    """
    job = await job_svc.update_job(id, payload)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job listing not found or unavailable."
        )
    return job


@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_job_listing(
    id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    job_svc: JobService = Depends(get_job_service)
) -> dict:
    """
    Soft-delete a job listing from the platform.
    """
    deleted = await job_svc.delete_job(id, initiator=str(current_user.id))
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job listing not found or unauthorized deletion request."
        )
    return {"status": "success", "message": "Job listing deleted successfully."}
