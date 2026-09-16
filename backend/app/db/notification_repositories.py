import uuid
from typing import List, Optional
from sqlalchemy import select, and_, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import BaseRepository
from app.models.notification import Notification, NotificationPreference


class NotificationRepository(BaseRepository[Notification]):
    """
    Manages notifications persistence, querying, marking as read, and purging unneeded histories.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=Notification, db=db)

    async def get_by_user_id(
        self, 
        user_id: uuid.UUID, 
        is_read: Optional[bool] = None, 
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """
        Retrieves notifications for a specific user, optionally filtered by read/unread status.
        Sorted by creation time descending.
        """
        filters = [self.model.user_id == user_id]
        if is_read is not None:
            filters.append(self.model.is_read == is_read)
            
        if hasattr(self.model, "deleted_at"):
            filters.append(self.model.deleted_at.is_(None))

        query = select(self.model).where(and_(*filters)).order_by(
            desc(self.model.created_at)
        ).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_read_bulk(self, user_id: uuid.UUID, notification_ids: List[uuid.UUID]) -> int:
        """
        Bulk updates multiple notifications read statuses to True.
        """
        import datetime
        stmt = update(self.model).where(
            and_(
                self.model.id.in_(notification_ids),
                self.model.user_id == user_id
            )
        ).values(
            is_read=True,
            read_at=datetime.datetime.utcnow()
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        """
        Marks all unread notifications for a user as read.
        """
        import datetime
        stmt = update(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.is_read == False
            )
        ).values(
            is_read=True,
            read_at=datetime.datetime.utcnow()
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    async def delete_by_id_secure(self, user_id: uuid.UUID, notification_id: uuid.UUID) -> bool:
        """
        Securely deletes a notification owned by the target user.
        """
        stmt = delete(self.model).where(
            and_(
                self.model.id == notification_id,
                self.model.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0


class NotificationPreferenceRepository(BaseRepository[NotificationPreference]):
    """
    Manages user preferences for notification channels, times, frequencies, and subscriptions.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=NotificationPreference, db=db)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[NotificationPreference]:
        """
        Retrieves existing notification preferences.
        """
        query = select(self.model).where(self.model.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_or_none()

    async def get_or_create_preferences(self, user_id: uuid.UUID) -> NotificationPreference:
        """
        Gets existing notification preferences or populates a default set if none exist.
        """
        pref = await self.get_by_user_id(user_id)
        if pref:
            return pref

        default_topics = {
            "system": True,
            "resume": True,
            "ats": True,
            "jobs": True,
            "application": True,
            "interview": True,
            "career": True,
            "billing": True,
            "security": True,
            "admin": True
        }

        pref_data = {
            "user_id": user_id,
            "enable_in_app": True,
            "enable_email": True,
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
            "topic_subscriptions": default_topics
        }

        new_pref = await self.create(pref_data)
        await self.db.commit()
        return new_pref
