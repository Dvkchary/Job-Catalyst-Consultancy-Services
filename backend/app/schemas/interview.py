import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CreateInterviewSessionRequest(BaseModel):
    resume_id: uuid.UUID = Field(..., description="The ID of the candidate's resume to ground the interview context.")
    job_id: Optional[uuid.UUID] = Field(None, description="Optional ID of the target job listing to customize questions.")
    interview_type: str = Field("Technical", description="Type of interview: Technical, Behavioral, HR, System Design, Coding, Case Study, Managerial, Custom.")
    difficulty: str = Field("Medium", description="Difficulty level: Easy, Medium, Hard.")
    practice_mode: str = Field("Quick Practice", description="Practice mode: Quick Practice, Full Mock Interview, Coding Interview, Behavioral Practice, Custom Interview.")
    duration: int = Field(30, description="Session duration in minutes.")


class SubmitAnswerRequest(BaseModel):
    answer_text: str = Field(..., description="The plain text answer typed or spoken by the candidate.")


class QuestionBankCreate(BaseModel):
    interview_type: str
    difficulty: str
    question_text: str
    expected_topics: List[str] = Field(default_factory=list)
    role_specific: Optional[str] = None
    company_specific: Optional[str] = None


class InterviewQuestionResponse(BaseModel):
    id: uuid.UUID
    interview_type: str
    difficulty: str
    question_text: str
    expected_topics: List[str]
    role_specific: Optional[str] = None
    company_specific: Optional[str] = None

    class Config:
        from_attributes = True


class MicroFeedback(BaseModel):
    score: float = Field(..., description="Instant score for this individual answer (1-100).")
    grammar_ok: bool = Field(..., description="True if no major grammatical/syntax errors were found.")
    feedback_notes: str = Field(..., description="Brief encouraging improvement feedback.")
    suggested_revision: str = Field(..., description="Refined, more impactful way to phrase this answer.")


class NextQuestionResponse(BaseModel):
    question_index: int = Field(..., description="Chronological step index.")
    next_question: Optional[str] = Field(None, description="The text of the next question, or None if the interview is complete.")
    micro_feedback: Optional[MicroFeedback] = Field(None, description="Real-time feedback on the last submitted answer.")
    is_finished: bool = Field(..., description="True if there are no more questions and the session is ready for final calculation.")


class EvaluationMetrics(BaseModel):
    communication: float = Field(..., description="Clarity, structure, and articulation rating (1-100).")
    technical_knowledge: float = Field(..., description="Subject matter correctness and domain expertise rating (1-100).")
    confidence: float = Field(..., description="Tone, pacing, and executive presence rating (1-100).")
    problem_solving: float = Field(..., description="Analytical methodology and algorithmic formulation rating (1-100).")
    behavior: float = Field(..., description="Alignment with standard STAR technique and leadership principles (1-100).")
    grammar: float = Field(..., description="Linguistic correctness and vocabulary variation rating (1-100).")
    professionalism: float = Field(..., description="Politeness, attitude, and posture/delivery rating (1-100).")
    overall_score: float = Field(..., description="Weighted average overall composite rating (1-100).")


class SuggestedAnswerMapping(BaseModel):
    question_text: str = Field(..., description="The interview question.")
    suggested_answer: str = Field(..., description="Industry-standard high-performing model answer.")


class AIFeedbackResponse(BaseModel):
    strengths: List[str] = Field(default_factory=list, description="Core candidate strengths validated by responses.")
    weaknesses: List[str] = Field(default_factory=list, description="Opportunities for growth or key content omissions.")
    suggested_answers: List[SuggestedAnswerMapping] = Field(default_factory=list, description="Model industry answers mapping.")
    improvement_tips: List[str] = Field(default_factory=list, description="Clear, highly actionable behavior/content adjustments.")
    learning_resources: List[str] = Field(default_factory=list, description="Recommended learning paths, modules, or articles.")


class TranscriptItem(BaseModel):
    question_text: str = Field(..., description="The question prompted by AI.")
    candidate_answer: Optional[str] = Field(None, description="The answer supplied by candidate.")
    score: Optional[float] = Field(None, description="Score computed for this individual exchange.")
    notes: Optional[str] = Field(None, description="Real-time evaluation comments.")


class InterviewSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    resume_id: uuid.UUID
    job_id: Optional[uuid.UUID] = None
    interview_type: str
    difficulty: str
    duration: int
    status: str
    practice_mode: str
    overall_score: Optional[float] = None
    transcript: List[TranscriptItem] = Field(default_factory=list)
    evaluation: Optional[EvaluationMetrics] = None
    feedback: Optional[AIFeedbackResponse] = None
    current_question_index: int
    created_at: Any
    updated_at: Any

    class Config:
        from_attributes = True


class InterviewHistoryItem(BaseModel):
    id: uuid.UUID = Field(..., description="The Session ID.")
    interview_type: str = Field(..., description="E.g., Technical.")
    difficulty: str = Field(..., description="Difficulty of the interview.")
    practice_mode: str = Field(..., description="Selected practice mode.")
    status: str = Field(..., description="Current state of the session.")
    overall_score: Optional[float] = Field(None, description="Composite final score.")
    created_at: Any = Field(..., description="Timestamp of the practice run.")


class InterviewHistoryTrend(BaseModel):
    attempts_count: int = Field(..., description="Total sessions attempted.")
    average_score: float = Field(..., description="Overall average of completed sessions.")
    improvement_trend: str = Field(..., description="Textual description of performance progression.")
    recent_attempts: List[InterviewHistoryItem] = Field(default_factory=list, description="Chronological record details.")
