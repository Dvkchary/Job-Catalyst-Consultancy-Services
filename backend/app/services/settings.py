import uuid
from typing import Any, Dict, Optional

from app.db.profile_repositories import AccountSettingsRepository
from app.models.profile import AccountSettings
from app.schemas.profile import AccountSettingsUpdate


class SettingsService:
    """
    User Preferences & Account Settings management service.
    Coordinates localizations, accessibility themes, notification channels,
    and account privacy states.
    """

    def __init__(self, settings_repo: AccountSettingsRepository) -> None:
        self.repo = settings_repo

    async def get_by_user_id(self, user_id: uuid.UUID) -> AccountSettings:
        """
        Retrieves the account settings associated with a user.
        If no settings record has been initialized, registers a default settings profile on the fly.
        """
        settings = await self.repo.get_by_user_id(user_id)
        if not settings:
            # Lazy initialize standard preferences to support a smooth onboarding flow
            default_payload = {
                "user_id": user_id,
                "theme": "light",
                "language": "en",
                "notification_preferences": {
                    "email_alerts": True,
                    "marketing_emails": False,
                    "push_notifications": True
                },
                "privacy_settings": {
                    "profile_visibility": "PUBLIC",
                    "search_index_allowed": True,
                    "anonymous_mode": False
                },
                "security_preferences": {
                    "mfa_required": False,
                    "session_timeout_minutes": 60
                }
            }
            settings = await self.repo.create(default_payload)
        return settings

    async def update_settings(self, user_id: uuid.UUID, payload: AccountSettingsUpdate) -> AccountSettings:
        """
        Mutates user configuration settings with validation checks.
        """
        settings = await self.get_by_user_id(user_id)

        # Build clean update dictionary mapping Pydantic model configurations
        update_data = payload.model_dump(exclude_unset=True)

        # Unpack nested structures into raw dictionaries for serialization
        for key in ["notification_preferences", "privacy_settings", "security_preferences"]:
            if key in update_data and update_data[key] is not None:
                if hasattr(update_data[key], "model_dump"):
                    update_data[key] = update_data[key].model_dump()

        return await self.repo.update(db_obj=settings, obj_in=update_data)
