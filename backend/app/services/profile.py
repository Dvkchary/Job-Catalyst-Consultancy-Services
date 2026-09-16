import uuid
from typing import Any, Dict, List, Optional, Tuple

from app.db.profile_repositories import UserProfileRepository
from app.models.profile import UserProfile
from app.schemas.profile import UserProfileCreate, UserProfileUpdate
from app.services.completion import ProfileCompletionEngine, ProfileCompletionStatus
from app.services.validation import ValidationService


class ProfileService:
    """
    Unified Profile Management Service coordinating data mutations,
    nest schema validations, avatar actions, and profile search integrations.
    """

    def __init__(self, profile_repo: UserProfileRepository) -> None:
        self.repo = profile_repo

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[UserProfile]:
        """
        Retrieves a user profile by the associated user's ID.
        """
        return await self.repo.get_by_user_id(user_id)

    async def create_profile(self, user_id: uuid.UUID, payload: UserProfileCreate) -> UserProfile:
        """
        Initializes and registers a new UserProfile.
        Guarantees that a user cannot register duplicate profiles.
        """
        existing = await self.repo.get_by_user_id(user_id)
        if existing:
            raise ValueError("A profile already exists for this user account.")

        # Run model-level validational validations
        await self._validate_profile_payload(payload)

        # Build dictionary from input payload
        profile_data = payload.model_dump()
        profile_data["user_id"] = user_id

        # Insert record
        return await self.repo.create(profile_data)

    async def update_profile(self, user_id: uuid.UUID, payload: UserProfileUpdate) -> UserProfile:
        """
        Mutates an existing UserProfile with partial updates.
        Ensures strict business and formatting rules on modified components.
        """
        profile = await self.repo.get_by_user_id(user_id)
        if not profile:
            raise ValueError("Profile not found. Please create a profile first.")

        # Run validations on non-empty fields in the update payload
        await self._validate_profile_payload(payload)

        # Filter out unset/None fields to support partial updates
        update_data = payload.model_dump(exclude_unset=True)

        # Coerce custom schemas back to native dicts for JSON serialization
        for key in ["social_links", "preferred_salary", "work_authorization", "availability"]:
            if key in update_data and update_data[key] is not None:
                if hasattr(update_data[key], "model_dump"):
                    update_data[key] = update_data[key].model_dump()

        for key in ["education", "experience", "certifications", "languages"]:
            if key in update_data and update_data[key] is not None:
                update_data[key] = [
                    item.model_dump() if hasattr(item, "model_dump") else item 
                    for item in update_data[key]
                ]

        # Save updates
        return await self.repo.update(db_obj=profile, obj_in=update_data)

    async def delete_profile(self, user_id: uuid.UUID) -> bool:
        """
        Soft deletes user profile details.
        """
        profile = await self.repo.get_by_user_id(user_id)
        if not profile:
            return False
        return await self.repo.delete(profile.id, soft=True)

    async def get_completion_status(self, user_id: uuid.UUID) -> ProfileCompletionStatus:
        """
        Calculates and returns profile strength statistics and completion tips.
        """
        profile = await self.repo.get_by_user_id(user_id)
        if not profile:
            # Return zeroed out status if no profile has been initialized yet
            return ProfileCompletionStatus(
                completion_percentage=0,
                missing_fields=["profile"],
                recommendations=[
                    {
                        "section": "Profile",
                        "priority": "HIGH",
                        "tip": "Create your professional profile to begin discovering career matches."
                    }
                ]
            )
        return ProfileCompletionEngine.evaluate(profile)

    async def search_profiles(
        self,
        *,
        skills: Optional[List[str]] = None,
        roles: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        limit: int = 20,
        skip: int = 0
    ) -> Tuple[List[UserProfile], int]:
        """
        Queries and returns profiles matching filter criteria along with matching aggregates.
        """
        results = await self.repo.search_profiles(
            skills=skills,
            roles=roles,
            locations=locations,
            limit=limit,
            skip=skip
        )
        # Fetch matching aggregate count
        filters = {}
        total_count = await self.repo.count(filters=filters)
        return results, total_count

    async def update_avatar_url(self, user_id: uuid.UUID, avatar_url: Optional[str]) -> UserProfile:
        """
        Registers a direct URL path as the user's active profile picture avatar.
        Passing None/empty removes the profile avatar.
        """
        profile = await self.repo.get_by_user_id(user_id)
        if not profile:
            raise ValueError("Profile not found. Create a profile before attaching an avatar.")

        profile.avatar_url = avatar_url
        self.repo.db.add(profile)
        await self.repo.db.flush()
        return profile

    # ==============================================================================
    # Internal Validation Handlers
    # ==============================================================================

    async def _validate_profile_payload(self, payload: Any) -> None:
        """
        Internal business-rule checker to assert clean, coherent data fields.
        """
        # 1. Date Range Validations (Education)
        education_list = getattr(payload, "education", None)
        if education_list:
            for edu in education_list:
                ok, err = ValidationService.validate_date_range(edu.start_date, edu.end_date)
                if not ok:
                    raise ValueError(f"Education Validation: {err}")

        # 2. Date Range Validations (Experience)
        experience_list = getattr(payload, "experience", None)
        if experience_list:
            for exp in experience_list:
                ok, err = ValidationService.validate_date_range(exp.start_date, exp.end_date)
                if not ok:
                    raise ValueError(f"Experience Validation: {err}")

        # 3. Salary Constraints Validation
        salary = getattr(payload, "preferred_salary", None)
        if salary:
            ok, err = ValidationService.validate_salary_range(salary.min_salary, salary.max_salary)
            if not ok:
                raise ValueError(f"Salary Validation: {err}")

        # 4. Social Links Syntactical Verification
        socials = getattr(payload, "social_links", None)
        if socials:
            if socials.linkedin:
                ok, err = ValidationService.validate_social_url(socials.linkedin, "linkedin")
                if not ok:
                    raise ValueError(f"Social Links Validation: {err}")
            if socials.github:
                ok, err = ValidationService.validate_social_url(socials.github, "github")
                if not ok:
                    raise ValueError(f"Social Links Validation: {err}")
            if socials.portfolio:
                ok, err = ValidationService.validate_social_url(socials.portfolio, "portfolio")
                if not ok:
                    raise ValueError(f"Social Links Validation: {err}")
