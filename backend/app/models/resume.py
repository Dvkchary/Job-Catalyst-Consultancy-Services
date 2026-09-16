import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import ForeignKey, String, JSON, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.base_models import DatabaseModelMixin


class ResumeTemplate(Base, DatabaseModelMixin):
    """
    Resume Template Entity representing pre-styled layouts for user resumes.
    Includes default template configurations, categories, and custom layouts.
    """
    __tablename__ = "resume_template"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="Standard", nullable=False)
    layout_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class Resume(Base, DatabaseModelMixin):
    """
    Core Resume Entity storing structured CV details, template associations,
    publishing language settings, and visibility levels.
    """
    __tablename__ = "resume"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="DRAFT", nullable=False)  # DRAFT, COMPLETED, ARCHIVED
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resume_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("resume_template.id", ondelete="SET NULL"),
        nullable=True
    )
    template_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    visibility: Mapped[str] = mapped_column(String(50), default="PRIVATE", nullable=False)  # PUBLIC, PRIVATE

    # Main Structured Content (Resume Builder fields packed inside JSON for cross-DB speed and dynamic sections support)
    # Fields: personal_info, education, experience, projects, skills, certifications, awards,
    # languages, volunteer, publications, references, custom_sections, section_ordering
    content: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="resumes")
    template: Mapped[Optional[ResumeTemplate]] = relationship("ResumeTemplate")
    versions: Mapped[List["ResumeVersion"]] = relationship(
        "ResumeVersion",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="ResumeVersion.version_number.desc()"
    )


class ResumeVersion(Base, DatabaseModelMixin):
    """
    Resume Version Snapshot Entity to track, restore, and compare complete historic iterations.
    """
    __tablename__ = "resume_version"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resume.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    content_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    metadata_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    resume: Mapped[Resume] = relationship("Resume", back_populates="versions")
