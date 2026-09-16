import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, select, update, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import BaseRepository
from app.models.resume import Resume, ResumeTemplate, ResumeVersion


class ResumeRepository(BaseRepository[Resume]):
    """
    Data-access repository for managing Resume entities,
    including querying, setting primary resumes, and listings.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=Resume, db=db)

    async def get_by_user_id(self, user_id: uuid.UUID) -> List[Resume]:
        """
        Retrieves all active resumes associated with a user.
        """
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.deleted_at.is_(None)
            )
        ).order_by(desc(self.model.created_at))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_primary(self, user_id: uuid.UUID) -> Optional[Resume]:
        """
        Retrieves the primary active resume for a user, if any.
        """
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.is_primary.is_(True),
                self.model.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_or_none()

    async def set_primary(self, user_id: uuid.UUID, resume_id: uuid.UUID) -> Optional[Resume]:
        """
        Sets a specific resume as the user's primary resume.
        Automatically unsets all other resumes as primary.
        """
        # Unset others
        unset_query = (
            update(self.model)
            .where(
                and_(
                    self.model.user_id == user_id,
                    self.model.id != resume_id,
                    self.model.is_primary.is_(True)
                )
            )
            .values(is_primary=False)
        )
        await self.db.execute(unset_query)

        # Set new primary
        set_query = (
            update(self.model)
            .where(
                and_(
                    self.model.user_id == user_id,
                    self.model.id == resume_id
                )
            )
            .values(is_primary=True)
        )
        await self.db.execute(set_query)
        await self.db.flush()

        return await self.get(resume_id)


class ResumeTemplateRepository(BaseRepository[ResumeTemplate]):
    """
    Data-access repository for managing ResumeTemplate entities.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=ResumeTemplate, db=db)

    async def get_by_code(self, code: str) -> Optional[ResumeTemplate]:
        """
        Retrieves a resume template by its unique code string.
        """
        query = select(self.model).where(
            and_(
                self.model.code == code,
                self.model.deleted_at.is_(None) if hasattr(self.model, "deleted_at") else True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_or_none()


class ResumeVersionRepository(BaseRepository[ResumeVersion]):
    """
    Data-access repository for managing ResumeVersion entities.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=ResumeVersion, db=db)

    async def get_by_resume_id(self, resume_id: uuid.UUID) -> List[ResumeVersion]:
        """
        Retrieves all historic versions of a specific resume.
        """
        query = select(self.model).where(
            and_(
                self.model.resume_id == resume_id,
                self.model.deleted_at.is_(None) if hasattr(self.model, "deleted_at") else True
            )
        ).order_by(desc(self.model.version_number))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_version(self, resume_id: uuid.UUID, version_number: int) -> Optional[ResumeVersion]:
        """
        Retrieves a specific historic version of a resume by its version number.
        """
        query = select(self.model).where(
            and_(
                self.model.resume_id == resume_id,
                self.model.version_number == version_number,
                self.model.deleted_at.is_(None) if hasattr(self.model, "deleted_at") else True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_or_none()

    async def get_latest_version_number(self, resume_id: uuid.UUID) -> int:
        """
        Returns the highest version number recorded for a specific resume.
        """
        query = select(func.max(self.model.version_number)).where(
            self.model.resume_id == resume_id
        )
        result = await self.db.execute(query)
        return result.scalar() or 0
