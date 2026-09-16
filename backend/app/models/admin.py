import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import String, Boolean, JSON, Integer, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.base_models import DatabaseModelMixin


class AuditLog(Base, DatabaseModelMixin):
    """
    A persistent record of system-wide administrative interventions, 
    user mutations, AI pipeline activities, and security events.
    """
    __tablename__ = "audit_log"

    # The user performing the action, nullable if anonymous or system background worker
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    
    # Categories: Admin Action, User Action, AI Event, Security Event, System Event
    category: Mapped[str] = mapped_column(String(50), default="User Action", index=True, nullable=False)
    
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    context_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")


class SystemConfiguration(Base, DatabaseModelMixin):
    """
    Provides secure database-backed key-value configurations, categories
    like Application, Email, Storage, Redis, Database, and Environment settings.
    """
    __tablename__ = "system_configuration"

    config_key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    # Categories: Application, Email, Storage, Redis, Database, Environment
    category: Mapped[str] = mapped_column(String(50), default="Application", index=True, nullable=False)
    
    config_value: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class FeatureFlag(Base, DatabaseModelMixin):
    """
    Real-time application toggles to control localized rollout percentages,
    canary deployments, and simple toggles without restarting services.
    """
    __tablename__ = "feature_flag"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rollout_percentage: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)


class ResumeTemplate(Base, DatabaseModelMixin):
    """
    Stores structured resume layouts and LaTeX/JSON definitions 
    provided by the platform for resume generations.
    """
    __tablename__ = "resume_template"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="Professional", index=True, nullable=False)
    template_content: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class JobSource(Base, DatabaseModelMixin):
    """
    Monitors external pluggable job sources, crawler statuses, and synchronization intervals.
    """
    __tablename__ = "job_source"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    plugin_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    last_imported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Statuses: SUCCESS, FAILED, RUNNING, IDLE
    import_status: Mapped[str] = mapped_column(String(50), default="IDLE", nullable=False)
    import_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
