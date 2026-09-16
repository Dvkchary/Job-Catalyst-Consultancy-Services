import logging
import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import (
    get_current_active_user,
    get_interview_service,
)
from app.models.auth import User
from app.schemas.interview import (
    CreateInterviewSessionRequest,
    SubmitAnswerRequest,
    InterviewSessionResponse,
    NextQuestionResponse,
    InterviewHistoryItem,
    InterviewHistoryTrend
)
from app.services.interview import InterviewService

logger = logging.getLogger("app.api.interview")

router = APIRouter(prefix="/sessions", tags=["AI Interview Prep Platform"])


@router.post("", response_model=InterviewSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_interview_session(
    payload: CreateInterviewSessionRequest,
    current_user: User = Depends(get_current_active_user),
    interview_svc: InterviewService = Depends(get_interview_service)
) -> Any:
    """
    Initializes a structured mock interview session. Pulls company-aligned,
    role-specific questions dynamically using the AI engine.
    """
    try:
        return await interview_svc.create_session(
            user_id=current_user.id,
            resume_id=payload.resume_id,
            interview_type=payload.interview_type,
            difficulty=payload.difficulty,
            practice_mode=payload.practice_mode,
            duration=payload.duration,
            job_id=payload.job_id
        )
    except ValueError as e:
        logger.warning(f"Validation error creating session: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"System error creating interview session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected system error occurred while preparing the session."
        )


@router.post("/{session_id}/start", response_model=Dict[str, Any] if False else Any, status_code=status.HTTP_200_OK)
async def start_interview_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    interview_svc: InterviewService = Depends(get_interview_service)
) -> Any:
    """
    Starts an active mock interview session. Transitions the state to In_Progress and serves the first question.
    """
    try:
        session = await interview_svc.get_session(session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or unauthorized.")

        first_question = await interview_svc.start_interview_session(session_id)
        return {"question": first_question, "status": "In_Progress"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not activate session.")


@router.post("/{session_id}/next", response_model=NextQuestionResponse, status_code=status.HTTP_200_OK)
async def submit_answer(
    session_id: uuid.UUID,
    payload: SubmitAnswerRequest,
    current_user: User = Depends(get_current_active_user),
    interview_svc: InterviewService = Depends(get_interview_service)
) -> Any:
    """
    Submits the candidate's answer for the current step. Evaluates response quality in real-time,
    returns feedback, and progresses to the next question.
    """
    try:
        session = await interview_svc.get_session(session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or unauthorized.")

        return await interview_svc.submit_candidate_answer(
            session_id=session_id,
            answer_text=payload.answer_text
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing answer: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not process your response.")


@router.post("/{session_id}/finish", response_model=InterviewSessionResponse, status_code=status.HTTP_200_OK)
async def finish_interview(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    interview_svc: InterviewService = Depends(get_interview_service)
) -> Any:
    """
    Finalizes the practice run. Aggregates responses and compiles the multi-axis score,
    strengths, weaknesses, and professional training plan.
    """
    try:
        session = await interview_svc.get_session(session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or unauthorized.")

        return await interview_svc.finish_interview_session(session_id)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error finalizing interview session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not finalize session.")


@router.get("/history", response_model=List[InterviewHistoryItem], status_code=status.HTTP_200_OK)
async def list_history(
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    interview_svc: InterviewService = Depends(get_interview_service)
) -> Any:
    """
    Retrieves chronological log of past interview practice attempts.
    """
    try:
        return await interview_svc.get_user_history(
            user_id=current_user.id,
            limit=limit,
            skip=skip
        )
    except Exception as e:
        logger.error(f"Error listing practice history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not load history.")


@router.get("/trend", response_model=InterviewHistoryTrend, status_code=status.HTTP_200_OK)
async def get_history_trend(
    current_user: User = Depends(get_current_active_user),
    interview_svc: InterviewService = Depends(get_interview_service)
) -> Any:
    """
    Retrieves composite scoring trends, attempt metrics, and growth progression curves.
    """
    try:
        return await interview_svc.get_user_history_trend(user_id=current_user.id)
    except Exception as e:
        logger.error(f"Error getting performance trend: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve performance trends.")


@router.get("/{session_id}", response_model=InterviewSessionResponse, status_code=status.HTTP_200_OK)
async def get_session_details(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    interview_svc: InterviewService = Depends(get_interview_service)
) -> Any:
    """
    Fetches full records, dialogue logs, transcripts, and evaluation outputs for a specific session.
    """
    try:
        session = await interview_svc.get_session(session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or unauthorized.")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading session details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not load session.")
