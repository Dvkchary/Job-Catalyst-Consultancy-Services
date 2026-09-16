import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import ForeignKey, String, JSON, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.base_models import DatabaseModelMixin


class Notification(Base, DatabaseModelMixin):
    """
    Durable representation of an individual communication or alert event,
    recording metadata, delivery priorities, status, and associated context payload.
    """
    __tablename__ = "notification"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Types: System, Resume, ATS, Jobs, Application, Interview, Career Coach, Billing, Security, Admin
    notification_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    
    # Priority: Low, Medium, High, Emergency
    priority: Mapped[str] = mapped_column(String(20), default="Medium", index=True, nullable=False)
    
    # Category: Alert, Message, Reminder, Progress, System
    category: Mapped[str] = mapped_column(String(50), default="Alert", index=True, nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Multi-channel delivery records (flags for tracking delivery states)
    channel_delivery_status: Mapped[Dict[str, Any]] = mapped_column(
        JSON, 
        default=lambda: {
            "in_app": "Sent",
            "email": "Pending",
            "sms": "Skipped",
            "push": "Skipped",
            "webhook": "Skipped"
        }, 
        nullable=False
    )

    context_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="notifications")


class NotificationPreference(Base, DatabaseModelMixin):
    """
    Candidate notification delivery preferences, specifying allowed channels,
    quiet hours intervals, message frequency bounds, digest groupings, and emergency overrides.
    """
    __tablename__ = "notification_preference"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        unique=True,
        nullable=False
    )

    # Channels
    enable_in_app: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_email: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_sms: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enable_push: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enable_webhook: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Quiet Hours Configuration
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quiet_hours_start: Mapped[Optional[str]] = mapped_column(String(5), default="22:00", nullable=True)  # HH:MM
    quiet_hours_end: Mapped[Optional[str]] = mapped_column(String(5), default="08:00", nullable=True)    # HH:MM
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)

    # Timing Settings
    frequency: Mapped[str] = mapped_column(String(20), default="Instant", nullable=False)  # Instant, Hourly, Daily, Weekly
    digest_mode_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_emergencies: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Topic Subscriptions JSON mapping
    # e.g., {"system": true, "billing": true, "interview_reminders": true}
    topic_subscriptions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="notification_preference")
