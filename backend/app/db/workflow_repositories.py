import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.repository import BaseRepository
from app.models.workflow import Workflow, WorkflowExecution, WorkflowTemplate, WorkflowLog


class WorkflowRepository(BaseRepository[Workflow]):
    """
    Persistence layer for managing custom Workflow structures and trigger lookups.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=Workflow, db=db)

    async def get_by_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Workflow]:
        """Retrieves active workflows configured by a specific user."""
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.deleted_at.is_(None)
            )
        ).order_by(desc(self.model.created_at)).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_scheduled_workflows(self) -> List[Workflow]:
        """Retrieves all active workflows that are configured with a SCHEDULED trigger."""
        query = select(self.model).where(
            and_(
                self.model.is_active == True,
                self.model.status == "ACTIVE",
                self.model.trigger_type == "SCHEDULED",
                self.model.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_event_workflows(self, event_name: str) -> List[Workflow]:
        """Retrieves all active workflows configured to respond to an Event Driven trigger."""
        query = select(self.model).where(
            and_(
                self.model.is_active == True,
                self.model.status == "ACTIVE",
                self.model.trigger_type == "EVENT_DRIVEN",
                self.model.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        workflows = list(result.scalars().all())
        
        # Filter in-memory for exact event names matching the trigger config
        filtered = []
        for wf in workflows:
            if wf.trigger_config.get("event") == event_name:
                filtered.append(wf)
        return filtered


class WorkflowExecutionRepository(BaseRepository[WorkflowExecution]):
    """
    Persistence layer for tracking individual workflow execution instances and metrics.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=WorkflowExecution, db=db)

    async def get_by_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[WorkflowExecution]:
        """Retrieves execution histories for a specific user with eager workflow loading."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.user_id == user_id,
                    self.model.deleted_at.is_(None)
                )
            )
            .options(selectinload(self.model.workflow))
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_workflow(self, workflow_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[WorkflowExecution]:
        """Retrieves historical executions run under a specific workflow definition."""
        query = select(self.model).where(
            and_(
                self.model.workflow_id == workflow_id,
                self.model.deleted_at.is_(None)
            )
        ).order_by(desc(self.model.created_at)).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())


class WorkflowTemplateRepository(BaseRepository[WorkflowTemplate]):
    """
    Persistence layer for managing template definitions (System or Shared).
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=WorkflowTemplate, db=db)

    async def get_by_category(self, category: str) -> List[WorkflowTemplate]:
        """Retrieves template blueprints grouped by category (e.g. Resume, ATS)."""
        query = select(self.model).where(
            and_(
                self.model.category == category,
                self.model.deleted_at.is_(None)
            )
        ).order_by(self.model.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_system_templates(self) -> List[WorkflowTemplate]:
        """Retrieves all pre-bundled system template blueprints."""
        query = select(self.model).where(
            and_(
                self.model.is_system == True,
                self.model.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())


class WorkflowLogRepository(BaseRepository[WorkflowLog]):
    """
    Persistence layer for tracking real-time observability logs inside executions.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=WorkflowLog, db=db)

    async def get_by_execution(self, execution_id: uuid.UUID) -> List[WorkflowLog]:
        """Retrieves step log records sorted chronologically for diagnostics debugging."""
        query = select(self.model).where(
            and_(
                self.model.execution_id == execution_id,
                self.model.deleted_at.is_(None)
            )
        ).order_by(self.model.timestamp)
        result = await self.db.execute(query)
        return list(result.scalars().all())
