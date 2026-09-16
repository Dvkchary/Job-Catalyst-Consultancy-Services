import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =====================================================================
# NOTIFICATION PREFERENCE SCHEMAS
# =====================================================================

class NotificationPreferenceUpdate(BaseModel):
    enable_in_app: Optional[bool] = None
    enable_email: Optional[bool] = None
    enable_sms: Optional[bool] = None
    enable_push: Optional[bool] = None
    enable_webhook: Optional[bool] = None
    webhook_url: Optional[str] = None
    
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    timezone: Optional[str] = None
    
    frequency: Optional[str] = Field(None, description="Instant, Hourly, Daily, Weekly")
    digest_mode_enabled: Optional[bool] = None
    allow_emergencies: Optional[bool] = None
    topic_subscriptions: Optional[Dict[str, bool]] = None


class NotificationPreferenceResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    enable_in_app: bool
    enable_email: bool
    enable_sms: bool
    enable_push: bool
    enable_webhook: bool
    webhook_url: Optional[str]
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    timezone: str
    frequency: str
    digest_mode_enabled: bool
    allow_emergencies: bool
    topic_subscriptions: Dict[str, Any]
    created_at: Any
    updated_at: Any

    class Config:
        from_attributes = True


# =====================================================================
# NOTIFICATION ITEM SCHEMAS
# =====================================================================

class NotificationCreate(BaseModel):
    notification_type: str = Field(..., description="System, Resume, ATS, Jobs, Application, Interview, Career, Billing, Security, Admin")
    priority: str = Field("Medium", description="Low, Medium, High, Emergency")
    category: str = Field("Alert", description="Alert, Message, Reminder, Progress, System")
    title: str = Field(..., max_length=255)
    message: str = Field(..., max_length=1000)
    context_data: Dict[str, Any] = Field(default_factory=dict)


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    notification_type: str
    priority: str
    category: str
    title: str
    message: str
    is_read: bool
    read_at: Optional[datetime]
    channel_delivery_status: Dict[str, Any]
    context_data: Dict[str, Any]
    created_at: Any
    updated_at: Any

    class Config:
        from_attributes = True


class MarkReadRequest(BaseModel):
    notification_ids: List[uuid.UUID] = Field(..., description="List of notification UUIDs to change status.")


# =====================================================================
# REMINDER SCHEMAS
# =====================================================================

class ReminderTriggerRequest(BaseModel):
    reminder_type: str = Field(..., description="Interview, Application, Resume, Learning, Subscription")
    title: str = Field(..., max_length=255)
    message: str = Field(..., max_length=1000)
    target_date: Optional[datetime] = None
    context_data: Dict[str, Any] = Field(default_factory=dict)


class ReminderResponse(BaseModel):
    success: bool
    notification: Optional[NotificationResponse] = None
    queued_task_id: Optional[str] = None
    message: str
