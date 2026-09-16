import uuid
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from app.db.job_repositories import (
    CompanyRepository,
    JobRepository,
    SavedJobRepository,
    SavedSearchRepository,
    SearchHistoryRepository
)
from app.models.job import Company, Job, SavedJob, SavedSearch, SearchHistory
from app.schemas.job import (
    CompanyCreate,
    CompanyUpdate,
    JobCreate,
    JobUpdate,
    SavedJobCreate,
    SavedSearchCreate,
    SavedSearchUpdate,
    SearchHistoryCreate
)
from app.utils.datetime_utils import get_utc_now

logger = logging.getLogger("app.services.job_engine")


class CompanyService:
    """
    Service layer for managing corporate profiles, industry indexing, and scale classifications.
    """
    def __init__(self, company_repo: CompanyRepository) -> None:
        self.company_repo = company_repo

    async def get_company(self, company_id: uuid.UUID) -> Optional[Company]:
        return await self.company_repo.get(company_id)

    async def get_company_by_name(self, name: str) -> Optional[Company]:
        return await self.company_repo.get_by_name(name)

    async def create_company(self, company_in: CompanyCreate) -> Company:
        existing = await self.company_repo.get_by_name(company_in.name)
        if existing:
            return existing
        return await self.company_repo.create(company_in.model_dump())

    async def update_company(self, company_id: uuid.UUID, company_in: CompanyUpdate) -> Optional[Company]:
        db_obj = await self.company_repo.get(company_id)
        if not db_obj:
            return None
        return await self.company_repo.update(db_obj=db_obj, obj_in=company_in)

    async def list_companies(self, skip: int = 0, limit: int = 100) -> List[Company]:
        return await self.company_repo.get_multi(skip=skip, limit=limit)


class JobService:
    """
    Service layer managing central Job listings, bookmarks, and collection folders.
    """
    def __init__(
        self,
        job_repo: JobRepository,
        company_repo: CompanyRepository,
        saved_job_repo: SavedJobRepository
    ) -> None:
        self.job_repo = job_repo
        self.company_repo = company_repo
        self.saved_job_repo = saved_job_repo

    async def get_job(self, job_id: uuid.UUID) -> Optional[Job]:
        return await self.job_repo.get(job_id)

    async def create_job(self, job_in: JobCreate) -> Job:
        """
        Creates a new Job. If company_id is not specified but company_name is,
        it automatically looks up or registers the company.
        """
        obj_data = job_in.model_dump()
        
        # Link or create company automatically
        if not obj_data.get("company_id") and obj_data.get("company_name"):
            comp = await self.company_repo.get_by_name(obj_data["company_name"])
            if not comp:
                comp = await self.company_repo.create({"name": obj_data["company_name"]})
            obj_data["company_id"] = comp.id

        return await self.job_repo.create(obj_data)

    async def update_job(self, job_id: uuid.UUID, job_in: JobUpdate) -> Optional[Job]:
        db_obj = await self.job_repo.get(job_id)
        if not db_obj:
            return None
        return await self.job_repo.update(db_obj=db_obj, obj_in=job_in)

    async def delete_job(self, job_id: uuid.UUID, initiator: Optional[str] = None) -> bool:
        return await self.job_repo.delete(job_id, soft=True, initiator=initiator)

    # Saved Jobs / Bookmarks & Folders operations
    async def save_job(self, user_id: uuid.UUID, save_in: SavedJobCreate) -> SavedJob:
        """
        Saves/bookmarks a job in a specific folder.
        """
        # Verify job exists
        job = await self.job_repo.get(save_in.job_id)
        if not job:
            raise ValueError(f"Job with ID {save_in.job_id} does not exist.")

        # Check if already saved
        existing = await self.saved_job_repo.get_by_user_and_job(user_id, save_in.job_id)
        if existing:
            # If folder differs, update folder name
            if existing.folder != save_in.folder:
                existing.folder = save_in.folder
                await self.saved_job_repo.update(db_obj=existing, obj_in={"folder": save_in.folder})
            return existing

        db_input = {
            "user_id": user_id,
            "job_id": save_in.job_id,
            "folder": save_in.folder
        }
        return await self.saved_job_repo.create(db_input, creator_id=str(user_id))

    async def unsave_job(self, user_id: uuid.UUID, job_id: uuid.UUID) -> bool:
        """
        Removes a saved job bookmark.
        """
        existing = await self.saved_job_repo.get_by_user_and_job(user_id, job_id)
        if not existing:
            return False
        return await self.saved_job_repo.delete(existing.id, soft=False)  # Hard delete bookmark association

    async def list_saved_jobs(
        self,
        user_id: uuid.UUID,
        folder: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SavedJob]:
        return await self.saved_job_repo.get_user_saved_jobs(
            user_id=user_id,
            folder=folder,
            skip=skip,
            limit=limit
        )


class SearchService:
    """
    Service layer powering search mechanics, logging histories, and saving query alerts.
    """
    def __init__(
        self,
        job_repo: JobRepository,
        saved_search_repo: SavedSearchRepository,
        search_history_repo: SearchHistoryRepository
    ) -> None:
        self.job_repo = job_repo
        self.saved_search_repo = saved_search_repo
        self.search_history_repo = search_history_repo

    async def execute_search(
        self,
        *,
        user_id: Optional[uuid.UUID] = None,
        keyword: Optional[str] = None,
        location: Optional[str] = None,
        employment_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        remote_status: Optional[str] = None,
        visa_sponsorship: Optional[bool] = None,
        min_salary: Optional[float] = None,
        skills: Optional[List[str]] = None,
        sort_by: str = "posted_at",
        sort_desc: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Job], int]:
        """
        Conducts advanced multi-field job searches and records user's history when authenticated.
        """
        items = await self.job_repo.search_jobs(
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
        total = await self.job_repo.count_search_results(
            keyword=keyword,
            location=location,
            employment_type=employment_type,
            experience_level=experience_level,
            remote_status=remote_status,
            visa_sponsorship=visa_sponsorship,
            min_salary=min_salary,
            skills=skills
        )

        # Audit track searches if user is authenticated and query has criteria
        if user_id and (keyword or location):
            try:
                filters = {}
                if employment_type: filters["employment_type"] = employment_type
                if experience_level: filters["experience_level"] = experience_level
                if remote_status: filters["remote_status"] = remote_status
                if visa_sponsorship is not None: filters["visa_sponsorship"] = visa_sponsorship
                if min_salary is not None: filters["min_salary"] = min_salary
                if skills: filters["skills"] = skills

                history_input = {
                    "user_id": user_id,
                    "query": keyword or f"Location: {location}",
                    "filters": filters
                }
                await self.search_history_repo.create(history_input, creator_id=str(user_id))
            except Exception as e:
                logger.warning(f"Failed to log search history: {str(e)}")

        return items, total

    # Saved Searches operations
    async def create_saved_search(self, user_id: uuid.UUID, search_in: SavedSearchCreate) -> SavedSearch:
        db_input = {
            "user_id": user_id,
            "name": search_in.name,
            "query_params": search_in.query_params,
            "notifications_enabled": search_in.notifications_enabled
        }
        return await self.saved_search_repo.create(db_input, creator_id=str(user_id))

    async def list_saved_searches(self, user_id: uuid.UUID) -> List[SavedSearch]:
        return await self.saved_search_repo.get_by_user_id(user_id)

    async def update_saved_search(
        self,
        user_id: uuid.UUID,
        search_id: uuid.UUID,
        search_in: SavedSearchUpdate
    ) -> Optional[SavedSearch]:
        db_obj = await self.saved_search_repo.get(search_id)
        if not db_obj or db_obj.user_id != user_id:
            return None
        return await self.saved_search_repo.update(db_obj=db_obj, obj_in=search_in, updater_id=str(user_id))

    async def delete_saved_search(self, user_id: uuid.UUID, search_id: uuid.UUID) -> bool:
        db_obj = await self.saved_search_repo.get(search_id)
        if not db_obj or db_obj.user_id != user_id:
            return False
        return await self.saved_search_repo.delete(search_id, soft=False)  # Hard delete saved search configurations

    # Search History operations
    async def get_search_history(self, user_id: uuid.UUID, limit: int = 20) -> List[SearchHistory]:
        return await self.search_history_repo.get_user_history(user_id, limit)


class ImportService:
    """
    Enterprise pluggable job feed integration service handling deduplication,
    validation, and mapping of multiple job ingestion sources (LinkedIn, Indeed, Greenhouse, etc.).
    """
    def __init__(self, job_service: JobService, job_repo: JobRepository) -> None:
        self.job_service = job_service
        self.job_repo = job_repo

    async def import_job_listing(self, source: str, raw_payload: Dict[str, Any]) -> Tuple[Job, bool]:
        """
        Validates, maps, and deduplicates an incoming job listing from a external source feed.
        Returns a Tuple: (Job object, True if newly created / False if updated).
        """
        source_id = str(raw_payload.get("id") or raw_payload.get("job_id") or "")
        if not source_id:
            raise ValueError("External job payload must contain a unique identifier ('id' or 'job_id').")

        # Map external source specific payloads into standard Job schema
        mapped_job_data = self._map_external_payload(source, source_id, raw_payload)
        
        # Deduplication check
        existing_job = await self.job_repo.get_by_source_id(source, source_id)
        if existing_job:
            # Update existing job
            update_payload = JobUpdate(**mapped_job_data)
            updated_job = await self.job_service.update_job(existing_job.id, update_payload)
            return updated_job, False
        else:
            # Create new job
            create_payload = JobCreate(**mapped_job_data)
            new_job = await self.job_service.create_job(create_payload)
            return new_job, True

    def _map_external_payload(self, source: str, source_id: str, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enterprise payload mapper mapping LinkedIn, Greenhouse, Lever, Workday formats to Job schema.
        """
        # Defaults
        title = raw.get("title") or raw.get("role_name") or "Untitled Position"
        company_name = raw.get("company") or raw.get("company_name") or "Unknown Company"
        location = raw.get("location") or raw.get("workplace") or "Remote/Global"
        employment_type = raw.get("employment_type") or raw.get("type") or "Full-time"
        remote_status = raw.get("remote_status") or raw.get("work_style") or "Onsite"
        description = raw.get("description") or raw.get("body") or "No description provided."
        
        # Parse currency & salary if available
        salary_min = float(raw.get("salary_min")) if raw.get("salary_min") is not None else None
        salary_max = float(raw.get("salary_max")) if raw.get("salary_max") is not None else None
        currency = raw.get("currency") or "USD"
        
        # Lists / arrays
        skills = raw.get("skills") or raw.get("required_skills") or []
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]
            
        benefits = raw.get("benefits") or raw.get("perks") or []
        if isinstance(benefits, str):
            benefits = [b.strip() for b in benefits.split(",") if b.strip()]

        # Expire tracking
        expires_at = None
        if raw.get("expires_at"):
            try:
                expires_at = datetime.fromisoformat(raw["expires_at"])
            except Exception:
                pass

        # Source normalization
        norm_source = source.lower()
        if norm_source == "linkedin":
            source_display = "LinkedIn"
        elif norm_source == "indeed":
            source_display = "Indeed"
        elif norm_source == "greenhouse":
            source_display = "Greenhouse"
        elif norm_source == "lever":
            source_display = "Lever"
        elif norm_source == "workday":
            source_display = "Workday"
        else:
            source_display = source.title()

        return {
            "title": title,
            "company_name": company_name,
            "location": location,
            "employment_type": employment_type,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "currency": currency,
            "experience_level": raw.get("experience_level") or "Mid-level",
            "remote_status": remote_status,
            "visa_sponsorship": bool(raw.get("visa_sponsorship", False)),
            "work_authorization": raw.get("work_authorization"),
            "expires_at": expires_at,
            "skills": skills,
            "benefits": benefits,
            "description": description,
            "url": raw.get("url") or raw.get("apply_url") or raw.get("link"),
            "source": source_display,
            "source_id": source_id
        }
