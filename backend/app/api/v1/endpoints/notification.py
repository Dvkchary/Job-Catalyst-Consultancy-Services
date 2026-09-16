import logging
import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import (
    get_current_active_user,
    get_notification_service,
    get_reminder_service
)
from app.models.auth import User
from app.schemas.notification import (
    NotificationResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    MarkReadRequest,
    ReminderTriggerRequest,
    ReminderResponse
)
from app.services.notification import NotificationService, ReminderService

logger = logging.getLogger("app.api.notification")

router = APIRouter(prefix="/notification", tags=["Enterprise Communications & Alerts"])


@router.get("/list", response_model=List[NotificationResponse], status_code=status.HTTP_200_OK)
async def list_notifications(
    is_read: Optional[bool] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    notif_svc: NotificationService = Depends(get_notification_service)
) -> Any:
    """
    Retrieves a chronological list of user notifications, filtered optionally by read/unread status.
    """
    try:
        return await notif_svc.get_notifications_for_user(
            user_id=current_user.id, 
            is_read=is_read, 
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve communications inbox."
        )


@router.put("/read", response_model=Any, status_code=status.HTTP_200_OK)
async def mark_notifications_read(
    payload: MarkReadRequest,
    current_user: User = Depends(get_current_active_user),
    notif_svc: NotificationService = Depends(get_notification_service)
) -> Any:
    """
    Accepts a list of notification UUIDs and flags them as read.
    """
    try:
        count = await notif_svc.mark_read(user_id=current_user.id, notification_ids=payload.notification_ids)
        return {"success": True, "marked_count": count}
    except Exception as e:
        logger.error(f"Error marking notifications as read: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification read statuses."
        )


@router.put("/read/all", status_code=status.HTTP_200_OK)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    notif_svc: NotificationService = Depends(get_notification_service)
) -> Any:
    """
    Flags all unread notifications for the active user as read.
    """
    try:
        count = await notif_svc.mark_all_as_read(user_id=current_user.id)
        return {"success": True, "marked_count": count}
    except Exception as e:
        logger.error(f"Error bulk clearing notifications: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not clear all notification flags."
        )


@router.delete("/{notification_id}", status_code=status.HTTP_200_OK)
async def delete_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    notif_svc: NotificationService = Depends(get_notification_service)
) -> Any:
    """
    Removes an individual notification record securely.
    """
    try:
        success = await notif_svc.delete_notification(user_id=current_user.id, notification_id=notification_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or access denied."
            )
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification {notification_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification record."
        )


@router.get("/preferences", response_model=NotificationPreferenceResponse, status_code=status.HTTP_200_OK)
async def get_notification_preferences(
    current_user: User = Depends(get_current_active_user),
    notif_svc: NotificationService = Depends(get_notification_service)
) -> Any:
    """
    Retrieves the current configured channel toggles, quiet hours, and frequency subscriptions.
    """
    try:
        return await notif_svc.get_preferences(user_id=current_user.id)
    except Exception as e:
        logger.error(f"Error getting preferences: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load notification delivery parameters."
        )


@router.put("/preferences", response_model=NotificationPreferenceResponse, status_code=status.HTTP_200_OK)
async def update_notification_preferences(
    payload: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_active_user),
    notif_svc: NotificationService = Depends(get_notification_service)
) -> Any:
    """
    Saves candidate modifications to channels, quiet hours, and theme subscriptions.
    """
    try:
        return await notif_svc.update_preferences(user_id=current_user.id, payload=payload)
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply preference changes."
        )


@router.post("/reminder", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def trigger_reminder(
    payload: ReminderTriggerRequest,
    current_user: User = Depends(get_current_active_user),
    reminder_svc: ReminderService = Depends(get_reminder_service)
) -> Any:
    """
    Directly enqueues / dispatches an interactive reminder for interview prep,
    submitting follow-up forms, or learning targets.
    """
    try:
        notif = await reminder_svc.trigger_manual_reminder(
            user_id=current_user.id,
            payload=payload,
            user_email=current_user.email,
            recipient_name=current_user.username
        )
        return ReminderResponse(
            success=True,
            notification=notif,
            queued_task_id=f"task-{uuid.uuid4()}",
            message="Reminder queued and dispatched successfully."
        )
    except Exception as e:
        logger.error(f"Error triggering reminder: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not initiate dynamic reminder alert."
        )
