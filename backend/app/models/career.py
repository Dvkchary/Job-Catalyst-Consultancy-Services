import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import ForeignKey, String, JSON, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.base_models import DatabaseModelMixin


class CareerProfile(Base, DatabaseModelMixin):
    """
    Enterprise Career Profile Entity tracking candidate's current career status,
    target roles, preferred countries, visa requirements, timeline, and composite scores.
    """
    __tablename__ = "career_profile"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False
    )

    current_role: Mapped[str] = mapped_column(String(100), nullable=False)
    target_role: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    experience_level: Mapped[str] = mapped_column(String(50), default="Mid", nullable=False)  # Junior, Mid, Senior, Lead, Executive
    
    # JSON arrays/lists
    skills: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    career_goals: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    preferred_countries: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    
    visa_status: Mapped[str] = mapped_column(String(100), default="Not Required", nullable=False)
    timeline: Mapped[str] = mapped_column(String(100), default="6 Months", nullable=False)  # Immediate, 3 Months, 6 Months, 1 Year
    
    career_score: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)

    # Granular Salary Intelligence (Current, Market, Expected, Negotiation Advice, Trends)
    salary_intelligence: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Readiness indicators (Promotion, Resume, Interview, Application Readiness metrics)
    readiness_insights: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="career_profile")


class CareerRoadmap(Base, DatabaseModelMixin):
    """
    Durable Short, Medium, and Long-Term Career Roadmap containing dynamic milestones,
    progress tracking metrics, and structured weekly/monthly goals.
    """
    __tablename__ = "career_roadmap"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    career_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("career_profile.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    # Chronological breakdown: short-term, medium-term, long-term roadmap elements and milestones
    roadmap_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    # Trackers for weekly/monthly goal completions
    weekly_goals: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    monthly_goals: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    # Detailed learning progress and resource completion indexes
    learning_progress: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="career_roadmaps")
    career_profile: Mapped["CareerProfile"] = relationship("CareerProfile", backref="roadmaps")


class CareerRecommendation(Base, DatabaseModelMixin):
    """
    Highly targeted AI recommendations capturing skill gaps, tailored learning resources
    (courses, certifications, books, projects, open-source), improvements, and next best actions.
    """
    __tablename__ = "career_recommendation"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    career_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("career_profile.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    # Dynamic structured recommendation mappings
    recommendations_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="career_recommendations")
    career_profile: Mapped["CareerProfile"] = relationship("CareerProfile", backref="recommendations")
