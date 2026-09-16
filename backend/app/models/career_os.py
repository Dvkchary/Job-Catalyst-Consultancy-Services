import uuid
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Integer, Boolean, Text, JSON, ForeignKey, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.base_class import Base
from app.db.base_models import DatabaseModelMixin


class AICareerAssistantSession(Base, DatabaseModelMixin):
    __tablename__ = "ai_career_assistant_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New Conversation")
    context_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    messages: Mapped[List["AICareerAssistantMessage"]] = relationship("AICareerAssistantMessage", back_populates="session", cascade="all, delete-orphan")


class AICareerAssistantMessage(Base, DatabaseModelMixin):
    __tablename__ = "ai_career_assistant_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ai_career_assistant_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False) # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    session: Mapped["AICareerAssistantSession"] = relationship("AICareerAssistantSession", back_populates="messages")


class CareerMemory(Base, DatabaseModelMixin):
    __tablename__ = "career_memories"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="general")
    confidence: Mapped[float] = mapped_column(Integer, nullable=False, default=100)
    source: Mapped[str] = mapped_column(String(255), nullable=True)


class CareerGoal(Base, DatabaseModelMixin):
    __tablename__ = "career_goals"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="in_progress") # pending, in_progress, achieved, abandoned
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    milestones: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)


class CareerHabit(Base, DatabaseModelMixin):
    __tablename__ = "career_habits"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    frequency: Mapped[str] = mapped_column(String(100), nullable=False) # daily, weekly
    streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_completed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class CareerTimelineEvent(Base, DatabaseModelMixin):
    __tablename__ = "career_timeline_events"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="milestone") # role_change, achievement, certification, project
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)


class CareerDocument(Base, DatabaseModelMixin):
    __tablename__ = "career_documents"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False) # resume, cover_letter, portfolio, certificate
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class AIWorkspaceProject(Base, DatabaseModelMixin):
    __tablename__ = "ai_workspace_projects"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    workspace_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
