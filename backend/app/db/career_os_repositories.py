import uuid
from typing import List, Optional
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.repository import BaseRepository
from app.models.career_os import (
    AICareerAssistantSession, AICareerAssistantMessage, CareerMemory,
    CareerGoal, CareerHabit, CareerTimelineEvent, CareerDocument, AIWorkspaceProject
)

class AICareerAssistantSessionRepository(BaseRepository[AICareerAssistantSession]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=AICareerAssistantSession, db=db)
        
    async def get_by_user(self, user_id: uuid.UUID) -> List[AICareerAssistantSession]:
        query = select(self.model).where(
            and_(self.model.user_id == user_id, self.model.deleted_at.is_(None))
        ).order_by(desc(self.model.updated_at))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_with_messages(self, session_id: uuid.UUID) -> Optional[AICareerAssistantSession]:
        query = select(self.model).where(
            and_(self.model.id == session_id, self.model.deleted_at.is_(None))
        ).options(selectinload(self.model.messages))
        result = await self.db.execute(query)
        return result.scalar_or_none()

class AICareerAssistantMessageRepository(BaseRepository[AICareerAssistantMessage]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=AICareerAssistantMessage, db=db)

class CareerMemoryRepository(BaseRepository[CareerMemory]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=CareerMemory, db=db)
        
    async def get_all_by_user(self, user_id: uuid.UUID) -> List[CareerMemory]:
        query = select(self.model).where(
            and_(self.model.user_id == user_id, self.model.deleted_at.is_(None))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

class CareerGoalRepository(BaseRepository[CareerGoal]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=CareerGoal, db=db)
        
    async def get_all_by_user(self, user_id: uuid.UUID) -> List[CareerGoal]:
        query = select(self.model).where(
            and_(self.model.user_id == user_id, self.model.deleted_at.is_(None))
        ).order_by(desc(self.model.created_at))
        result = await self.db.execute(query)
        return list(result.scalars().all())

class CareerHabitRepository(BaseRepository[CareerHabit]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=CareerHabit, db=db)
        
    async def get_all_by_user(self, user_id: uuid.UUID) -> List[CareerHabit]:
        query = select(self.model).where(
            and_(self.model.user_id == user_id, self.model.deleted_at.is_(None))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

class CareerTimelineEventRepository(BaseRepository[CareerTimelineEvent]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=CareerTimelineEvent, db=db)
        
    async def get_all_by_user(self, user_id: uuid.UUID) -> List[CareerTimelineEvent]:
        query = select(self.model).where(
            and_(self.model.user_id == user_id, self.model.deleted_at.is_(None))
        ).order_by(desc(self.model.event_date))
        result = await self.db.execute(query)
        return list(result.scalars().all())

class CareerDocumentRepository(BaseRepository[CareerDocument]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=CareerDocument, db=db)
        
    async def get_all_by_user(self, user_id: uuid.UUID) -> List[CareerDocument]:
        query = select(self.model).where(
            and_(self.model.user_id == user_id, self.model.deleted_at.is_(None))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

class AIWorkspaceProjectRepository(BaseRepository[AIWorkspaceProject]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=AIWorkspaceProject, db=db)
        
    async def get_all_by_user(self, user_id: uuid.UUID) -> List[AIWorkspaceProject]:
        query = select(self.model).where(
            and_(self.model.user_id == user_id, self.model.deleted_at.is_(None))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
