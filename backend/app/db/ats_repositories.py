import uuid
from typing import List, Optional
from sqlalchemy import and_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import BaseRepository
from app.models.ats import ATSReport


class ATSRepository(BaseRepository[ATSReport]):
    """
    Data-access repository for managing ATSReport entities,
    including querying, historical analysis retrieval, and matching reports.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=ATSReport, db=db)

    async def get_by_user_id(self, user_id: uuid.UUID) -> List[ATSReport]:
        """
        Retrieves all ATS reports associated with a user.
        """
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.deleted_at.is_(None) if hasattr(self.model, "deleted_at") else True
            )
        ).order_by(desc(self.model.created_at))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_resume_id(self, resume_id: uuid.UUID) -> List[ATSReport]:
        """
        Retrieves all ATS reports associated with a specific resume.
        Useful for building the improvement history of a resume over time.
        """
        query = select(self.model).where(
            and_(
                self.model.resume_id == resume_id,
                self.model.deleted_at.is_(None) if hasattr(self.model, "deleted_at") else True
            )
        ).order_by(desc(self.model.created_at))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_latest_report_for_resume(self, resume_id: uuid.UUID) -> Optional[ATSReport]:
        """
        Retrieves the most recent ATS report for a specific resume.
        """
        query = select(self.model).where(
            and_(
                self.model.resume_id == resume_id,
                self.model.deleted_at.is_(None) if hasattr(self.model, "deleted_at") else True
            )
        ).order_by(desc(self.model.created_at)).limit(1)
        result = await self.db.execute(query)
        return result.scalar_or_none()
