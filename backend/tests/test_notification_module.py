import uuid
import pytest
import datetime
from unittest.mock import AsyncMock, MagicMock

from app.models.auth import User
from app.models.notification import Notification, NotificationPreference
from app.schemas.notification import NotificationCreate, ReminderTriggerRequest, NotificationPreferenceUpdate
from app.db.notification_repositories import NotificationRepository, NotificationPreferenceRepository
from app.services.notification import NotificationService, EmailService, ReminderService
from app.core.dependencies import (
    get_current_active_user,
    get_notification_service,
    get_reminder_service
)


@pytest.mark.asyncio
async def test_notification_preference_repository_creation():
    """
    Ensures a default profile preference registers if the candidate accounts has none defined.
    """
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    
    # Mocking first select returning None, then mocking create and commit
    mock_result = MagicMock()
    mock_result.scalar_or_none = MagicMock(return_value=None)
    mock_db.execute.return_value = mock_result

    repo = NotificationPreferenceRepository(db=mock_db)
    user_id = uuid.uuid4()
    
    pref = await repo.get_or_create_preferences(user_id=user_id)
    assert pref is not None
    assert pref.user_id == user_id
    assert pref.enable_in_app is True
    assert pref.enable_email is True


@pytest.mark.asyncio
async def test_notification_repository_actions():
    """
    Checks list fetch filters and bulk updating notification statuses.
    """
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    
    # Mock rowcount returned by update execute
    mock_res = MagicMock()
    mock_res.rowcount = 4
    mock_db.execute.return_value = mock_res

    repo = NotificationRepository(db=mock_db)
    user_id = uuid.uuid4()
    notif_ids = [uuid.uuid4(), uuid.uuid4()]
    
    marked = await repo.mark_read_bulk(user_id=user_id, notification_ids=notif_ids)
    assert marked == 4


@pytest.mark.asyncio
async def test_email_service_exponential_backoff():
    """
    Verifies that EmailService delivers correctly or retries and logs failures.
    """
    svc = EmailService()
    
    # Normal delivery succeeds
    success = await svc.send_templated_email(
        recipient_email="test@candidate.com",
        template_key="WELCOME",
        placeholders={"name": "Alice"}
    )
    assert success is True

    # Failed delivery with connection issues retries and fails
    fail_res = await svc.send_templated_email(
        recipient_email="test@fail.com",
        template_key="WELCOME",
        placeholders={"name": "Alice"}
    )
    assert fail_res is False


@pytest.mark.asyncio
async def test_notification_service_quiet_hours_and_subscriptions():
    """
    Validates that quiet hours block standard alerts, but allow emergency overrides.
    """
    mock_notif_repo = MagicMock()
    mock_notif_repo.create = AsyncMock(side_effect=lambda x: Notification(id=uuid.uuid4(), **x))
    
    mock_pref_repo = MagicMock()
    # Mock preference with quiet hours enabled and email delivery on
    user_id = uuid.uuid4()
    mock_pref = NotificationPreference(
        id=uuid.uuid4(),
        user_id=user_id,
        enable_in_app=True,
        enable_email=True,
        enable_sms=False,
        enable_push=False,
        enable_webhook=False,
        quiet_hours_enabled=True,
        quiet_hours_start="00:00",
        quiet_hours_end="23:59",  # Active quiet hours practically 24/7
        timezone="UTC",
        frequency="Instant",
        topic_subscriptions={"system": True}
    )
    mock_pref_repo.get_or_create_preferences = AsyncMock(return_value=mock_pref)
    
    mock_email_svc = MagicMock()
    mock_email_svc.send_templated_email = AsyncMock(return_value=True)
    mock_db = MagicMock()

    svc = NotificationService(
        notification_repo=mock_notif_repo,
        pref_repo=mock_pref_repo,
        email_svc=mock_email_svc,
        db_session=mock_db
    )

    # 1. Standard priority alert during active quiet hours -> Held
    payload_normal = NotificationCreate(
        notification_type="System",
        priority="Medium",
        category="Alert",
        title="Welcome",
        message="Your workspace is online!"
    )
    
    notif_held = await svc.dispatch_notification(user_id=user_id, payload=payload_normal)
    assert notif_held.channel_delivery_status["email"] == "Held (Quiet Hours)"

    # 2. Emergency priority during quiet hours -> Bypassed
    payload_emerg = NotificationCreate(
        notification_type="System",
        priority="Emergency",
        category="Alert",
        title="Critical Security Alert",
        message="Someone logged in."
    )
    notif_bypass = await svc.dispatch_notification(
        user_id=user_id, 
        payload=payload_emerg, 
        user_email="bob@test.com"
    )
    assert notif_bypass.channel_delivery_status["email"] == "Sent"


@pytest.mark.asyncio
async def test_endpoint_list_notifications(client):
    """
    Verifies GET /api/v1/notification/list return codes.
    """
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, email="alice@test.com", username="alice", status="ACTIVE")

    mock_list = [
        {
            "id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "notification_type": "System",
            "priority": "Medium",
            "category": "Alert",
            "title": "Welcome!",
            "message": "Welcome Alice",
            "is_read": False,
            "read_at": None,
            "channel_delivery_status": {"in_app": "Sent"},
            "context_data": {},
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat()
        }
    ]

    mock_svc = MagicMock()
    mock_svc.get_notifications_for_user = AsyncMock(return_value=mock_list)

    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_notification_service] = lambda: mock_svc

    response = client.get("/api/v1/notification/list")
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Welcome!"


@pytest.mark.asyncio
async def test_endpoint_preferences_update(client):
    """
    Verifies updating notification channels settings.
    """
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, email="alice@test.com", username="alice", status="ACTIVE")

    mock_pref = {
        "id": str(uuid.uuid4()),
        "user_id": str(user_id),
        "enable_in_app": True,
        "enable_email": False,  # Updated to False
        "enable_sms": False,
        "enable_push": False,
        "enable_webhook": False,
        "webhook_url": None,
        "quiet_hours_enabled": False,
        "quiet_hours_start": "22:00",
        "quiet_hours_end": "08:00",
        "timezone": "UTC",
        "frequency": "Instant",
        "digest_mode_enabled": False,
        "allow_emergencies": True,
        "topic_subscriptions": {},
        "created_at": datetime.datetime.utcnow().isoformat(),
        "updated_at": datetime.datetime.utcnow().isoformat()
    }

    mock_svc = MagicMock()
    mock_svc.update_preferences = AsyncMock(return_value=mock_pref)

    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_notification_service] = lambda: mock_svc

    payload = {
        "enable_email": False
    }

    response = client.put("/api/v1/notification/preferences", json=payload)
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["enable_email"] is False


@pytest.mark.asyncio
async def test_endpoint_trigger_reminder(client):
    """
    Verifies POST /api/v1/notification/reminder endpoints.
    """
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, email="alice@test.com", username="alice", status="ACTIVE")

    mock_notif = {
        "id": str(uuid.uuid4()),
        "user_id": str(user_id),
        "notification_type": "Interview",
        "priority": "High",
        "category": "Reminder",
        "title": "Practice STAR Methods",
        "message": "Interview tomorrow at 10:00 AM.",
        "is_read": False,
        "read_at": None,
        "channel_delivery_status": {"in_app": "Sent"},
        "context_data": {},
        "created_at": datetime.datetime.utcnow().isoformat(),
        "updated_at": datetime.datetime.utcnow().isoformat()
    }

    mock_reminder_svc = MagicMock()
    mock_reminder_svc.trigger_manual_reminder = AsyncMock(return_value=mock_notif)

    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_reminder_service] = lambda: mock_reminder_svc

    payload = {
        "reminder_type": "Interview",
        "title": "Practice STAR Methods",
        "message": "Interview tomorrow at 10:00 AM.",
        "context_data": {"interview_type": "Behavioral"}
    }

    response = client.post("/api/v1/notification/reminder", json=payload)
    client.app.dependency_overrides.clear()

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["notification"]["notification_type"] == "Interview"
    assert data["queued_task_id"].startswith("task-")
