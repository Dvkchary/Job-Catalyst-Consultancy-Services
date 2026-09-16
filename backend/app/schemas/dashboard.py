import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =====================================================================
# WIDGET SCHEMAS
# =====================================================================

class WidgetConfigCreate(BaseModel):
    widget_key: str = Field(..., description="Unique key for the widget type, e.g. resume_score_trend.")
    title: str = Field(..., description="Display title for the widget.")
    is_visible: bool = Field(True, description="Whether the widget should render.")
    layout_x: int = Field(0, description="Grid X coordinate.")
    layout_y: int = Field(0, description="Grid Y coordinate.")
    layout_w: int = Field(4, description="Grid width.")
    layout_h: int = Field(3, description="Grid height.")
    settings_json: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary widget settings for extension plugins.")


class WidgetConfigUpdate(BaseModel):
    title: Optional[str] = None
    is_visible: Optional[bool] = None
    layout_x: Optional[int] = None
    layout_y: Optional[int] = None
    layout_w: Optional[int] = None
    layout_h: Optional[int] = None
    settings_json: Optional[Dict[str, Any]] = None


class WidgetResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    widget_key: str
    title: str
    is_visible: bool
    layout_x: int
    layout_y: int
    layout_w: int
    layout_h: int
    settings_json: Dict[str, Any]
    created_at: Any
    updated_at: Any

    class Config:
        from_attributes = True


class WidgetBulkLayoutUpdate(BaseModel):
    id: uuid.UUID
    layout_x: int
    layout_y: int
    layout_w: int
    layout_h: int


# =====================================================================
# ANALYTICS METRICS SUB-SCHEMAS
# =====================================================================

class ResumeAnalyticsData(BaseModel):
    resume_score_history: List[Dict[str, Any]] = Field(..., description="Historic scores over time.")
    ats_trends: List[Dict[str, Any]] = Field(..., description="Chronological scan score comparisons.")
    resume_views: int = Field(0, description="Simulated total times resume was viewed.")
    resume_downloads: int = Field(0, description="Simulated total times resume was downloaded.")
    optimization_history: List[Dict[str, Any]] = Field(..., description="Records of ATS scans and dates.")
    version_comparison: List[Dict[str, Any]] = Field(..., description="Side-by-side differences of versions.")


class JobAnalyticsData(BaseModel):
    jobs_viewed: int = Field(0, description="Aggregate viewed job listings.")
    jobs_saved: int = Field(0, description="Count of favorites or bookmarked roles.")
    applications_submitted: int = Field(0, description="ATS report count as a proxy for application.")
    response_rate: float = Field(0.0, description="Percentage of responses (e.g. 1-100).")
    interview_rate: float = Field(0.0, description="Percentage of matches that converted to interviews (1-100).")
    offer_rate: float = Field(0.0, description="Percentage of interviews that led to offers (1-100).")


class InterviewAnalyticsData(BaseModel):
    interview_history: List[Dict[str, Any]] = Field(..., description="History of mock interview session records.")
    average_score: float = Field(0.0, description="Average cumulative score across sessions.")
    skill_performance: Dict[str, float] = Field(..., description="Performance scores split by interview types or categories.")
    improvement_trends: List[Dict[str, Any]] = Field(..., description="Comparison markers over consecutive attempts.")
    success_rate: float = Field(0.0, description="Ratio of successful (score >= 70) attempts.")


class CareerAnalyticsData(BaseModel):
    career_score: float = Field(0.0, description="Active profile rating.")
    learning_progress: Dict[str, Any] = Field(..., description="Skills, hours, and goals finished.")
    skill_growth: List[Dict[str, Any]] = Field(..., description="Skill mastery progressions.")
    goal_progress: Dict[str, Any] = Field(..., description="Counts of weekly/monthly checkboxes hit.")
    salary_growth: Dict[str, Any] = Field(..., description="Trend data showing current vs target vs industry average compensation.")


class AIAnalyticsData(BaseModel):
    ai_requests: int = Field(0, description="Total logged AI requests count.")
    tokens_used: int = Field(0, description="Prompt + Completion tokens aggregated.")
    provider_usage: Dict[str, int] = Field(..., description="Request counts partitioned by provider name.")
    estimated_cost: float = Field(0.0, description="Accrued USD cost estimate.")
    recommendations_generated: int = Field(0, description="Total active recommendations lists created.")


# =====================================================================
# SYSTEM & SUMMARY SCHEMAS
# =====================================================================

class DashboardSummaryResponse(BaseModel):
    welcome_message: str = Field(..., description="Personalized greeting.")
    daily_summary: str = Field(..., description="Dynamic short status snapshot of today.")
    weekly_summary: str = Field(..., description="Summary of current week's targets.")
    monthly_summary: str = Field(..., description="High-level monthly perspective.")
    quick_actions: List[Dict[str, Any]] = Field(..., description="Recommended clickable actions based on current status.")
    recent_activity: List[Dict[str, Any]] = Field(..., description="Audit of recent actions, scans, or interviews.")
    career_progress: Dict[str, Any] = Field(..., description="Composite growth tracking metric summary.")


class CompleteAnalyticsResponse(BaseModel):
    resume: ResumeAnalyticsData
    job: JobAnalyticsData
    interview: InterviewAnalyticsData
    career: CareerAnalyticsData
    ai: AIAnalyticsData


# =====================================================================
# EXECUTIVE REPORT SCHEMAS
# =====================================================================

class ReportGenerateRequest(BaseModel):
    report_type: str = Field(..., description="Weekly, Monthly, Career, Resume, or Application.")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ExecutiveReportResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    report_type: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    content_json: Dict[str, Any]
    export_meta: Dict[str, Any]
    created_at: Any
    updated_at: Any

    class Config:
        from_attributes = True


class ReportExportResponse(BaseModel):
    file_name: str
    media_type: str
    download_url: str
    content_b64: str  # Encoded byte structure so client can immediately fetch or write locally
