import logging
import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import (
    get_current_active_user,
    get_matching_service,
)
from app.models.auth import User
from app.schemas.matching import (
    MatchResumeRequest,
    CompareResumeRequest,
    MatchingReportResponse,
    MatchHistoryItem,
    AIRecommendations
)
from app.services.matching import MatchingService

logger = logging.getLogger("app.api.matching")

router = APIRouter(prefix="/matching", tags=["AI Matching Engine"])


@router.post("/match", response_model=MatchingReportResponse, status_code=status.HTTP_200_OK)
async def match_resume(
    payload: MatchResumeRequest,
    current_user: User = Depends(get_current_active_user),
    matching_svc: MatchingService = Depends(get_matching_service),
) -> Any:
    """
    Evaluates a candidate's resume relative to a target job description or saved job listing.
    Calculates multidimensional scoring, skill gaps, and stores the results securely in the database.
    """
    try:
        return await matching_svc.match_resume_to_job(
            user_id=current_user.id,
            resume_id=payload.resume_id,
            job_id=payload.job_id,
            job_description=payload.job_description
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error matching resume: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while matching the resume.")


@router.post("/analyze", response_model=MatchingReportResponse, status_code=status.HTTP_200_OK)
async def analyze_job(
    resume_id: uuid.UUID = Query(..., description="The ID of the candidate's resume."),
    job_title: str = Query("Target Position", description="The title of the position to evaluate."),
    job_description: str = Query(..., description="The full plain text of the job description."),
    current_user: User = Depends(get_current_active_user),
    matching_svc: MatchingService = Depends(get_matching_service),
) -> Any:
    """
    Runs an on-the-fly requirements extraction, keyword scanning, and skill gap assessment
    between a candidate's resume and a raw job description string.
    """
    try:
        return await matching_svc.analyze_job_requirements(
            user_id=current_user.id,
            resume_id=resume_id,
            job_title=job_title,
            job_description=job_description
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error analyzing job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while analyzing the job.")


@router.post("/compare", status_code=status.HTTP_200_OK)
async def compare_resumes(
    payload: CompareResumeRequest,
    current_user: User = Depends(get_current_active_user),
    matching_svc: MatchingService = Depends(get_matching_service),
) -> Any:
    """
    Performs side-by-side comparative scoring, highlighting relative strengths and weaknesses,
    for two distinct resumes relative to a target job.
    """
    try:
        return await matching_svc.compare_two_resumes(
            user_id=current_user.id,
            resume_a_id=payload.resume_a_id,
            resume_b_id=payload.resume_b_id,
            job_id=payload.job_id,
            job_description=payload.job_description
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error comparing resumes: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while comparing the resumes.")


@router.get("/history", response_model=List[MatchHistoryItem], status_code=status.HTTP_200_OK)
async def list_match_history(
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    matching_svc: MatchingService = Depends(get_matching_service),
) -> Any:
    """
    Retrieves chronological list of past resume matching analyses performed by the user.
    """
    try:
        return await matching_svc.get_user_match_history(
            user_id=current_user.id,
            limit=limit,
            skip=skip
        )
    except Exception as e:
        logger.error(f"Error listing history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while fetching match history.")
