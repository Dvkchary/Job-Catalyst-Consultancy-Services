import logging
import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status

from app.core.dependencies import (
    get_current_active_user,
    get_profile_service,
    get_settings_service,
    require_permission,
)
from app.models.auth import User
from app.schemas.profile import (
    AccountSettingsOut,
    AccountSettingsUpdate,
    AvatarActionResponse,
    ProfileCompletionStatus,
    ProfileSearchResponse,
    UserProfileCreate,
    UserProfileOut,
    UserProfileUpdate,
)
from app.services.profile import ProfileService
from app.services.settings import SettingsService
from app.services.validation import ValidationService

logger = logging.getLogger("app.api.profile")

router = APIRouter(prefix="/profile", tags=["User Profile & Preferences"])


@router.post("", response_model=UserProfileOut, status_code=status.HTTP_201_CREATED)
async def create_my_profile(
    payload: UserProfileCreate,
    current_user: User = Depends(get_current_active_user),
    profile_svc: ProfileService = Depends(get_profile_service),
) -> Any:
    """
    Initializes and registers a new UserProfile matching the authenticated user session.
    """
    try:
        profile = await profile_svc.create_profile(user_id=current_user.id, payload=payload)
        return profile
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("", response_model=UserProfileOut)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    profile_svc: ProfileService = Depends(get_profile_service),
) -> Any:
    """
    Retrieves the active profile associated with the current user account.
    """
    profile = await profile_svc.get_by_user_id(user_id=current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please create a profile first."
        )
    return profile


@router.put("", response_model=UserProfileOut)
async def update_my_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    profile_svc: ProfileService = Depends(get_profile_service),
) -> Any:
    """
    Partially modifies user profile details, validating nested entries (experience, dates, salary).
    """
    try:
        profile = await profile_svc.update_profile(user_id=current_user.id, payload=payload)
        return profile
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("", status_code=status.HTTP_200_OK)
async def delete_my_profile(
    current_user: User = Depends(get_current_active_user),
    profile_svc: ProfileService = Depends(get_profile_service),
) -> Any:
    """
    Soft-deletes and archives the current user's profile details.
    """
    success = await profile_svc.delete_profile(user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found or already archived.")
    return {"detail": "Successfully soft-deleted user profile profile."}


@router.get("/completion", response_model=ProfileCompletionStatus)
async def get_profile_completion_status(
    current_user: User = Depends(get_current_active_user),
    profile_svc: ProfileService = Depends(get_profile_service),
) -> Any:
    """
    Evaluates profile completeness score, lists unpopulated fields, and emits actionable tips.
    """
    return await profile_svc.get_completion_status(user_id=current_user.id)


@router.post("/avatar", response_model=AvatarActionResponse)
async def upload_avatar_image(
    file: UploadFile = File(...),
    crop_x: Optional[int] = Form(0),
    crop_y: Optional[int] = Form(0),
    crop_w: Optional[int] = Form(None),
    crop_h: Optional[int] = Form(None),
    current_user: User = Depends(get_current_active_user),
    profile_svc: ProfileService = Depends(get_profile_service),
) -> Any:
    """
    Validates avatar file type, extension, size, and double extensions.
    Mocks cropping and files storage, registering the updated URL path on the profile.
    """
    # 1. Read file context to obtain accurate size limits
    contents = await file.read()
    file_size = len(contents)
    
    # 2. Strict file check validation
    ok, error_msg = ValidationService.validate_avatar_file(
        filename=file.filename or "avatar.jpg",
        content_type=file.content_type or "image/jpeg",
        byte_size=file_size
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    # 3. Handle Mock Storage registration
    # In a production environment, this would upload to S3/GCS or crop using Pillow.
    # To ensure complete offline testability without crashing, we generate a persistent mock url path:
    avatar_uuid = uuid.uuid4()
    mock_avatar_url = f"https://cdn.jobcatalyst.ai/avatars/{current_user.id}/{avatar_uuid}.jpg"
    
    # Simulate cropping logs for enterprise auditing
    if crop_w and crop_h:
        logger.info(f"Cropped avatar to size {crop_w}x{crop_h} at offset ({crop_x}, {crop_y})")

    # Save to user profile
    try:
        await profile_svc.update_avatar_url(user_id=current_user.id, avatar_url=mock_avatar_url)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return AvatarActionResponse(
        avatar_url=mock_avatar_url,
        status="success"
    )


@router.delete("/avatar", status_code=status.HTTP_200_OK)
async def delete_avatar_image(
    current_user: User = Depends(get_current_active_user),
    profile_svc: ProfileService = Depends(get_profile_service),
) -> Any:
    """
    Removes active avatar path registrations from the profile.
    """
    try:
        await profile_svc.update_avatar_url(user_id=current_user.id, avatar_url=None)
        return {"detail": "Successfully deleted profile avatar image."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/settings", response_model=AccountSettingsOut)
async def get_my_settings(
    current_user: User = Depends(get_current_active_user),
    settings_svc: SettingsService = Depends(get_settings_service),
) -> Any:
    """
    Retrieves localizations and preferences for the current user.
    Lazy initializes defaults if none has been registered yet.
    """
    return await settings_svc.get_by_user_id(user_id=current_user.id)


@router.put("/settings", response_model=AccountSettingsOut)
async def update_my_settings(
    payload: AccountSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    settings_svc: SettingsService = Depends(get_settings_service),
) -> Any:
    """
    Modifies account preferences (notification matrices, UI theme, visibility).
    """
    return await settings_svc.update_settings(user_id=current_user.id, payload=payload)


@router.get("/search", response_model=ProfileSearchResponse)
async def search_profiles_directory(
    skills: Optional[List[str]] = Query(None, description="Skills collection"),
    roles: Optional[List[str]] = Query(None, description="Preferred job roles collection"),
    locations: Optional[List[str]] = Query(None, description="Preferred locations collection"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(require_permission("resumes:read")),
    profile_svc: ProfileService = Depends(get_profile_service),
) -> Any:
    """
    Recruitment discovery endpoint. Searches active user profiles.
    Protected under the 'resumes:read' RBAC authorization boundary.
    """
    results, count = await profile_svc.search_profiles(
        skills=skills,
        roles=roles,
        locations=locations,
        limit=limit,
        skip=skip
    )
    return ProfileSearchResponse(
        results=results,
        total_count=count,
        limit=limit,
        skip=skip
    )
