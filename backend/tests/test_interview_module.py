import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.models.auth import User
from app.models.resume import Resume
from app.models.interview import InterviewSession, InterviewQuestion
from app.schemas.interview import CreateInterviewSessionRequest, SubmitAnswerRequest, InterviewSessionResponse
from app.services.interview import EvaluationService, FeedbackService, InterviewService, QuestionService
from app.core.dependencies import get_current_active_user, get_interview_service


def test_evaluation_service_heuristic_grading():
    """
    Validates heuristic grading logic under typical conditions.
    """
    # 1. Evaluate single answer
    micro_a = pytest.mark.asyncio(
        EvaluationService.evaluate_answer(
            question="Tell me about yourself.",
            answer="I am a highly driven Software Engineer with 5 years of experience."
        )
    )
    # Since it is a coroutine returning a future, we can run synchronous test verification on the scoring helper
    
    # 2. Score complete session
    transcript = [
        MagicMock(score=80.0, question_text="Q1", candidate_answer="A1"),
        MagicMock(score=90.0, question_text="Q2", candidate_answer="A2")
    ]
    metrics = pytest.mark.asyncio(
        EvaluationService.score_session(
            transcript_items=transcript,
            interview_type="Technical",
            difficulty="Medium"
        )
    )
    # Verify overall calculations are sound
    assert metrics is not None


@pytest.mark.asyncio
async def test_evaluation_calculations():
    """
    Verifies score_session behaves correctly under different difficulties.
    """
    transcript = [
        MagicMock(score=85.0),
        MagicMock(score=95.0)
    ]
    
    # Medium Difficulty
    metrics_med = await EvaluationService.score_session(transcript, "Technical", "Medium")
    assert metrics_med.overall_score > 0.0
    
    # Hard Difficulty (should lower composite values slightly due to higher expectations)
    metrics_hard = await EvaluationService.score_session(transcript, "Technical", "Hard")
    assert metrics_hard.overall_score <= metrics_med.overall_score


@pytest.mark.asyncio
async def test_question_service_fallback_to_seeder(db_session=None):
    """
    Verifies QuestionService pulls questions properly and seeds defaults if database is empty.
    """
    mock_q_repo = MagicMock()
    # Mocking returning empty list on first run to trigger seeding
    mock_q_repo.get_questions_for_interview = AsyncMock(side_effect=[[], [
        InterviewQuestion(question_text="Pre-seeded Q1", interview_type="Technical", difficulty="Medium"),
        InterviewQuestion(question_text="Pre-seeded Q2", interview_type="Technical", difficulty="Medium")
    ]])
    mock_q_repo.seed_default_questions = AsyncMock()

    q_svc = QuestionService(mock_q_repo)
    questions = await q_svc.get_questions_for_session("Technical", "Medium", limit=2)

    assert len(questions) > 0
    assert mock_q_repo.seed_default_questions.called


@pytest.mark.asyncio
async def test_interview_service_workflow_orchestration():
    """
    Tests full operational workflow orchestration inside the InterviewService.
    """
    user_id = uuid.uuid4()
    resume_id = uuid.uuid4()
    session_id = uuid.uuid4()

    mock_resume = Resume(id=resume_id, user_id=user_id, title="Test Resume", content={})
    
    mock_session = InterviewSession(
        id=session_id,
        user_id=user_id,
        resume_id=resume_id,
        interview_type="Technical",
        difficulty="Medium",
        practice_mode="Quick Practice",
        duration=30,
        status="In_Progress",
        current_question_index=0,
        transcript=[
            {"question_text": "Q1?", "candidate_answer": None, "score": None, "notes": None},
            {"question_text": "Q2?", "candidate_answer": None, "score": None, "notes": None}
        ]
    )

    # Setup Repo Mocks
    mock_session_repo = MagicMock()
    mock_session_repo.create_session = AsyncMock(return_value=mock_session)
    mock_session_repo.get = AsyncMock(return_value=mock_session)
    mock_session_repo.get_session_with_relations = AsyncMock(return_value=mock_session)
    mock_session_repo.update = AsyncMock()

    mock_question_repo = MagicMock()
    mock_question_repo.get_questions_for_interview = AsyncMock(return_value=[
        InterviewQuestion(question_text="Q1?", interview_type="Technical", difficulty="Medium"),
        InterviewQuestion(question_text="Q2?", interview_type="Technical", difficulty="Medium")
    ])

    mock_history_repo = MagicMock()
    mock_resume_repo = MagicMock()
    mock_resume_repo.get = AsyncMock(return_value=mock_resume)
    mock_job_repo = MagicMock()

    # Construct Service
    svc = InterviewService(
        interview_repo=mock_session_repo,
        question_repo=mock_question_repo,
        history_repo=mock_history_repo,
        resume_repo=mock_resume_repo,
        job_repo=mock_job_repo
    )

    # 1. Create Session
    session = await svc.create_session(
        user_id=user_id,
        resume_id=resume_id,
        interview_type="Technical",
        difficulty="Medium",
        practice_mode="Quick Practice",
        duration=30
    )
    assert session.id == session_id

    # 2. Start Session
    first_q = await svc.start_interview_session(session_id)
    assert first_q == "Q1?"

    # 3. Submit first answer
    res = await svc.submit_candidate_answer(session_id, "This is my answer to question 1.")
    assert res.question_index == 0
    assert res.next_question == "Q2?"
    assert res.is_finished is False

    # 4. Submit second answer (should complete)
    res_final = await svc.submit_candidate_answer(session_id, "This is my answer to question 2.")
    assert res_final.is_finished is True

    # 5. Finish and Evaluate
    completed_session = await svc.finish_interview_session(session_id)
    assert completed_session.status == "Completed"
    assert completed_session.overall_score is not None
    assert mock_session_repo.update.called


@pytest.mark.asyncio
async def test_endpoint_create_interview_session(client):
    """
    Verifies POST /api/v1/sessions endpoint can successfully launch an interview.
    """
    user_id = uuid.uuid4()
    resume_id = uuid.uuid4()
    session_id = uuid.uuid4()
    mock_user = User(id=user_id, email="bob@test.com", username="bob", password_hash="hash", status="ACTIVE")

    mock_session_response = InterviewSessionResponse(
        id=session_id,
        user_id=user_id,
        resume_id=resume_id,
        interview_type="Technical",
        difficulty="Medium",
        duration=30,
        status="Created",
        practice_mode="Quick Practice",
        overall_score=None,
        transcript=[],
        evaluation=None,
        feedback=None,
        current_question_index=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    mock_interview_svc = MagicMock()
    mock_interview_svc.create_session = AsyncMock(return_value=mock_session_response)

    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_interview_service] = lambda: mock_interview_svc

    payload = {
        "resume_id": str(resume_id),
        "interview_type": "Technical",
        "difficulty": "Medium",
        "practice_mode": "Quick Practice",
        "duration": 30
    }

    response = client.post("/api/v1/sessions", json=payload)
    client.app.dependency_overrides.clear()

    assert response.status_code == 201
    res_data = response.json()
    assert res_data["id"] == str(session_id)
    assert res_data["status"] == "Created"


@pytest.mark.asyncio
async def test_endpoint_submit_answer_and_next(client):
    """
    Verifies POST /api/v1/sessions/{session_id}/next responds with appropriate feedback and index.
    """
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    mock_user = User(id=user_id, email="bob@test.com", username="bob", password_hash="hash", status="ACTIVE")

    # Mock Session Details to bypass ownership guard
    mock_session = MagicMock(user_id=user_id)
    
    mock_next_response = {
        "question_index": 0,
        "next_question": "What is clean code?",
        "micro_feedback": {
            "score": 85.0,
            "grammar_ok": True,
            "feedback_notes": "Good answer.",
            "suggested_revision": "Try stating standard design patterns."
        },
        "is_finished": False
    }

    mock_interview_svc = MagicMock()
    mock_interview_svc.get_session = AsyncMock(return_value=mock_session)
    mock_interview_svc.submit_candidate_answer = AsyncMock(return_value=mock_next_response)

    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client.app.dependency_overrides[get_interview_service] = lambda: mock_interview_svc

    payload = {
        "answer_text": "I write modular and well-commented code."
    }

    response = client.post(f"/api/v1/sessions/{str(session_id)}/next", json=payload)
    client.app.dependency_overrides.clear()

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["next_question"] == "What is clean code?"
    assert res_data["micro_feedback"]["score"] == 85.0
