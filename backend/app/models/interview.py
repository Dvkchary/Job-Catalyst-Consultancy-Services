import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import ForeignKey, String, JSON, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.base_models import DatabaseModelMixin
from app.utils.datetime_utils import get_utc_now


class InterviewSession(Base, DatabaseModelMixin):
    """
    Enterprise Interview Session Entity tracking state, config, transcripts,
    and granular AI evaluations for a mock interview context.
    """
    __tablename__ = "interview_session"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("job.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resume.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    interview_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. Technical, Behavioral, HR, System Design
    difficulty: Mapped[str] = mapped_column(String(20), default="Medium", nullable=False)  # Easy, Medium, Hard
    duration: Mapped[int] = mapped_column(Integer, default=30, nullable=False)  # Duration in minutes
    status: Mapped[str] = mapped_column(String(20), default="Created", nullable=False)  # Created, In_Progress, Paused, Completed
    practice_mode: Mapped[str] = mapped_column(String(50), default="Quick Practice", nullable=False)  # Quick Practice, Full Mock, etc.
    
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Detailed transcripts storing history of questions, candidate answers, and feedback in real-time
    transcript: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    
    # AI Evaluation and metrics breakdown
    evaluation: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    # Actionable strengths, weaknesses, suggested answers, and learning resources
    feedback: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    current_question_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="interview_sessions")
    resume: Mapped["Resume"] = relationship("Resume", backref="interview_sessions")
    job: Mapped[Optional["Job"]] = relationship("Job", backref="interview_sessions")


class InterviewQuestion(Base, DatabaseModelMixin):
    """
    Predefined and dynamically generated Interview Question Bank.
    """
    __tablename__ = "interview_question"

    interview_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # Technical, Behavioral, etc.
    difficulty: Mapped[str] = mapped_column(String(20), default="Medium", index=True, nullable=False)  # Easy, Medium, Hard
    question_text: Mapped[str] = mapped_column(String, nullable=False)
    
    expected_topics: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    role_specific: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)  # e.g. "Software Engineer"
    company_specific: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)  # e.g. "Google", "Meta"
    
    is_system_template: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
