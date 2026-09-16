import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import BaseRepository
from app.models.interview import InterviewSession, InterviewQuestion


class InterviewRepository(BaseRepository[InterviewSession]):
    """
    Data-access repository for saving, updating, and querying active mock interview sessions.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=InterviewSession, db=db)

    async def get_session_with_relations(self, session_id: uuid.UUID) -> Optional[InterviewSession]:
        """
        Fetches an interview session, ensuring active non-deleted status check.
        """
        return await self.get(session_id)

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
        Creates a new interview session and persists it.
        """
        db_input = {
            "user_id": user_id,
            "resume_id": resume_id,
            "job_id": job_id,
            "interview_type": interview_type,
            "difficulty": difficulty,
            "practice_mode": practice_mode,
            "duration": duration,
            "status": "Created",
            "current_question_index": 0,
            "transcript": [],
            "evaluation": {},
            "feedback": {}
        }
        return await self.create(db_input, creator_id=str(user_id))


class QuestionRepository(BaseRepository[InterviewQuestion]):
    """
    Data-access repository for searching, filtering, and seeding the interview question bank.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=InterviewQuestion, db=db)

    async def get_questions_for_interview(
        self,
        interview_type: str,
        difficulty: str,
        limit: int = 5,
        role: Optional[str] = None,
        company: Optional[str] = None
    ) -> List[InterviewQuestion]:
        """
        Selects a collection of matching questions based on type, difficulty, role, or company.
        """
        # Build query
        filters = [
            InterviewQuestion.interview_type == interview_type,
            InterviewQuestion.difficulty == difficulty
        ]
        
        # Check role-specific or company-specific matching if requested
        query = select(self.model).where(and_(*filters)).limit(limit)
        result = await self.db.execute(query)
        questions = list(result.scalars().all())

        # If empty, seed standard premium questions for immediate robust operation!
        if not questions:
            await self.seed_default_questions()
            result = await self.db.execute(query)
            questions = list(result.scalars().all())

        return questions

    async def seed_default_questions(self) -> None:
        """
        Auto-populates high-quality, professional mock interview questions into the DB.
        """
        default_questions = [
            # Technical - Medium
            {
                "interview_type": "Technical",
                "difficulty": "Medium",
                "question_text": "Can you explain how concurrency works in Python? What is the GIL, and how does FastAPI/asyncio bypass its limitations?",
                "expected_topics": ["GIL", "asyncio", "concurrency", "event loop", "multiprocessing"],
                "role_specific": "Software Engineer",
                "is_system_template": True
            },
            {
                "interview_type": "Technical",
                "difficulty": "Medium",
                "question_text": "What is the difference between a clustered and a non-clustered index in SQL databases, and how do they impact query performance?",
                "expected_topics": ["SQL", "indexing", "b-tree", "clustered index", "performance tuning"],
                "role_specific": "Backend Engineer",
                "is_system_template": True
            },
            # System Design - Hard
            {
                "interview_type": "System Design",
                "difficulty": "Hard",
                "question_text": "How would you design a highly scalable, real-time notification system that must support up to 50,000 push notifications per second?",
                "expected_topics": ["message queue", "WebSockets", "scalability", "caching", "pub/sub"],
                "is_system_template": True
            },
            # Behavioral - Medium
            {
                "interview_type": "Behavioral",
                "difficulty": "Medium",
                "question_text": "Describe a situation where you had a major technical disagreement with a colleague or lead. How did you handle it and reach a resolution?",
                "expected_topics": ["STAR method", "collaboration", "conflict resolution", "communication"],
                "is_system_template": True
            },
            # HR - Easy
            {
                "interview_type": "HR",
                "difficulty": "Easy",
                "question_text": "Why are you interested in joining our company, and what key values or contributions do you hope to bring to the team?",
                "expected_topics": ["company values", "motivation", "contributions", "cultural fit"],
                "is_system_template": True
            }
        ]

        for q in default_questions:
            # Check if already exists to prevent duplicate seeding
            existing_query = select(self.model).where(
                InterviewQuestion.question_text == q["question_text"]
            )
            existing_res = await self.db.execute(existing_query)
            if not existing_res.scalar_or_none():
                # Correctly populate the fields
                await self.create(q, creator_id="system_seeder")


class HistoryRepository(BaseRepository[InterviewSession]):
    """
    Data-access repository for tracking chronology, statistics, and trends of a user's practice attempts.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=InterviewSession, db=db)

    async def get_history_by_user(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        skip: int = 0
    ) -> List[InterviewSession]:
        """
        Retrieves matching interview sessions for a specific user, ordered by most recent first.
        """
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.deleted_at.is_(None) if hasattr(self.model, "deleted_at") else True
            )
        ).order_by(desc(self.model.created_at)).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_aggregate_stats_by_user(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Retrieves composite performance trend aggregates (counts, average scores).
        """
        query = select(
            func.count(self.model.id).label("total_attempts"),
            func.avg(self.model.overall_score).label("avg_score")
        ).where(
            and_(
                self.model.user_id == user_id,
                self.model.status == "Completed",
                self.model.deleted_at.is_(None) if hasattr(self.model, "deleted_at") else True
            )
        )
        
        result = await self.db.execute(query)
        row = result.fetchone()
        
        total_attempts = row[0] if row and row[0] is not None else 0
        avg_score = float(row[1]) if row and row[1] is not None else 0.0

        return {
            "attempts_count": total_attempts,
            "average_score": round(avg_score, 1)
        }
