import uuid
from typing import List, Optional
from sqlalchemy import and_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import BaseRepository
from app.models.career import CareerProfile, CareerRoadmap, CareerRecommendation


class CareerRepository(BaseRepository[CareerProfile]):
    """
    Data-access repository for CareerProfile entities.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=CareerProfile, db=db)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[CareerProfile]:
        """
        Retrieves the unique active Career Profile for a user.
        """
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.deleted_at.is_(None) if hasattr(self.model, "deleted_at") else True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_or_none()


class RoadmapRepository(BaseRepository[CareerRoadmap]):
    """
    Data-access repository for CareerRoadmap entities.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=CareerRoadmap, db=db)

    async def get_by_user_id(self, user_id: uuid.UUID) -> List[CareerRoadmap]:
        """
        Retrieves all roadmaps created for a user.
        """
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.deleted_at.is_(None) if hasattr(self.model, "deleted_at") else True
            )
        ).order_by(desc(self.model.created_at))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_latest_by_user_id(self, user_id: uuid.UUID) -> Optional[CareerRoadmap]:
        """
        Retrieves the most recent roadmap created for a user.
        """
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.deleted_at.is_(None) if hasattr(self.model, "deleted_at") else True
            )
        ).order_by(desc(self.model.created_at)).limit(1)
        result = await self.db.execute(query)
        return result.scalar_or_none()


class RecommendationRepository(BaseRepository[CareerRecommendation]):
    """
    Data-access repository for CareerRecommendation entities.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=CareerRecommendation, db=db)

    async def get_latest_by_user_id(self, user_id: uuid.UUID) -> Optional[CareerRecommendation]:
        """
        Retrieves the most recent recommendations list created for a user.
        """
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.deleted_at.is_(None) if hasattr(self.model, "deleted_at") else True
            )
        ).order_by(desc(self.model.created_at)).limit(1)
        result = await self.db.execute(query)
        return result.scalar_or_none()
