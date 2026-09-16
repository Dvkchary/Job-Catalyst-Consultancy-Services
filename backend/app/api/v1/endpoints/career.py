import logging
import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import (
    get_current_active_user,
    get_career_service,
    get_roadmap_service,
    get_recommendation_service,
    get_analytics_service
)
from app.models.auth import User
from app.schemas.career import (
    CareerProfileCreate,
    CareerProfileResponse,
    CareerRoadmapResponse,
    UpdateGoalsRequest,
    AIRecommendationsResponse,
    ProgressTrackingResponse
)
from app.services.career import (
    CareerService,
    RoadmapService,
    RecommendationService,
    AnalyticsService
)

logger = logging.getLogger("app.api.career")

router = APIRouter(prefix="/career", tags=["AI Career Coach"])


@router.get("/profile", response_model=CareerProfileResponse, status_code=status.HTTP_200_OK)
async def get_career_profile(
    current_user: User = Depends(get_current_active_user),
    career_svc: CareerService = Depends(get_career_service)
) -> Any:
    """
    Retrieves the active career profile for the authenticated user.
    """
    try:
        profile = await career_svc.get_profile(user_id=current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Career profile not found. Please initialize your career profile first."
            )
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading career profile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while loading your career profile."
        )


@router.post("/profile", response_model=CareerProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_profile(
    payload: CareerProfileCreate,
    current_user: User = Depends(get_current_active_user),
    career_svc: CareerService = Depends(get_career_service)
) -> Any:
    """
    Creates or updates the user's career profile. Automatically triggers market salary
    estimations and calculates current readiness intelligence scores.
    """
    try:
        return await career_svc.create_or_update_profile(user_id=current_user.id, data=payload)
    except Exception as e:
        logger.error(f"Error updating career profile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not register career profile details."
        )


@router.get("/roadmap", response_model=CareerRoadmapResponse, status_code=status.HTTP_200_OK)
async def get_career_roadmap(
    current_user: User = Depends(get_current_active_user),
    roadmap_svc: RoadmapService = Depends(get_roadmap_service)
) -> Any:
    """
    Fetches the current milestone roadmap of short, medium, and long-term targets.
    """
    try:
        roadmap = await roadmap_svc.get_latest_roadmap(user_id=current_user.id)
        if not roadmap:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Roadmap not found. Please initialize your career profile first."
            )
        return roadmap
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading career roadmap: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve career roadmap."
        )


@router.post("/roadmap/generate", response_model=CareerRoadmapResponse, status_code=status.HTTP_201_CREATED)
async def generate_career_roadmap(
    current_user: User = Depends(get_current_active_user),
    career_svc: CareerService = Depends(get_career_service),
    roadmap_svc: RoadmapService = Depends(get_roadmap_service)
) -> Any:
    """
    Force-regenerates a fresh career milestone roadmap based on the current active career profile.
    """
    try:
        profile = await career_svc.get_profile(user_id=current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No career profile found. Please create a career profile before generating a roadmap."
            )
        return await roadmap_svc.generate_roadmap(user_id=current_user.id, profile_id=profile.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating roadmap: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not compile career roadmap."
        )


@router.post("/roadmap/goals", response_model=CareerRoadmapResponse, status_code=status.HTTP_200_OK)
async def update_goals(
    payload: UpdateGoalsRequest,
    current_user: User = Depends(get_current_active_user),
    roadmap_svc: RoadmapService = Depends(get_roadmap_service)
) -> Any:
    """
    Updates weekly and monthly task completion checklists.
    """
    try:
        roadmap = await roadmap_svc.get_latest_roadmap(user_id=current_user.id)
        if not roadmap:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active career roadmap found."
            )
        
        # Parse list elements back into dictionaries
        weekly_dict = [g.model_dump() for g in payload.weekly_goals] if payload.weekly_goals is not None else None
        monthly_dict = [g.model_dump() for g in payload.monthly_goals] if payload.monthly_goals is not None else None

        updated = await roadmap_svc.update_active_goals(
            user_id=current_user.id,
            roadmap_id=roadmap.id,
            weekly=weekly_dict,
            monthly=monthly_dict
        )
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating goals: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update goal states."
        )


@router.get("/recommendations", response_model=AIRecommendationsResponse, status_code=status.HTTP_200_OK)
async def get_recommendations(
    current_user: User = Depends(get_current_active_user),
    rec_svc: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """
    Fetches the targeted AI recommendations covering skill gaps, courses, and job suggestions.
    """
    try:
        recs = await rec_svc.get_latest_recommendations(user_id=current_user.id)
        if not recs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendations not found. Please initialize your career profile first."
            )
        
        # Map dynamic json recommendations back to standard properties
        data = recs.recommendations_data
        return {
            "id": recs.id,
            "user_id": recs.user_id,
            "career_profile_id": recs.career_profile_id,
            "next_best_action": data.get("next_best_action", ""),
            "skill_gap_analysis": data.get("skill_gap_analysis", []),
            "learning_recommendations": data.get("learning_recommendations", {}),
            "resume_improvements": data.get("resume_improvements", []),
            "interview_practice_suggestions": data.get("interview_practice_suggestions", []),
            "job_recommendations": data.get("job_recommendations", []),
            "created_at": recs.created_at,
            "updated_at": recs.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recommendations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load recommendations."
        )


@router.post("/recommendations/generate", response_model=AIRecommendationsResponse, status_code=status.HTTP_201_CREATED)
async def generate_recommendations(
    current_user: User = Depends(get_current_active_user),
    career_svc: CareerService = Depends(get_career_service),
    rec_svc: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """
    Force-regenerates targeted AI skill gap comparisons and learning options based on active profile.
    """
    try:
        profile = await career_svc.get_profile(user_id=current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No career profile found. Please create a profile first."
            )
        
        recs = await rec_svc.generate_recommendations(user_id=current_user.id, profile_id=profile.id)
        data = recs.recommendations_data
        return {
            "id": recs.id,
            "user_id": recs.user_id,
            "career_profile_id": recs.career_profile_id,
            "next_best_action": data.get("next_best_action", ""),
            "skill_gap_analysis": data.get("skill_gap_analysis", []),
            "learning_recommendations": data.get("learning_recommendations", {}),
            "resume_improvements": data.get("resume_improvements", []),
            "interview_practice_suggestions": data.get("interview_practice_suggestions", []),
            "job_recommendations": data.get("job_recommendations", []),
            "created_at": recs.created_at,
            "updated_at": recs.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error compiling recommendations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not compile career coaching recommendations."
        )


@router.get("/progress", response_model=ProgressTrackingResponse, status_code=status.HTTP_200_OK)
async def get_progress(
    current_user: User = Depends(get_current_active_user),
    analytics_svc: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """
    Computes user progress analytics across ATS scans and mock interview attempts.
    """
    try:
        return await analytics_svc.get_progress_analytics(user_id=current_user.id)
    except Exception as e:
        logger.error(f"Error gathering progress stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve aggregate career metrics."
        )
