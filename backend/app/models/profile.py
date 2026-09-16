import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import ForeignKey, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.base_models import DatabaseModelMixin


class UserProfile(Base, DatabaseModelMixin):
    """
    User Profile Entity storing comprehensive resume data, social profiles,
    career target selections, and work visa details.
    """
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False
    )

    # Personal Information
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    headline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    # Professional Profiles (JSON Lists and Objects)
    skills: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    education: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    experience: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    certifications: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    social_links: Mapped[Dict[str, str]] = mapped_column(JSON, default=dict, nullable=False)

    # Preferred Targets & Criteria
    preferred_job_locations: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    preferred_roles: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    preferred_salary: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Work Authorization & Availability Details
    work_authorization: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    availability: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    timezone: Mapped[Optional[str]] = mapped_column(String(100), default="UTC", nullable=True)
    languages: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="profile")


class AccountSettings(Base, DatabaseModelMixin):
    """
    User Account Preferences storing accessibility, notification matrices,
    and granular visibility preferences.
    """
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False
    )

    theme: Mapped[str] = mapped_column(String(50), default="light", nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    
    # Nested configurations mapped inside JSON structures
    notification_preferences: Mapped[Dict[str, bool]] = mapped_column(JSON, default=dict, nullable=False)
    privacy_settings: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    security_preferences: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="settings")
