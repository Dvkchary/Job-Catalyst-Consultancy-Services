import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import ForeignKey, String, JSON, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.base_models import DatabaseModelMixin


class AIPromptTemplate(Base, DatabaseModelMixin):
    """
    Prompt library containing templates and metadata.
    """
    __tablename__ = "ai_prompt_template"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    versions: Mapped[List["AIPromptVersion"]] = relationship(
        "AIPromptVersion", back_populates="template", cascade="all, delete-orphan"
    )


class AIPromptVersion(Base, DatabaseModelMixin):
    """
    Versioned prompts containing individual templates and variable trackers.
    """
    __tablename__ = "ai_prompt_version"

    template_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ai_prompt_template.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    template_body: Mapped[str] = mapped_column(String, nullable=False)
    variables: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False) # e.g. ["resume_content", "job_description"]
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    template: Mapped[AIPromptTemplate] = relationship("AIPromptTemplate", back_populates="versions")


class AIConversation(Base, DatabaseModelMixin):
    """
    Stores an interactive session or context window with a particular LLM provider.
    """
    __tablename__ = "ai_conversation"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. "gemini", "openai", "claude"
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    messages: Mapped[List["AIConversationMessage"]] = relationship(
        "AIConversationMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="AIConversationMessage.sequence_number"
    )


class AIConversationMessage(Base, DatabaseModelMixin):
    """
    Individual message in an AI conversation, with token metrics and safety metadata.
    """
    __tablename__ = "ai_conversation_message"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ai_conversation.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False) # "system", "user", "assistant"
    content: Mapped[str] = mapped_column(String, nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # Cost & Token usage trackers
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Safety attributes
    sensitive_data_redacted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_content_backup: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    conversation: Mapped[AIConversation] = relationship("AIConversation", back_populates="messages")


class AITokenUsage(Base, DatabaseModelMixin):
    """
    Chronological journal tracking aggregate costs and token overhead daily/monthly.
    """
    __tablename__ = "ai_token_usage"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    provider: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    model_name: Mapped[String] = mapped_column(String(100), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    purpose: Mapped[str] = mapped_column(String(100), nullable=False) # e.g. "resume_refine", "ats_analysis"
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
