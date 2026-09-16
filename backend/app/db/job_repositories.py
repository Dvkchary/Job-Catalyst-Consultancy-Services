import uuid
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from sqlalchemy import and_, select, desc, asc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import BaseRepository
from app.models.job import Company, Job, SavedJob, SavedSearch, SearchHistory


class CompanyRepository(BaseRepository[Company]):
    """
    Repository for managing Company entities.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=Company, db=db)

    async def get_by_name(self, name: str) -> Optional[Company]:
        """
        Retrieves a company profile by its case-insensitive name.
        """
        query = select(self.model).where(
            and_(
                func.lower(self.model.name) == name.lower(),
                self.model.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_or_none()


class JobRepository(BaseRepository[Job]):
    """
    Repository for managing Job entities, including advanced filtering, search, and pagination.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=Job, db=db)

    async def get_by_source_id(self, source: str, source_id: str) -> Optional[Job]:
        """
        Retrieves a job by its unique source identifier for deduplication during import.
        """
        query = select(self.model).where(
            and_(
                self.model.source == source,
                self.model.source_id == source_id,
                self.model.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_or_none()

    async def search_jobs(
        self,
        *,
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
    ) -> List[Job]:
        """
        Executes an advanced query with flexible text match and categorical filters.
        """
        query = select(self.model).where(self.model.deleted_at.is_(None))
        conditions = []

        if keyword:
            keyword_lower = f"%{keyword.lower()}%"
            conditions.append(
                or_(
                    func.lower(self.model.title).like(keyword_lower),
                    func.lower(self.model.description).like(keyword_lower),
                    func.lower(self.model.company_name).like(keyword_lower)
                )
            )

        if location:
            conditions.append(func.lower(self.model.location).like(f"%{location.lower()}%"))

        if employment_type:
            conditions.append(func.lower(self.model.employment_type) == employment_type.lower())

        if experience_level:
            conditions.append(func.lower(self.model.experience_level) == experience_level.lower())

        if remote_status:
            conditions.append(func.lower(self.model.remote_status) == remote_status.lower())

        if visa_sponsorship is not None:
            conditions.append(self.model.visa_sponsorship == visa_sponsorship)

        if min_salary is not None:
            conditions.append(
                or_(
                    self.model.salary_max >= min_salary,
                    self.model.salary_min >= min_salary
                )
            )

        if skills:
            # Check if any specified skills match items in the job's skills JSON array
            for skill in skills:
                conditions.append(
                    self.model.skills.contains([skill])
                )

        if conditions:
            query = query.where(and_(*conditions))

        # Ordering
        if hasattr(self.model, sort_by):
            sort_attr = getattr(self.model, sort_by)
            query = query.order_by(desc(sort_attr) if sort_desc else asc(sort_attr))
        else:
            query = query.order_by(desc(self.model.posted_at))

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_search_results(
        self,
        *,
        keyword: Optional[str] = None,
        location: Optional[str] = None,
        employment_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        remote_status: Optional[str] = None,
        visa_sponsorship: Optional[bool] = None,
        min_salary: Optional[float] = None,
        skills: Optional[List[str]] = None
    ) -> int:
        """
        Calculates total records matching search filters.
        """
        query = select(func.count()).select_from(self.model).where(self.model.deleted_at.is_(None))
        conditions = []

        if keyword:
            keyword_lower = f"%{keyword.lower()}%"
            conditions.append(
                or_(
                    func.lower(self.model.title).like(keyword_lower),
                    func.lower(self.model.description).like(keyword_lower),
                    func.lower(self.model.company_name).like(keyword_lower)
                )
            )

        if location:
            conditions.append(func.lower(self.model.location).like(f"%{location.lower()}%"))

        if employment_type:
            conditions.append(func.lower(self.model.employment_type) == employment_type.lower())

        if experience_level:
            conditions.append(func.lower(self.model.experience_level) == experience_level.lower())

        if remote_status:
            conditions.append(func.lower(self.model.remote_status) == remote_status.lower())

        if visa_sponsorship is not None:
            conditions.append(self.model.visa_sponsorship == visa_sponsorship)

        if min_salary is not None:
            conditions.append(
                or_(
                    self.model.salary_max >= min_salary,
                    self.model.salary_min >= min_salary
                )
            )

        if skills:
            for skill in skills:
                conditions.append(self.model.skills.contains([skill]))

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        return result.scalar() or 0


class SavedJobRepository(BaseRepository[SavedJob]):
    """
    Repository for managing SavedJob entities (bookmarks and folders).
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=SavedJob, db=db)

    async def get_by_user_and_job(self, user_id: uuid.UUID, job_id: uuid.UUID) -> Optional[SavedJob]:
        """
        Checks if a user has already saved a specific job.
        """
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.job_id == job_id,
                self.model.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_or_none()

    async def get_user_saved_jobs(
        self,
        user_id: uuid.UUID,
        folder: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SavedJob]:
        """
        Retrieves saved jobs for a specific user, optionally filtered by folder name.
        """
        conditions = [self.model.user_id == user_id, self.model.deleted_at.is_(None)]
        if folder:
            conditions.append(func.lower(self.model.folder) == folder.lower())

        query = select(self.model).where(and_(*conditions)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())


class SavedSearchRepository(BaseRepository[SavedSearch]):
    """
    Repository for managing SavedSearch queries.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=SavedSearch, db=db)

    async def get_by_user_id(self, user_id: uuid.UUID) -> List[SavedSearch]:
        """
        Gets all active saved searches for a specific user.
        """
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.deleted_at.is_(None)
            )
        ).order_by(desc(self.model.created_at))
        result = await self.db.execute(query)
        return list(result.scalars().all())


class SearchHistoryRepository(BaseRepository[SearchHistory]):
    """
    Repository for managing user search query history.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=SearchHistory, db=db)

    async def get_user_history(self, user_id: uuid.UUID, limit: int = 20) -> List[SearchHistory]:
        """
        Gets chronological search logs for a user.
        """
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.deleted_at.is_(None)
            )
        ).order_by(desc(self.model.timestamp)).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
