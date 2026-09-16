import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.db.career_os_repositories import (
    AICareerAssistantSessionRepository,
    AICareerAssistantMessageRepository,
    CareerMemoryRepository,
    CareerGoalRepository,
    CareerHabitRepository,
    CareerTimelineEventRepository,
    CareerDocumentRepository,
    AIWorkspaceProjectRepository
)
from app.schemas.career_os import (
    AICareerAssistantSessionCreate, AICareerAssistantMessageCreate,
    CareerMemoryCreate, CareerGoalCreate, CareerGoalUpdate, CareerHabitCreate,
    CareerTimelineEventCreate, CareerDocumentCreate, AIWorkspaceProjectCreate
)

class CareerOSService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_repo = AICareerAssistantSessionRepository(db)
        self.message_repo = AICareerAssistantMessageRepository(db)
        self.memory_repo = CareerMemoryRepository(db)
        self.goal_repo = CareerGoalRepository(db)
        self.habit_repo = CareerHabitRepository(db)
        self.timeline_repo = CareerTimelineEventRepository(db)
        self.document_repo = CareerDocumentRepository(db)
        self.workspace_repo = AIWorkspaceProjectRepository(db)

    # --- AI Assistant Sessions ---
    async def create_assistant_session(self, user_id: uuid.UUID, data: AICareerAssistantSessionCreate):
        return await self.session_repo.create(user_id=user_id, **data.model_dump())

    async def get_assistant_sessions(self, user_id: uuid.UUID):
        return await self.session_repo.get_by_user(user_id)

    async def get_assistant_session_with_messages(self, user_id: uuid.UUID, session_id: uuid.UUID):
        session = await self.session_repo.get_with_messages(session_id)
        if not session or session.user_id != user_id:
            raise HTTPException(status_code=404, detail="Session not found")
        return session

    async def add_assistant_message(self, user_id: uuid.UUID, session_id: uuid.UUID, data: AICareerAssistantMessageCreate):
        session = await self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise HTTPException(status_code=404, detail="Session not found")
        return await self.message_repo.create(session_id=session_id, **data.model_dump())

    # --- Career Memory ---
    async def get_memories(self, user_id: uuid.UUID):
        return await self.memory_repo.get_all_by_user(user_id)
        
    async def add_memory(self, user_id: uuid.UUID, data: CareerMemoryCreate):
        return await self.memory_repo.create(user_id=user_id, **data.model_dump())

    # --- Goals ---
    async def get_goals(self, user_id: uuid.UUID):
        return await self.goal_repo.get_all_by_user(user_id)
        
    async def create_goal(self, user_id: uuid.UUID, data: CareerGoalCreate):
        return await self.goal_repo.create(user_id=user_id, **data.model_dump())
        
    async def update_goal(self, user_id: uuid.UUID, goal_id: uuid.UUID, data: CareerGoalUpdate):
        goal = await self.goal_repo.get_by_id(goal_id)
        if not goal or goal.user_id != user_id:
            raise HTTPException(status_code=404, detail="Goal not found")
        return await self.goal_repo.update(db_obj=goal, obj_in=data.model_dump(exclude_unset=True))

    # --- Habits ---
    async def get_habits(self, user_id: uuid.UUID):
        return await self.habit_repo.get_all_by_user(user_id)
        
    async def create_habit(self, user_id: uuid.UUID, data: CareerHabitCreate):
        return await self.habit_repo.create(user_id=user_id, **data.model_dump())

    # --- Timeline ---
    async def get_timeline(self, user_id: uuid.UUID):
        return await self.timeline_repo.get_all_by_user(user_id)
        
    async def add_timeline_event(self, user_id: uuid.UUID, data: CareerTimelineEventCreate):
        return await self.timeline_repo.create(user_id=user_id, **data.model_dump())

    # --- Documents ---
    async def get_documents(self, user_id: uuid.UUID):
        return await self.document_repo.get_all_by_user(user_id)
        
    async def add_document(self, user_id: uuid.UUID, data: CareerDocumentCreate):
        return await self.document_repo.create(user_id=user_id, **data.model_dump())

    # --- AI Workspace ---
    async def get_workspaces(self, user_id: uuid.UUID):
        return await self.workspace_repo.get_all_by_user(user_id)
        
    async def create_workspace(self, user_id: uuid.UUID, data: AIWorkspaceProjectCreate):
        return await self.workspace_repo.create(user_id=user_id, **data.model_dump())
