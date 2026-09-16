import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import ForeignKey, String, JSON, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.base_models import DatabaseModelMixin


class Workflow(Base, DatabaseModelMixin):
    """
    SaaS Workflow definition, maintaining trigger configuration, 
    custom blocks structure (JSON DSL), and runtime active status.
    """
    __tablename__ = "workflow"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Trigger parameters: MANUAL, SCHEDULED, EVENT_DRIVEN, API, WEBHOOK
    trigger_type: Mapped[str] = mapped_column(String(50), default="MANUAL", index=True, nullable=False)
    
    # Store trigger-specific configurations: e.g. {"cron": "0 9 * * 1"} for SCHEDULED, {"event_name": "resume.uploaded"} for EVENT_DRIVEN
    trigger_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    # JSON definition of the DAG/Steps structure: e.g. [{"id": "step1", "type": "ai_call", "config": {...}}]
    definition: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    
    # DRAFT, ACTIVE, PAUSED
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", index=True, nullable=False)
    
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="workflows")
    executions: Mapped[List["WorkflowExecution"]] = relationship(
        "WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan"
    )


class WorkflowExecution(Base, DatabaseModelMixin):
    """
    Durable execution audit log tracker tracking state changes, progress indices,
    input contexts, step progress states, and execution status.
    """
    __tablename__ = "workflow_execution"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED, PAUSED
    status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True, nullable=False)
    
    # MANUAL, API, SCHEDULED, EVENT
    trigger_source: Mapped[str] = mapped_column(String(50), default="MANUAL", nullable=False)
    
    current_step_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Stores dynamic inputs and outputs passed across steps, e.g. {"resume_id": "...", "optimized_text": "..."}
    context_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    # Step by step progression state tracker: e.g. {"step_1": {"status": "COMPLETED", "output": {...}}}
    steps_state: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    error_message: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Relationships
    workflow: Mapped[Workflow] = relationship("Workflow", back_populates="executions")
    user: Mapped["User"] = relationship("User", backref="workflow_executions")
    logs: Mapped[List["WorkflowLog"]] = relationship(
        "WorkflowLog", back_populates="execution", cascade="all, delete-orphan"
    )


class WorkflowTemplate(Base, DatabaseModelMixin):
    """
    Pre-configured workflow templates for rapid user import and execution.
    Categories: Resume Optimization, ATS Analysis, Job Matching, Cover Letter Generation, etc.
    """
    __tablename__ = "workflow_template"

    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Resume, ATS, Jobs, Cover Letter, Prep, Career, Review
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    
    trigger_type: Mapped[str] = mapped_column(String(50), default="MANUAL", nullable=False)
    trigger_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    definition: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    is_system: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)


class WorkflowLog(Base, DatabaseModelMixin):
    """
    Sub-step logging capture to support observability and failure reports within Workflows.
    """
    __tablename__ = "workflow_log"

    execution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_execution.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    step_name: Mapped[str] = mapped_column(String(150), nullable=False)
    
    # INFO, WARNING, ERROR, SUCCESS
    level: Mapped[str] = mapped_column(String(20), default="INFO", nullable=False)
    
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    execution: Mapped[WorkflowExecution] = relationship("WorkflowExecution", back_populates="logs")
