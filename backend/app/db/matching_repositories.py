import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import BaseRepository
from app.models.ats import ATSReport


class MatchingRepository(BaseRepository[ATSReport]):
    """
    Data-access repository for saving, updating, and querying semantic matching reports.
    Uses the underlying ATSReport database model for secure storage.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=ATSReport, db=db)

    async def create_match_report(
        self,
        user_id: uuid.UUID,
        resume_id: uuid.UUID,
        job_title: str,
        job_description: str,
        overall_score: float,
        report_data_dict: Dict[str, Any],
        job_id: Optional[uuid.UUID] = None
    ) -> ATSReport:
        """
        Persists a complete resume-to-job matching result as an ATSReport entity.
        """
        # Embed the matching-specific metadata inside the JSON report_data structure
        report_data_dict["matching_metadata"] = {
            "type": "semantic_match",
            "job_id": str(job_id) if job_id else None,
            "job_title": job_title
        }

        db_input = {
            "user_id": user_id,
            "resume_id": resume_id,
            "job_title": job_title,
            "job_description": job_description,
            "ats_score": int(overall_score),
            "report_data": report_data_dict
        }

        return await self.create(db_input, creator_id=str(user_id))

    async def get_match_report(self, match_id: uuid.UUID) -> Optional[ATSReport]:
        """
        Fetches an active matching report by ID.
        """
        return await self.get(match_id)


class AnalysisRepository(BaseRepository[ATSReport]):
    """
    Data-access repository for detailed ATS analyses and requirements extraction.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=ATSReport, db=db)

    async def save_job_analysis(
        self,
        user_id: uuid.UUID,
        resume_id: uuid.UUID,
        job_title: str,
        job_description: str,
        ats_score: float,
        analysis_data: Dict[str, Any]
    ) -> ATSReport:
        """
        Saves a distinct job/resume ATS and skill gap analysis to the database.
        """
        analysis_data["analysis_metadata"] = {
            "type": "requirements_analysis",
            "job_title": job_title
        }

        db_input = {
            "user_id": user_id,
            "resume_id": resume_id,
            "job_title": job_title,
            "job_description": job_description,
            "ats_score": int(ats_score),
            "report_data": analysis_data
        }

        return await self.create(db_input, creator_id=str(user_id))

    async def get_job_analysis(self, analysis_id: uuid.UUID) -> Optional[ATSReport]:
        """
        Fetches an analysis report by ID.
        """
        return await self.get(analysis_id)


class HistoryRepository(BaseRepository[ATSReport]):
    """
    Data-access repository for tracking match history chronological audit trails.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=ATSReport, db=db)

    async def get_match_history_by_user(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        skip: int = 0
    ) -> List[ATSReport]:
        """
        Retrieves matching history for a specific user, ordered by most recent first.
        """
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.deleted_at.is_(None) if hasattr(self.model, "deleted_at") else True
            )
        ).order_by(desc(self.model.created_at)).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_match_history_by_resume(
        self,
        resume_id: uuid.UUID,
        limit: int = 50,
        skip: int = 0
    ) -> List[ATSReport]:
        """
        Retrieves matching history for a specific resume, ordered by most recent first.
        """
        query = select(self.model).where(
            and_(
                self.model.resume_id == resume_id,
                self.model.deleted_at.is_(None) if hasattr(self.model, "deleted_at") else True
            )
        ).order_by(desc(self.model.created_at)).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())
