import logging
import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_active_user, get_resume_service
from app.models.auth import User
from app.schemas.resume import ResumeContentSchema
from app.schemas.resume_analysis import ResumeQualityReport, SkillNormalizationResult
from app.services.resume import ResumeService
from app.services.resume_analysis import ResumeAnalysisService

logger = logging.getLogger("app.api.resume_analysis")

router = APIRouter(prefix="/resume-analysis", tags=["Resume Quality Foundation"])


@router.post("/analyze", response_model=ResumeQualityReport, status_code=status.HTTP_200_OK)
async def analyze_adhoc_resume(
    payload: ResumeContentSchema,
    current_user: User = Depends(get_current_active_user),
) -> ResumeQualityReport:
    """
    Analyzes an ad-hoc JSON resume structure passed in the body.
    Returns a comprehensive quality analysis report including health scores,
    chronological checks, duplicates, and spelling/formatting suggestions.
    """
    try:
        content_dict = payload.model_dump()
        return ResumeAnalysisService.analyze_resume_quality(content_dict)
    except Exception as e:
        logger.error(f"Ad-hoc analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to analyze resume data: {str(e)}"
        )


@router.get("/{resume_id}", response_model=ResumeQualityReport, status_code=status.HTTP_200_OK)
async def analyze_existing_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    resume_svc: ResumeService = Depends(get_resume_service),
) -> ResumeQualityReport:
    """
    Fetches an existing resume from the database by UUID, validates ownership,
    and returns its detailed quality and health analysis report.
    """
    resume = await resume_svc.get_by_id(resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found."
        )
    if resume.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resume."
        )

    # Ensure content exists
    content_dict = resume.content or {}
    return ResumeAnalysisService.analyze_resume_quality(content_dict, resume_id=resume.id)


from pydantic import BaseModel

class SkillNormalizeInput(BaseModel):
    skills: List[str]


@router.post("/skills/normalize", response_model=List[SkillNormalizationResult], status_code=status.HTTP_200_OK)
async def normalize_skills_list(
    payload: SkillNormalizeInput,
    current_user: User = Depends(get_current_active_user),
) -> List[SkillNormalizationResult]:
    """
    Reusable utility endpoint to normalize a list of raw, messy skill strings
    into their official professional industry standard spellings and casing.
    """
    results = []
    for s in payload.skills:
        s_clean = s.strip()
        s_lower = s_clean.lower()
        if s_lower in ResumeAnalysisService.SKILL_NORMALIZATION_MAP:
            normalized = ResumeAnalysisService.SKILL_NORMALIZATION_MAP[s_lower]
        else:
            normalized = s_clean
        results.append(SkillNormalizationResult(original=s_clean, normalized=normalized))
    return results
