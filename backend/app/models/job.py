import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import ForeignKey, String, JSON, Boolean, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.base_models import DatabaseModelMixin
from app.utils.datetime_utils import get_utc_now


class Company(Base, DatabaseModelMixin):
    """
    Company Profile entity storing industrial sector, scale, ratings, and structural metadata.
    """
    __tablename__ = "company"

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "10-50", "1000+"
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    locations: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class Job(Base, DatabaseModelMixin):
    """
    Enterprise Job Entity representing an aggregated job listing from various job sources (LinkedIn, Indeed, etc.).
    """
    __tablename__ = "job"

    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("company.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    company_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    location: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    employment_type: Mapped[str] = mapped_column(String(50), default="Full-time", nullable=False)  # Full-time, Part-time, Contract, etc.
    salary_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    salary_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    experience_level: Mapped[str] = mapped_column(String(50), default="Mid-level", nullable=False)  # Entry, Mid-level, Senior, Executive
    remote_status: Mapped[str] = mapped_column(String(50), default="Onsite", nullable=False)  # Remote, Hybrid, Onsite
    visa_sponsorship: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    work_authorization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    skills: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    benefits: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # LinkedIn, Indeed, Glassdoor, etc.
    source_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)

    # Relationships
    company: Mapped[Optional[Company]] = relationship("Company", backref="jobs")


class SavedJob(Base, DatabaseModelMixin):
    """
    Bookmark mapping showing user saves, collections, and catalog folder organization.
    """
    __tablename__ = "saved_job"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    folder: Mapped[str] = mapped_column(String(100), default="Favorites", nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="saved_jobs")
    job: Mapped[Job] = relationship("Job")


class SavedSearch(Base, DatabaseModelMixin):
    """
    User search queries that are bookmarked for periodic reuse or alerts.
    """
    __tablename__ = "saved_search"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    query_params: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="saved_searches")


class SearchHistory(Base, DatabaseModelMixin):
    """
    User search log entries tracking query history chronological audit trail.
    """
    __tablename__ = "search_history"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    query: Mapped[str] = mapped_column(String(255), nullable=False)
    filters: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="search_history")
