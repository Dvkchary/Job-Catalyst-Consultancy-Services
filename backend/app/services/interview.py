import uuid
import logging
import json
import httpx
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.db.interview_repositories import InterviewRepository, QuestionRepository, HistoryRepository
from app.db.resume_repositories import ResumeRepository
from app.db.job_repositories import JobRepository
from app.models.interview import InterviewSession, InterviewQuestion
from app.schemas.interview import (
    InterviewSessionResponse,
    NextQuestionResponse,
    MicroFeedback,
    EvaluationMetrics,
    AIFeedbackResponse,
    SuggestedAnswerMapping,
    TranscriptItem,
    InterviewHistoryItem,
    InterviewHistoryTrend
)

logger = logging.getLogger("app.services.interview")


import hashlib
from app.core.cache_pool import fast_cache, HTTPClientProvider


class GeminiClient:
    """
    Lightweight, robust async Gemini API client that calls Google Generative Language endpoints
    via standard HTTP POST requests, handling failures and missing keys gracefully.
    """
    @classmethod
    async def generate_text(cls, prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("GEMINI_API_KEY is not configured. Falling back to rule-based engine.")
            return None

        # 1. High-Performance Response Cache lookup (hashing input parameters)
        param_hash = hashlib.sha256(f"{system_instruction or ''}:{prompt}".encode("utf-8")).hexdigest()
        cache_key = f"gemini:txt:{param_hash}"
        cached_res = await fast_cache.get(cache_key)
        if cached_res is not None:
            logger.info(f"AI Response Cache Hit! Skipping API request for key: {cache_key[:15]}...")
            return cached_res

        # Standard Endpoint for gemini-1.5-flash (or gemini-2.5-flash as available)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        contents = []
        if system_instruction:
            contents.append({
                "role": "user",
                "parts": [{"text": f"SYSTEM INSTRUCTION: {system_instruction}"}]
            })
            
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.95,
                "maxOutputTokens": 2048,
            }
        }

        try:
            # 2. Shared HTTP Connection Pool usage
            client = await HTTPClientProvider.get_client()
            response = await client.post(url, json=payload, timeout=25.0)
            if response.status_code == 200:
                res_json = response.json()
                text = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                
                # 3. Cache successful response for 1 hour to prevent redundant cost and API load
                await fast_cache.set(cache_key, text, ttl_seconds=3600)
                return text
            else:
                logger.error(f"Gemini API returned status {response.status_code}: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Failed to communicate with Gemini API: {str(e)}", exc_info=True)
            return None


class QuestionService:
    """
    Core Question Generator dynamically producing or selecting interview questions.
    """
    def __init__(self, question_repo: QuestionRepository) -> None:
        self.question_repo = question_repo

    async def get_questions_for_session(
        self,
        interview_type: str,
        difficulty: str,
        limit: int = 5,
        role: Optional[str] = None,
        company: Optional[str] = None
    ) -> List[str]:
        """
        Retrieves a collection of mock interview questions.
        Utilizes pre-seeded bank items or generates matching ones dynamically via Gemini.
        """
        # First query pre-seeded questions to establish context
        db_questions = await self.question_repo.get_questions_for_interview(
            interview_type=interview_type,
            difficulty=difficulty,
            limit=limit,
            role=role,
            company=company
        )

        questions_text = [q.question_text for q in db_questions]

        # Attempt to enrich with custom AI Questions if key is present
        ai_prompt = (
            f"Generate exactly {limit} professional and challenging mock interview questions for an interview with the following parameters:\n"
            f"- Type: {interview_type}\n"
            f"- Difficulty: {difficulty}\n"
            f"- Target Role: {role or 'Software Engineer'}\n"
            f"- Target Company: {company or 'Tech Company'}\n\n"
            f"Respond with a plain JSON list of strings only, containing the questions, like: "
            f'["Question 1?", "Question 2?"]. Do not output markdown, formatting, or extra text.'
        )
        
        ai_response = await GeminiClient.generate_text(prompt=ai_prompt)
        if ai_response:
            try:
                # Clean up any potential json codeblock markers
                cleaned = ai_response.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                parsed = json.loads(cleaned)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed[:limit]
            except Exception as e:
                logger.warning(f"Could not parse AI-generated questions JSON: {str(e)}. Falling back to local bank.")

        # Default back to DB seeded items
        return questions_text[:limit]


class EvaluationService:
    """
    Evaluator performing answer evaluation (micro-feedback) and complete session scoring.
    """
    @classmethod
    async def evaluate_answer(
        cls,
        question: str,
        answer: str
    ) -> MicroFeedback:
        """
        Runs real-time feedback and grammatical validation on a submitted candidate answer.
        """
        # Fallback heuristic evaluations
        ans_len = len(answer) if answer else 0
        score = 50.0
        grammar_ok = True
        feedback_notes = "Excellent participation. Consider expanding on your hands-on achievements and direct involvement using metrics."
        suggested_revision = "To deliver a higher-performing answer, frame your experience using the STAR technique (Situation, Task, Action, Result)."

        # Simple heuristic analyzer
        if ans_len > 250:
            score += 20.0
        elif ans_len > 100:
            score += 10.0
        else:
            score -= 10.0

        # Check for simple structural keywords (STAR method)
        star_count = 0
        for kw in ["situation", "task", "action", "result", "metric", "spearheaded", "optimized", "team", "challenge"]:
            if kw in answer.lower():
                star_count += 1
        score = min(100.0, score + (star_count * 3.0))

        # Check grammar patterns
        if len(answer.split()) < 5:
            grammar_ok = False
            feedback_notes = "Answer is too brief to evaluate. Provide details on how you solved the problem."

        # Attempt dynamic evaluation via Gemini
        ai_prompt = (
            f"Evaluate the following candidate response in a professional mock interview:\n"
            f"Question: {question}\n"
            f"Candidate Answer: {answer}\n\n"
            f"Provide your evaluation in a plain JSON format with the following keys:\n"
            f'- "score": (number between 0 and 100)\n'
            f'- "grammar_ok": (boolean, whether the grammar is mostly correct and professional)\n'
            f'- "feedback_notes": (brief feedback highlighting what was good and how to improve)\n'
            f'- "suggested_revision": (a high-quality revision demonstrating a strong, professional way to express the answer)\n\n'
            f"Output plain JSON only without any markdown tags."
        )

        ai_res = await GeminiClient.generate_text(prompt=ai_prompt)
        if ai_res:
            try:
                cleaned = ai_res.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                parsed = json.loads(cleaned)
                return MicroFeedback(
                    score=float(parsed.get("score", score)),
                    grammar_ok=bool(parsed.get("grammar_ok", grammar_ok)),
                    feedback_notes=str(parsed.get("feedback_notes", feedback_notes)),
                    suggested_revision=str(parsed.get("suggested_revision", suggested_revision))
                )
            except Exception as e:
                logger.warning(f"Failed parsing micro-feedback JSON: {str(e)}")

        return MicroFeedback(
            score=round(score, 1),
            grammar_ok=grammar_ok,
            feedback_notes=feedback_notes,
            suggested_revision=suggested_revision
        )

    @classmethod
    async def score_session(
        cls,
        transcript_items: List[TranscriptItem],
        interview_type: str,
        difficulty: str
    ) -> EvaluationMetrics:
        """
        Compiles aggregate scores along individual multi-axis evaluation categories.
        """
        # Average candidate answer score from individual items
        valid_scores = [item.score for item in transcript_items if item.score is not None]
        base_score = sum(valid_scores) / len(valid_scores) if valid_scores else 70.0

        # Custom variations based on parameters
        diff_factor = {"Easy": 5.0, "Medium": 0.0, "Hard": -5.0}.get(difficulty, 0.0)
        
        # Calculate subscores
        communication = min(100.0, max(1.0, base_score + 3.0 + diff_factor))
        technical = min(100.0, max(1.0, base_score - 1.0 + diff_factor))
        confidence = min(100.0, max(1.0, base_score + 2.0 + diff_factor))
        problem_solving = min(100.0, max(1.0, base_score + diff_factor))
        behavior = min(100.0, max(1.0, base_score + 1.0 + diff_factor))
        grammar = min(100.0, max(1.0, base_score + 4.0))
        professionalism = min(100.0, max(1.0, base_score + 5.0))

        overall_score = (
            (communication * 0.15) +
            (technical * 0.25) +
            (confidence * 0.10) +
            (problem_solving * 0.20) +
            (behavior * 0.15) +
            (grammar * 0.05) +
            (professionalism * 0.10)
        )

        return EvaluationMetrics(
            communication=round(communication, 1),
            technical_knowledge=round(technical, 1),
            confidence=round(confidence, 1),
            problem_solving=round(problem_solving, 1),
            behavior=round(behavior, 1),
            grammar=round(grammar, 1),
            professionalism=round(professionalism, 1),
            overall_score=round(overall_score, 1)
        )


class FeedbackService:
    """
    Service generating detailed feedback, model answers, and training action plans.
    """
    @classmethod
    async def generate_feedback(
        cls,
        transcript_items: List[TranscriptItem],
        metrics: EvaluationMetrics,
        interview_type: str
    ) -> AIFeedbackResponse:
        """
        Compiles detailed feedback containing strengths, weaknesses, model answers, and growth plans.
        """
        # Formulate Suggested Answers mappings
        suggested_answers = []
        for item in transcript_items:
            suggested_answers.append(
                SuggestedAnswerMapping(
                    question_text=item.question_text,
                    suggested_answer=f"To answer '{item.question_text}' effectively, focus on stating a clear, quantifiable challenge you overcame. E.g., 'At my prior role, I redesigned our service layer, resulting in a 35% speed improvement.'"
                )
            )

        # Standard heuristics
        strengths = [
            "Demonstrated clear technical articulation in describing concurrency and data scaling structures.",
            "Utilized active industry action verbs and maintained a high level of professional composure throughout."
        ]
        weaknesses = [
            "Could expand more on individual system metrics or specific design decisions.",
            "Answers sometimes drift into high-level definitions instead of detailing exact, practical contributions."
        ]
        improvement_tips = [
            "Use the STAR Method: Structure every situational answer strictly using Situation, Task, Action, and Result.",
            "Quantify Your Impact: Highlight key operational results such as percentages, dollars, or headcount saved.",
            "Be Concise: Limit answers to between 2 and 3 minutes to maintain audience engagement."
        ]
        learning_resources = [
            "FastAPI Advanced Guides & Production Architectures",
            "Cracking the Coding Interview & System Design Primer Course on Educative.io",
            "STAR Interviewing Technique Comprehensive Mastery Blueprint"
        ]

        # Attempt to synthesize custom AI feedback via Gemini
        dialogue_log = ""
        for idx, item in enumerate(transcript_items):
            dialogue_log += f"Q{idx+1}: {item.question_text}\nA{idx+1}: {item.candidate_answer or '(No response)'}\n\n"

        ai_prompt = (
            f"Generate a professional mock interview feedback evaluation for a finished session.\n"
            f"Interview Type: {interview_type}\n"
            f"Overall Score: {metrics.overall_score}\n"
            f"Dialogue Transcript:\n{dialogue_log}\n"
            f"Provide your evaluation in a plain JSON format with the following keys:\n"
            f'- "strengths": (list of strings representing candidate strengths)\n'
            f'- "weaknesses": (list of strings representing growth opportunities/weaknesses)\n'
            f'- "improvement_tips": (list of actionable steps to improve response quality)\n'
            f'- "learning_resources": (list of articles, courses, or guides they should read)\n'
            f'- "suggested_answers": (list of objects with "question_text" and "suggested_answer" keys providing high-performing model answers)\n\n'
            f"Output plain JSON only, with no markdown formatting."
        )

        ai_res = await GeminiClient.generate_text(prompt=ai_prompt)
        if ai_res:
            try:
                cleaned = ai_res.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                parsed = json.loads(cleaned)
                
                ai_suggested = []
                for mapping in parsed.get("suggested_answers", []):
                    if "question_text" in mapping and "suggested_answer" in mapping:
                        ai_suggested.append(
                            SuggestedAnswerMapping(
                                question_text=mapping["question_text"],
                                suggested_answer=mapping["suggested_answer"]
                            )
                        )

                return AIFeedbackResponse(
                    strengths=parsed.get("strengths", strengths),
                    weaknesses=parsed.get("weaknesses", weaknesses),
                    suggested_answers=ai_suggested if ai_suggested else suggested_answers,
                    improvement_tips=parsed.get("improvement_tips", improvement_tips),
                    learning_resources=parsed.get("learning_resources", learning_resources)
                )
            except Exception as e:
                logger.warning(f"Failed parsing detailed AI feedback: {str(e)}")

        return AIFeedbackResponse(
            strengths=strengths,
            weaknesses=weaknesses,
            suggested_answers=suggested_answers,
            improvement_tips=improvement_tips,
            learning_resources=learning_resources
        )


class InterviewService:
    """
    Unified Service Orchestrator for Enterprise AI Interview Platform.
    Integrates session management, real-time question generation, and grading.
    """
    def __init__(
        self,
        interview_repo: InterviewRepository,
        question_repo: QuestionRepository,
        history_repo: HistoryRepository,
        resume_repo: ResumeRepository,
        job_repo: JobRepository
    ) -> None:
        self.interview_repo = interview_repo
        self.question_repo = question_repo
        self.history_repo = history_repo
        self.resume_repo = resume_repo
        self.job_repo = job_repo
        self.question_svc = QuestionService(question_repo)

    async def get_session(self, session_id: uuid.UUID) -> Optional[InterviewSession]:
        """
        Fetches an active interview session.
        """
        return await self.interview_repo.get_session_with_relations(session_id)

    async def create_session(
        self,
        user_id: uuid.UUID,
        resume_id: uuid.UUID,
        interview_type: str,
        difficulty: str,
        practice_mode: str,
        duration: int,
        job_id: Optional[uuid.UUID] = None
    ) -> InterviewSession:
        """
        Creates, configures, and prepares an interview session.
        Auto-generates and caches questions inside the session context.
        """
        # 1. Verify Parents exist
        resume = await self.resume_repo.get(resume_id)
        if not resume:
            raise ValueError(f"Resume entity not found: {resume_id}")

        job_title = "General Position"
        company_name = "General Company"
        if job_id:
            job = await self.job_repo.get(job_id)
            if job:
                job_title = getattr(job, "title", job_title) or job_title
                company_name = getattr(job, "company_name", company_name) or company_name

        # 2. Setup Session Entity
        session = await self.interview_repo.create_session(
            user_id=user_id,
            resume_id=resume_id,
            interview_type=interview_type,
            difficulty=difficulty,
            practice_mode=practice_mode,
            duration=duration,
            job_id=job_id
        )

        # 3. Pull or generate target questions
        num_questions = 3 if practice_mode == "Quick Practice" else 5
        questions = await self.question_svc.get_questions_for_session(
            interview_type=interview_type,
            difficulty=difficulty,
            limit=num_questions,
            role=job_title,
            company=company_name
        )

        # 4. Initialize session transcript placeholder
        transcript = []
        for q in questions:
            transcript.append({
                "question_text": q,
                "candidate_answer": None,
                "score": None,
                "notes": None
            })

        # Commit questions cache to session
        session.transcript = transcript
        session.current_question_index = 0
        
        await self.interview_repo.update(session)
        return session

    async def start_interview_session(self, session_id: uuid.UUID) -> Optional[str]:
        """
        Starts the session. Transitions status to In_Progress and retrieves the first question.
        """
        session = await self.interview_repo.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session.status = "In_Progress"
        await self.interview_repo.update(session)
        
        if session.transcript and len(session.transcript) > 0:
            return session.transcript[0]["question_text"]
        return "Are you ready to begin the interview?"

    async def submit_candidate_answer(
        self,
        session_id: uuid.UUID,
        answer_text: str
    ) -> NextQuestionResponse:
        """
        Submits candidate's answer for the current question, evaluates it in real-time,
        and proceeds to select the next question or complete the loop.
        """
        session = await self.interview_repo.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if session.status != "In_Progress":
            raise ValueError(f"Session is in invalid state: {session.status}")

        idx = session.current_question_index
        transcript = list(session.transcript)

        if idx >= len(transcript):
            return NextQuestionResponse(
                question_index=idx,
                next_question=None,
                micro_feedback=None,
                is_finished=True
            )

        # 1. Update Transcript answer text
        current_item = dict(transcript[idx])
        current_item["candidate_answer"] = answer_text

        # 2. Run real-time answer evaluation
        micro_feedback = await EvaluationService.evaluate_answer(
            question=current_item["question_text"],
            answer=answer_text
        )

        # Cache micro scores
        current_item["score"] = micro_feedback.score
        current_item["notes"] = micro_feedback.feedback_notes
        transcript[idx] = current_item
        session.transcript = transcript

        # 3. Increment index and select next question or complete
        next_idx = idx + 1
        session.current_question_index = next_idx

        is_finished = next_idx >= len(transcript)
        next_q = None if is_finished else transcript[next_idx]["question_text"]

        if is_finished:
            # Transition to a pending completion step (final trigger happens in finish)
            session.status = "Paused" # Needs explicit finishing

        await self.interview_repo.update(session)

        return NextQuestionResponse(
            question_index=idx,
            next_question=next_q,
            micro_feedback=micro_feedback,
            is_finished=is_finished
        )

    async def finish_interview_session(self, session_id: uuid.UUID) -> InterviewSession:
        """
        Transitions interview status to Completed, triggers full multidimensional scoring
        and aggregates complete AI feedback and performance analytics.
        """
        session = await self.interview_repo.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # 1. Compile Transcript Items
        items = []
        for x in session.transcript:
            items.append(
                TranscriptItem(
                    question_text=x["question_text"],
                    candidate_answer=x.get("candidate_answer"),
                    score=x.get("score"),
                    notes=x.get("notes")
                )
            )

        # 2. Score session multi-axis
        metrics = await EvaluationService.score_session(
            transcript_items=items,
            interview_type=session.interview_type,
            difficulty=session.difficulty
        )

        # 3. Generate detailed actionable growth plan
        feedback = await FeedbackService.generate_feedback(
            transcript_items=items,
            metrics=metrics,
            interview_type=session.interview_type
        )

        # 4. Save calculations
        session.status = "Completed"
        session.overall_score = metrics.overall_score
        session.evaluation = metrics.model_dump()
        session.feedback = feedback.model_dump()
        session.updated_at = get_utc_now()

        await self.interview_repo.update(session)
        return session

    async def get_user_history(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        skip: int = 0
    ) -> List[InterviewHistoryItem]:
        """
        Retrieves practice attempt records chronologically.
        """
        sessions = await self.history_repo.get_history_by_user(user_id, limit=limit, skip=skip)
        
        items = []
        for s in sessions:
            items.append(
                InterviewHistoryItem(
                    id=s.id,
                    interview_type=s.interview_type,
                    difficulty=s.difficulty,
                    practice_mode=s.practice_mode,
                    status=s.status,
                    overall_score=s.overall_score,
                    created_at=s.created_at
                )
            )
        return items

    async def get_user_history_trend(self, user_id: uuid.UUID) -> InterviewHistoryTrend:
        """
        Calculates and tracks performance progression and trending metrics.
        """
        stats = await self.history_repo.get_aggregate_stats_by_user(user_id)
        
        # Pull 5 most recent completed attempts
        recent_sessions = await self.history_repo.get_history_by_user(user_id, limit=5)
        recent_items = []
        for s in recent_sessions:
            recent_items.append(
                InterviewHistoryItem(
                    id=s.id,
                    interview_type=s.interview_type,
                    difficulty=s.difficulty,
                    practice_mode=s.practice_mode,
                    status=s.status,
                    overall_score=s.overall_score,
                    created_at=s.created_at
                )
            )

        # Derive progression trend comment
        trend_text = "Establish your benchmark by completing your first mock interview!"
        if len(recent_items) >= 2:
            scores = [r.overall_score for r in recent_items if r.overall_score is not None]
            if len(scores) >= 2:
                # Compare oldest to newest
                diff = scores[0] - scores[-1] # Ordering is most recent first
                if diff > 3.0:
                    trend_text = "Superb! Your score shows a strong positive progression trend over your recent practice attempts."
                elif diff < -3.0:
                    trend_text = "Consolidating. Your performance has dipped slightly; focus on reviewing improvement tips to boost ratings."
                else:
                    trend_text = "Consistent. Your response scoring remains stable and consistent across recent runs."

        return InterviewHistoryTrend(
            attempts_count=stats["attempts_count"],
            average_score=stats["average_score"],
            improvement_trend=trend_text,
            recent_attempts=recent_items
        )
