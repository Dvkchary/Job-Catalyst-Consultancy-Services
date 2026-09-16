import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import ForeignKey, String, JSON, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.base_models import DatabaseModelMixin


class DashboardWidget(Base, DatabaseModelMixin):
    """
    Durable configurations for dashboard widgets, supporting custom layout grids,
    drag-and-drop alignment parameters, visible states, and future plugin modules.
    """
    __tablename__ = "dashboard_widget"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    widget_key: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # e.g., 'resume_score_trend', 'application_funnel'
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Coordinates and dimensions for layout frameworks (grid systems)
    layout_x: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    layout_y: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    layout_w: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    layout_h: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    
    settings_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="dashboard_widgets")


class ExecutiveReport(Base, DatabaseModelMixin):
    """
    Stores generated analytical snapshots, weekly/monthly audits, and structural summaries
    compiled by JobCatalyst AI for candidate review and distribution exports.
    """
    __tablename__ = "executive_report"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    report_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # e.g. "Weekly", "Monthly", "Career", "Resume", "Application"
    
    # Chronological bounding intervals
    start_date: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Cached JSON metrics payload
    content_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    # Tracking file export downloads or offline indicators
    export_meta: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="executive_reports")
