import uuid
import logging
import asyncio
import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.notification_repositories import NotificationRepository, NotificationPreferenceRepository
from app.models.notification import Notification, NotificationPreference
from app.schemas.notification import NotificationCreate, ReminderTriggerRequest, NotificationPreferenceUpdate

logger = logging.getLogger("app.services.notification")


class EmailService:
    """
    Handles compiling and sending beautiful, localized HTML/Plain-text emails with retry policies.
    """
    TEMPLATES = {
        "en": {
            "WELCOME": {
                "subject": "Welcome to JobCatalyst AI!",
                "plain": "Welcome, {name}! Your career journey starts here.",
                "html": "<h3>Welcome, {name}!</h3><p>Your career acceleration starts right now with JobCatalyst AI.</p>"
            },
            "INTERVIEW_REMINDER": {
                "subject": "Upcoming Mock Interview Reminder",
                "plain": "Hi {name}, you have a {interview_type} mock interview scheduled.",
                "html": "<h3>Hi {name},</h3><p>This is a reminder for your upcoming <strong>{interview_type}</strong> mock interview session.</p>"
            },
            "APPLICATION_FOLLOWUP": {
                "subject": "Follow-up Reminder: {role}",
                "plain": "It's time to check in on your application for {role} at {company}.",
                "html": "<h3>Application Status Check</h3><p>It has been a week since your submission to <strong>{company}</strong> for <strong>{role}</strong>. Let's send a friendly follow-up.</p>"
            },
            "RESUME_UPDATE": {
                "subject": "Resume Refresh Notice",
                "plain": "Keep your resume competitive by refreshing your target skills.",
                "html": "<h3>Optimize Your Resume</h3><p>Your resume has not been optimized recently. Update it against your targets to improve your ATS score.</p>"
            },
            "LEARNING": {
                "subject": "Coaching & Skills Goal Reminder",
                "plain": "Don't forget to complete your weekly goals on your career roadmap.",
                "html": "<h3>Weekly Goals Check-in</h3><p>Keep your momentum high! Visit the Career Coach module to check off your active goals.</p>"
            },
            "SUBSCRIPTION": {
                "subject": "Subscription Status Alert",
                "plain": "Your JobCatalyst AI subscription is up for renewal.",
                "html": "<h3>Subscription Renewal Alert</h3><p>Your subscription is active. Ensure payment methods are valid to avoid uninterrupted coaching access.</p>"
            }
        },
        "es": {
            "WELCOME": {
                "subject": "¡Bienvenido a JobCatalyst AI!",
                "plain": "¡Bienvenido, {name}! Su viaje profesional comienza aquí.",
                "html": "<h3>¡Bienvenido, {name}!</h3><p>Su aceleración profesional comienza ahora mismo con JobCatalyst AI.</p>"
            }
        }
    }

    def __init__(self) -> None:
        self.default_locale = "en"

    async def send_templated_email(
        self, 
        recipient_email: str, 
        template_key: str, 
        placeholders: Dict[str, Any], 
        locale: str = "en"
    ) -> bool:
        """
        Prepares localized content and schedules delivery. Implements basic exponential backoff retries.
        """
        lang = locale if locale in self.TEMPLATES else self.default_locale
        tmpl = self.TEMPLATES[lang].get(template_key, self.TEMPLATES[self.default_locale].get(template_key))
        
        if not tmpl:
            logger.error(f"Email template '{template_key}' not found.")
            return False

        subject = tmpl["subject"].format(**placeholders)
        plain_body = tmpl["plain"].format(**placeholders)
        html_body = tmpl["html"].format(**placeholders)

        logger.info(f"Preparing email delivery to {recipient_email}. Subject: '{subject}'")

        # Enterprise Retry Block
        max_retries = 3
        retry_delay = 1.0  # seconds
        
        for attempt in range(1, max_retries + 1):
            try:
                # Simulate real email dispatcher action (SMTP or Sendgrid integration mock)
                if "@fail" in recipient_email:
                    raise ConnectionError("SMTP server unresponsive.")
                
                logger.info(f"Email successfully delivered to {recipient_email} on attempt {attempt}")
                return True
            except Exception as exc:
                logger.warning(f"Email attempt {attempt} failed: {str(exc)}")
                if attempt == max_retries:
                    logger.error(f"Failed all {max_retries} email delivery attempts to {recipient_email}.")
                    return False
                await asyncio.sleep(retry_delay)
                retry_delay *= 2.0  # Exponential backoff

        return False


class NotificationService:
    """
    Orchestrates notifications, validating user preferences and quiet hours constraints before dispatching.
    """
    def __init__(
        self,
        notification_repo: NotificationRepository,
        pref_repo: NotificationPreferenceRepository,
        email_svc: EmailService,
        db_session: AsyncSession
    ) -> None:
        self.notification_repo = notification_repo
        self.pref_repo = pref_repo
        self.email_svc = email_svc
        self.db = db_session

    async def get_notifications_for_user(
        self, 
        user_id: uuid.UUID, 
        is_read: Optional[bool] = None, 
        limit: int = 50
    ) -> List[Notification]:
        return await self.notification_repo.get_by_user_id(user_id=user_id, is_read=is_read, limit=limit)

    async def mark_read(self, user_id: uuid.UUID, notification_ids: List[uuid.UUID]) -> int:
        return await self.notification_repo.mark_read_bulk(user_id=user_id, notification_ids=notification_ids)

    async def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        return await self.notification_repo.mark_all_read(user_id=user_id)

    async def delete_notification(self, user_id: uuid.UUID, notification_id: uuid.UUID) -> bool:
        return await self.notification_repo.delete_by_id_secure(user_id=user_id, notification_id=notification_id)

    async def get_preferences(self, user_id: uuid.UUID) -> NotificationPreference:
        return await self.pref_repo.get_or_create_preferences(user_id)

    async def update_preferences(self, user_id: uuid.UUID, payload: NotificationPreferenceUpdate) -> NotificationPreference:
        pref = await self.get_preferences(user_id)
        
        # Apply non-empty updates
        for field, value in payload.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(pref, field, value)

        await self.pref_repo.db.commit()
        return pref

    async def dispatch_notification(
        self, 
        user_id: uuid.UUID, 
        payload: NotificationCreate,
        user_email: Optional[str] = None,
        recipient_name: Optional[str] = None
    ) -> Notification:
        """
        Prepares and inserts notifications into durable storage, adhering strictly
        to user channel settings and quiet-hours intervals.
        """
        pref = await self.get_preferences(user_id)
        
        # 1. Topic subscription check
        topic_key = payload.notification_type.lower()
        is_subscribed = pref.topic_subscriptions.get(topic_key, True)

        # 2. Quiet Hours check
        is_quiet = False
        if pref.quiet_hours_enabled:
            # Check current time
            now_utc = datetime.datetime.utcnow().time()
            try:
                start_h, start_m = map(int, pref.quiet_hours_start.split(":"))
                end_h, end_m = map(int, pref.quiet_hours_end.split(":"))
                start_time = datetime.time(start_h, start_m)
                end_time = datetime.time(end_h, end_m)

                if start_time < end_time:
                    is_quiet = start_time <= now_utc <= end_time
                else:  # Overnights
                    is_quiet = now_utc >= start_time or now_utc <= end_time
            except Exception:
                logger.warning("Could not accurately parse quiet hours intervals. Bypassing check.")

        # Bypass quiet hours for Emergency priorities
        should_hold = is_quiet and not (payload.priority == "Emergency" and pref.allow_emergencies)

        delivery_records = {
            "in_app": "Sent" if pref.enable_in_app and is_subscribed else "Disabled",
            "email": "Pending" if pref.enable_email and is_subscribed else "Disabled",
            "sms": "Pending" if pref.enable_sms and is_subscribed else "Disabled",
            "push": "Pending" if pref.enable_push and is_subscribed else "Disabled",
            "webhook": "Pending" if pref.enable_webhook and is_subscribed else "Disabled"
        }

        # If quiet hours are active, hold non-emergency notifications
        if should_hold:
            for k in delivery_records.keys():
                if delivery_records[k] == "Pending":
                    delivery_records[k] = "Held (Quiet Hours)"

        # Prepare instance
        notif_data = {
            "user_id": user_id,
            "notification_type": payload.notification_type,
            "priority": payload.priority,
            "category": payload.category,
            "title": payload.title,
            "message": payload.message,
            "is_read": False,
            "channel_delivery_status": delivery_records,
            "context_data": payload.context_data
        }

        notif = await self.notification_repo.create(notif_data)
        await self.db.commit()

        # Trigger Out-of-band Channels if permitted immediately
        if not should_hold and is_subscribed:
            # Email delivery trigger
            if pref.enable_email and user_email:
                # Deduce corresponding template or fallback to general ALERT template
                tmpl_key = "WELCOME" if payload.notification_type == "System" and "welcome" in payload.title.lower() else "LEARNING"
                
                placeholders = {
                    "name": recipient_name or "Candidate",
                    "role": payload.context_data.get("role_title", "Target Role"),
                    "company": payload.context_data.get("company", "Employer"),
                    "interview_type": payload.context_data.get("interview_type", "Mock Session")
                }
                
                email_sent = await self.email_svc.send_templated_email(
                    recipient_email=user_email,
                    template_key=tmpl_key,
                    placeholders=placeholders
                )
                
                # Update status
                delivery_records["email"] = "Sent" if email_sent else "Failed"
                notif.channel_delivery_status = delivery_records
                await self.db.commit()

            # Webhook triggers (Mock Webhook dispatch)
            if pref.enable_webhook and pref.webhook_url:
                logger.info(f"Dispatching Webhook event to: {pref.webhook_url}")
                delivery_records["webhook"] = "Sent"
                notif.channel_delivery_status = delivery_records
                await self.db.commit()

        return notif


class ReminderService:
    """
    Automates generating reminder logs based on scheduling criteria.
    """
    def __init__(self, notif_svc: NotificationService) -> None:
        self.notif_svc = notif_svc

    async def trigger_manual_reminder(
        self, 
        user_id: uuid.UUID, 
        payload: ReminderTriggerRequest,
        user_email: Optional[str] = None,
        recipient_name: Optional[str] = None
    ) -> Notification:
        """
        Creates an actionable reminder, converting reminder_type into equivalent categories.
        """
        notif_type_map = {
            "Interview": "Interview",
            "Application": "Jobs",
            "Resume": "Resume",
            "Learning": "Career Coach",
            "Subscription": "Billing"
        }

        notification_payload = NotificationCreate(
            notification_type=notif_type_map.get(payload.reminder_type, "System"),
            priority="High",
            category="Reminder",
            title=payload.title,
            message=payload.message,
            context_data=payload.context_data
        )

        return await self.notif_svc.dispatch_notification(
            user_id=user_id,
            payload=notification_payload,
            user_email=user_email,
            recipient_name=recipient_name
        )
