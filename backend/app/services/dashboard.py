import base64
import uuid
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dashboard_repositories import (
    DashboardWidgetRepository,
    ExecutiveReportRepository,
    AnalyticsRepository
)
from app.models.dashboard import DashboardWidget, ExecutiveReport
from app.models.profile import UserProfile
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    CompleteAnalyticsResponse,
    ResumeAnalyticsData,
    JobAnalyticsData,
    InterviewAnalyticsData,
    CareerAnalyticsData,
    AIAnalyticsData,
    ReportGenerateRequest,
    ReportExportResponse
)
from app.models.ats import ATSReport
from app.models.interview import InterviewSession
from app.models.job import SavedJob

logger = logging.getLogger("app.services.dashboard")


class DashboardService:
    """
    Coordinates layout configs, interactive activity streams, and quick action widgets.
    """
    def __init__(
        self,
        widget_repo: DashboardWidgetRepository,
        db_session: AsyncSession
    ) -> None:
        self.widget_repo = widget_repo
        self.db = db_session

    async def get_summary(self, user_id: uuid.UUID) -> DashboardSummaryResponse:
        """
        Creates a welcoming, structured digest of recent career actions and progress markers.
        """
        # Fetch user profile for customized welcome text
        prof_query = select(UserProfile).where(UserProfile.user_id == user_id)
        prof_res = await self.db.execute(prof_query)
        profile = prof_res.scalar_or_none()

        name = "Candidate"
        if profile and profile.first_name:
            name = profile.first_name

        welcome_message = f"Welcome back, {name}! Let's accelerate your job search today."

        # Fetch recent database activities to merge into a single chronological feed
        recent_activity: List[Dict[str, Any]] = []

        # 1. Recent ATS reports
        ats_query = select(ATSReport).where(ATSReport.user_id == user_id).order_by(desc(ATSReport.created_at)).limit(3)
        ats_res = await self.db.execute(ats_query)
        recent_scans = list(ats_res.scalars().all())
        for s in recent_scans:
            recent_activity.append({
                "type": "resume_scan",
                "title": "Resume Optimized",
                "description": f"Analyzed CV against '{s.job_title}' with score {s.ats_score}%",
                "timestamp": s.created_at.isoformat() if s.created_at else datetime.utcnow().isoformat()
            })

        # 2. Recent Mock Interviews
        int_query = select(InterviewSession).where(InterviewSession.user_id == user_id).order_by(desc(InterviewSession.created_at)).limit(3)
        int_res = await self.db.execute(int_query)
        recent_ints = list(int_res.scalars().all())
        for i in recent_ints:
            recent_activity.append({
                "type": "interview",
                "title": f"{i.interview_type} Practice",
                "description": f"Completed {i.difficulty} difficulty session. Score: {i.overall_score or 0.0}%",
                "timestamp": i.created_at.isoformat() if i.created_at else datetime.utcnow().isoformat()
            })

        # 3. Recent Bookmarked jobs
        job_query = select(SavedJob).where(SavedJob.user_id == user_id).order_by(desc(SavedJob.created_at)).limit(3)
        job_res = await self.db.execute(job_query)
        recent_jobs = list(job_res.scalars().all())
        for j in recent_jobs:
            recent_activity.append({
                "type": "saved_job",
                "title": "Job Saved",
                "description": "Bookmarked a new target role in Favorites list.",
                "timestamp": j.created_at.isoformat() if j.created_at else datetime.utcnow().isoformat()
            })

        # Sort combined feed newest first
        recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_activity = recent_activity[:5]

        # Calculate high-level counts to craft tailored digests
        scans_count = len(recent_scans)
        interviews_count = len(recent_ints)
        saved_count = len(recent_jobs)

        daily_summary = f"Today's Overview: You have bookmarked {saved_count} target job listings and run {scans_count} system compatibility scans."
        weekly_summary = f"Weekly targets: Aim to complete at least 2 behavioral mock sessions and optimize your primary CV for 3 upcoming listings."
        monthly_summary = f"Monthly Outlook: Keep matching scores above 75% to maximize interview callbacks from active applications."

        quick_actions = [
            {"action": "Optimize Resume", "description": "Run an instant ATS compatibility scan against target listings", "link": "/ats", "importance": "high"},
            {"action": "Practice Interviewing", "description": "Launch AI Coach to refine system design or behavioral answers", "link": "/interview", "importance": "high"},
            {"action": "Update Goals", "description": "Mark weekly targets completed to raise readiness index", "link": "/career", "importance": "medium"},
        ]

        # Aggregate growth percentages
        career_progress = {
            "total_scans": scans_count,
            "total_interviews": interviews_count,
            "readiness_milestones": 1 + (scans_count // 2),
            "target_ready_percentage": min(95.0, 45.0 + (scans_count * 5) + (interviews_count * 10))
        }

        return DashboardSummaryResponse(
            welcome_message=welcome_message,
            daily_summary=daily_summary,
            weekly_summary=weekly_summary,
            monthly_summary=monthly_summary,
            quick_actions=quick_actions,
            recent_activity=recent_activity,
            career_progress=career_progress
        )

    async def get_or_create_widgets(self, user_id: uuid.UUID) -> List[DashboardWidget]:
        return await self.widget_repo.get_or_create_default_widgets(user_id)

    async def update_bulk_layouts(self, user_id: uuid.UUID, updates: List[Dict[str, Any]]) -> List[DashboardWidget]:
        return await self.widget_repo.update_bulk_layouts(user_id=user_id, updates=updates)


class PlatformAnalyticsService:
    """
    Consolidates data across all JobCatalyst modules to provide complete analytic views.
    """
    def __init__(self, analytics_repo: AnalyticsRepository) -> None:
        self.analytics_repo = analytics_repo

    async def get_all_analytics(self, user_id: uuid.UUID) -> CompleteAnalyticsResponse:
        """
        Compiles the complete set of analytics models for candidate evaluation.
        """
        resume_raw = await self.analytics_repo.get_resume_analytics(user_id)
        job_raw = await self.analytics_repo.get_job_analytics(user_id)
        interview_raw = await self.analytics_repo.get_interview_analytics(user_id)
        career_raw = await self.analytics_repo.get_career_analytics(user_id)
        ai_raw = await self.analytics_repo.get_ai_analytics(user_id)

        return CompleteAnalyticsResponse(
            resume=ResumeAnalyticsData(**resume_raw),
            job=JobAnalyticsData(**job_raw),
            interview=InterviewAnalyticsData(**interview_raw),
            career=CareerAnalyticsData(**career_raw),
            ai=AIAnalyticsData(**ai_raw)
        )


class ReportService:
    """
    Generates tailored Weekly, Monthly, Resume, Application, and Career coaching reports.
    """
    def __init__(
        self,
        report_repo: ExecutiveReportRepository,
        analytics_repo: AnalyticsRepository,
        db_session: AsyncSession
    ) -> None:
        self.report_repo = report_repo
        self.analytics_repo = analytics_repo
        self.db = db_session

    async def generate_report(self, user_id: uuid.UUID, payload: ReportGenerateRequest) -> ExecutiveReport:
        """
        Assembles a report containing deep analytics, insights, and specific action steps.
        """
        # Fetch actual metrics
        resume_metrics = await self.analytics_repo.get_resume_analytics(user_id)
        job_metrics = await self.analytics_repo.get_job_analytics(user_id)
        interview_metrics = await self.analytics_repo.get_interview_analytics(user_id)
        career_metrics = await self.analytics_repo.get_career_analytics(user_id)
        ai_metrics = await self.analytics_repo.get_ai_analytics(user_id)

        # Assemble basic descriptive information and rules-based insights
        score_history = resume_metrics.get("resume_score_history", [])
        avg_resume_score = sum(item["score"] for item in score_history) / len(score_history) if score_history else 0.0

        avg_int_score = interview_metrics.get("average_score", 0.0)
        success_rate = interview_metrics.get("success_rate", 0.0)

        # Base structure
        content = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "reporting_interval": payload.report_type,
                "range_start": payload.start_date.isoformat() if payload.start_date else None,
                "range_end": payload.end_date.isoformat() if payload.end_date else None,
            },
            "kpi_overview": {
                "resume_score_average": round(avg_resume_score, 1),
                "interviews_average_score": avg_int_score,
                "mock_interview_success_ratio": success_rate,
                "applications_count": job_metrics.get("applications_submitted", 0),
                "saved_listings": job_metrics.get("jobs_saved", 0),
                "career_readiness_score": career_metrics.get("career_score", 60.0),
                "accrued_ai_overhead_usd": ai_metrics.get("estimated_cost", 0.0)
            },
            "strengths": [],
            "growth_areas": [],
            "action_items": []
        }

        # Inject logical, descriptive items based on metrics
        if avg_resume_score >= 80:
            content["strengths"].append("Your target resumes exhibit high ATS compatibility levels.")
        else:
            content["growth_areas"].append("Several critical keyword gaps persist in your primary CV.")
            content["action_items"].append("Re-align the skills matrix on your primary resume with key target listings.")

        if avg_int_score >= 75:
            content["strengths"].append("Strong articulation and communication displayed in mock interviews.")
        else:
            content["growth_areas"].append("Struggling with higher difficulty technical and behavioral questions.")
            content["action_items"].append("Schedule another Behavioral mock interview session to practice STAR responses.")

        if job_metrics.get("applications_submitted", 0) < 3:
            content["action_items"].append("Identify and run ATS scans on at least 3 new job listings this week.")

        # Default fallback descriptions if empty
        if not content["strengths"]:
            content["strengths"].append("Initial profile initialized and ready for structural coaching.")
        if not content["growth_areas"]:
            content["growth_areas"].append("Expand portfolio diversity and practicing higher difficulty system design.")
        if not content["action_items"]:
            content["action_items"].append("Generate a new career roadmap checklist inside the Career Coach module.")

        report_data = {
            "user_id": user_id,
            "report_type": payload.report_type,
            "start_date": payload.start_date or (datetime.utcnow() - timedelta(days=7)),
            "end_date": payload.end_date or datetime.utcnow(),
            "content_json": content,
            "export_meta": {
                "is_cached": True,
                "times_downloaded": 0
            }
        }

        new_report = await self.report_repo.create(report_data)
        await self.db.commit()
        return new_report


class ExportService:
    """
    Handles rendering and base64 export conversion of compiled executive reports.
    """
    def __init__(self, report_repo: ExecutiveReportRepository) -> None:
        self.report_repo = report_repo

    async def export_pdf_b64(self, user_id: uuid.UUID, report_id: uuid.UUID) -> ReportExportResponse:
        """
        Generates a beautifully structured PDF mock-stream, encoded as base64.
        """
        report = await self.report_repo.get(report_id)
        if not report or report.user_id != user_id:
            raise ValueError("Requested report not found or authorization failed.")

        content = report.content_json
        meta = content.get("metadata", {})
        kpis = content.get("kpi_overview", {})

        # Build a highly clean text design layout representing the PDF document content
        document_text = f"""
========================================================================
                      JOBCATALYST AI EXECUTIVE COOPERATION
                         OFFICIAL REPORT: {report.report_type.upper()}
========================================================================
Generated At: {meta.get("generated_at", "N/A")}
Report ID: {str(report.id)}
User Reference: {str(user_id)}
Reporting Window: {report.start_date.strftime("%Y-%m-%d") if report.start_date else "N/A"} to {report.end_date.strftime("%Y-%m-%d") if report.end_date else "N/A"}

------------------------------------------------------------------------
1. EXECUTIVE PERFORMANCE METRICS (KPIs)
------------------------------------------------------------------------
* Average Resume Match Index:   {kpis.get("resume_score_average", 0.0)}%
* Career Readiness Rating:      {kpis.get("career_readiness_score", 0.0)}%
* Mock Interview Average:       {kpis.get("interviews_average_score", 0.0)}%
* Interview Success Percentage: {kpis.get("mock_interview_success_ratio", 0.0)}%
* Logged Applications Count:    {kpis.get("applications_count", 0)}
* Bookmarked Target Roles:      {kpis.get("saved_listings", 0)}
* AI System Overhead (USD):     ${kpis.get("accrued_ai_overhead_usd", 0.00)}

------------------------------------------------------------------------
2. HIGHLIGHTED CORE STRENGTHS
------------------------------------------------------------------------
"""
        for s in content.get("strengths", []):
            document_text += f"- {s}\n"

        document_text += """
------------------------------------------------------------------------
3. IDENTIFIED ROADMAP GROWTH AREAS
------------------------------------------------------------------------
"""
        for g in content.get("growth_areas", []):
            document_text += f"- {g}\n"

        document_text += """
------------------------------------------------------------------------
4. SUGGESTED ACTION ITEMS & PLAN
------------------------------------------------------------------------
"""
        for idx, a in enumerate(content.get("action_items", [])):
            document_text += f"{idx + 1}. {a}\n"

        document_text += """
========================================================================
                    © 2026 JobCatalyst AI. All Rights Reserved.
========================================================================
"""
        b64_data = base64.b64encode(document_text.encode("utf-8")).decode("utf-8")

        return ReportExportResponse(
            file_name=f"JobCatalyst_{report.report_type}_Report_{datetime.utcnow().strftime('%Y%m%d')}.pdf",
            media_type="application/pdf",
            download_url="",
            content_b64=b64_data
        )

    async def export_excel_b64(self, user_id: uuid.UUID, report_id: uuid.UUID) -> ReportExportResponse:
        """
        Compiles an enterprise-grade CSV layout mock-stream, encoded as base64.
        """
        report = await self.report_repo.get(report_id)
        if not report or report.user_id != user_id:
            raise ValueError("Requested report not found or authorization failed.")

        content = report.content_json
        kpis = content.get("kpi_overview", {})

        csv_lines = [
            "JobCatalyst AI Report,Executive Summary Table",
            f"Report ID,{str(report.id)}",
            f"Report Type,{report.report_type}",
            f"Start Date,{report.start_date.isoformat() if report.start_date else ''}",
            f"End Date,{report.end_date.isoformat() if report.end_date else ''}",
            "",
            "Core Key Performance Indicators (KPIs)",
            f"Average Resume ATS Score,{kpis.get('resume_score_average', 0.0)}%",
            f"Career Readiness Rating,{kpis.get('career_readiness_score', 0.0)}%",
            f"Mock Interview Score Average,{kpis.get('interviews_average_score', 0.0)}%",
            f"Mock Interview Success Ratio,{kpis.get('mock_interview_success_ratio', 0.0)}%",
            f"Tracked Applications count,{kpis.get('applications_count', 0)}",
            f"Saved listings,{kpis.get('saved_listings', 0)}",
            f"Accrued AI Overhead (USD),${kpis.get('accrued_ai_overhead_usd', 0.00)}",
            "",
            "Strengths List"
        ]
        for s in content.get("strengths", []):
            csv_lines.append(f"Strength,\"{s}\"")

        csv_lines.append("")
        csv_lines.append("Growth Areas List")
        for g in content.get("growth_areas", []):
            csv_lines.append(f"Growth Area,\"{g}\"")

        csv_lines.append("")
        csv_lines.append("Recommended Action Plan")
        for idx, a in enumerate(content.get("action_items", [])):
            csv_lines.append(f"Action Step {idx + 1},\"{a}\"")

        csv_text = "\n".join(csv_lines)
        b64_data = base64.b64encode(csv_text.encode("utf-8")).decode("utf-8")

        return ReportExportResponse(
            file_name=f"JobCatalyst_{report.report_type}_Spreadsheet_{datetime.utcnow().strftime('%Y%m%d')}.csv",
            media_type="text/csv",
            download_url="",
            content_b64=b64_data
        )
