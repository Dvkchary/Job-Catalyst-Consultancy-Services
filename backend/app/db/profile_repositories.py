import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import BaseRepository
from app.models.profile import AccountSettings, UserProfile


class UserProfileRepository(BaseRepository[UserProfile]):
    """
    Data-access repository for managing UserProfile entities,
    including querying, updating, and matching search queries.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=UserProfile, db=db)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[UserProfile]:
        """
        Retrieves a user profile by the associated User's UUID.
        """
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.deleted_at.is_(None) if hasattr(self.model, "deleted_at") else True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_or_none()

    async def search_profiles(
        self,
        *,
        skills: Optional[List[str]] = None,
        roles: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        limit: int = 20,
        skip: int = 0
    ) -> List[UserProfile]:
        """
        Searches user profiles by skills, preferred roles, and preferred locations.
        """
        query = select(self.model).where(
            self.model.deleted_at.is_(None) if hasattr(self.model, "deleted_at") else True
        )
        
        conditions = []
        # Since skills, preferred_roles, and preferred_job_locations are JSON,
        # we can perform queries to match them.
        # However, to be fully compatible with multiple backends (SQLite/PostgreSQL) during tests,
        # we can do robust condition filtering or Python-side post-filtering if database-specific structures fail,
        # but modern SQLAlchemy can generate JSON matches.
        # Let's write standard SQL-compatible queries using JSON cast/contain or standard string match for maximum portability.
        if skills:
            for skill in skills:
                # Standard string-like checks for maximum cross-compatibility across SQLite and Postgres
                conditions.append(self.model.skills.astext.contains(skill))
        
        if roles:
            for role in roles:
                conditions.append(self.model.preferred_roles.astext.contains(role))

        if locations:
            for loc in locations:
                conditions.append(self.model.preferred_job_locations.astext.contains(loc))

        if conditions:
            query = query.where(and_(*conditions))

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())


class AccountSettingsRepository(BaseRepository[AccountSettings]):
    """
    Data-access repository for managing AccountSettings entities,
    storing localized user preferences and visibility filters.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=AccountSettings, db=db)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[AccountSettings]:
        """
        Retrieves account settings by the associated User's UUID.
        """
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.deleted_at.is_(None) if hasattr(self.model, "deleted_at") else True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_or_none()
