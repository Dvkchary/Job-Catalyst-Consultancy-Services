import uuid
from typing import Any, Dict, Optional
from sqlalchemy import ForeignKey, String, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.base_models import DatabaseModelMixin


class ATSReport(Base, DatabaseModelMixin):
    """
    ATS Analysis Report Entity storing comparison results of a resume against a job description.
    """
    __tablename__ = "ats_report"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    resume_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resume.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    job_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    job_description: Mapped[str] = mapped_column(String, nullable=False)
    ats_score: Mapped[int] = mapped_column(Integer, nullable=False)

    # Detailed json payload storing keyword comparisons, formatting analysis, and improvements
    report_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="ats_reports")
    resume: Mapped["Resume"] = relationship("Resume", backref="ats_reports")
