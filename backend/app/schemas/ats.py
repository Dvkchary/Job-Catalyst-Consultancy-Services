import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ATSAnalysisRequest(BaseModel):
    resume_id: uuid.UUID = Field(..., description="UUID of the resume to evaluate")
    job_description: str = Field(..., description="The complete text of the Job Description")
    job_title: Optional[str] = Field(None, description="The job title for target comparison")


class KeywordMatchDetails(BaseModel):
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    keyword_match_percentage: float = Field(..., description="Percentage of keywords matched")


class FormattingDetails(BaseModel):
    has_unsupported_fonts: bool = Field(False)
    has_poor_margins: bool = Field(False)
    has_complex_tables: bool = Field(False)
    has_charts_or_images: bool = Field(False)
    issues: List[str] = Field(default_factory=list)


class ReadabilityDetails(BaseModel):
    flesch_reading_ease: float
    grade_level: str
    readability_rating: str  # e.g., EASY, STANDARD, DIFFICULT, VERY_DIFFICULT


class GrammarDetails(BaseModel):
    errors_detected: int
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class ActionVerbDetails(BaseModel):
    action_verbs_count: int
    verbs_used: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class SectionCompletenessDetails(BaseModel):
    present_sections: List[str] = Field(default_factory=list)
    missing_essential_sections: List[str] = Field(default_factory=list)
    completeness_percentage: float


class BenchmarkDetails(BaseModel):
    industry_average_score: float = Field(default=65.0)
    user_percentile: float = Field(default=50.0)
    rating: str = Field(..., description="BELOW_AVERAGE, AVERAGE, ABOVE_AVERAGE, OUTSTANDING")


class ATSReportData(BaseModel):
    ats_score: int
    keyword_matching: KeywordMatchDetails
    formatting_analysis: FormattingDetails
    readability_analysis: ReadabilityDetails
    grammar_analysis: GrammarDetails
    action_verb_analysis: ActionVerbDetails
    section_completeness: SectionCompletenessDetails
    ai_suggestions: List[str] = Field(default_factory=list)
    benchmark: BenchmarkDetails


class ATSReportResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    job_title: Optional[str] = None
    job_description: str
    ats_score: int
    report_data: ATSReportData
    created_at: datetime


class ResumeComparisonRequest(BaseModel):
    resume_a_id: uuid.UUID
    resume_b_id: uuid.UUID
    job_description: str


class ScoreMetricComparison(BaseModel):
    score_a: float
    score_b: float
    comparison_notes: str


class ResumeComparisonResponse(BaseModel):
    resume_a_id: uuid.UUID
    resume_b_id: uuid.UUID
    common_skills: List[str] = Field(default_factory=list)
    unique_skills_a: List[str] = Field(default_factory=list)
    unique_skills_b: List[str] = Field(default_factory=list)
    ats_score_a: int
    ats_score_b: int
    score_comparison: Dict[str, ScoreMetricComparison] = Field(default_factory=dict)
    comparison_summary: str
