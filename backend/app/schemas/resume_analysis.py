import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    category: str = Field(..., description="e.g., DATE, FORMATTING, COMPLETENESS, SPELLING, GRAMMAR")
    severity: str = Field(..., description="INFO, WARNING, ERROR")
    section: str = Field(..., description="The resume section where issue occurs")
    message: str = Field(..., description="Description of the issue")
    suggestion: Optional[str] = Field(None, description="Actionable suggestion to fix the issue")


class SectionStatus(BaseModel):
    section_name: str
    is_present: bool
    word_count: int
    completeness_percentage: float
    issues: List[ValidationIssue] = Field(default_factory=list)


class ChronologyIssue(BaseModel):
    section: str
    entry_index: int
    message: str
    severity: str


class DateAnalysis(BaseModel):
    is_chronological: bool
    total_years_experience: float
    overlapping_intervals: List[Dict[str, Any]] = Field(default_factory=list)
    issues: List[ChronologyIssue] = Field(default_factory=list)


class KeywordMatch(BaseModel):
    keyword: str
    count: int
    category: str  # e.g., TECHNICAL, LEADERSHIP, METHODOLOGY, BUSINESS


class SkillNormalizationResult(BaseModel):
    original: str
    normalized: str
    category: Optional[str] = None


class ResumeStats(BaseModel):
    total_words: int
    total_sentences: int
    avg_bullet_length: float
    section_word_counts: Dict[str, int]


class QualityScoreBreakdown(BaseModel):
    completeness: float = Field(..., description="Score 0-100")
    structure: float = Field(..., description="Score 0-100")
    formatting: float = Field(..., description="Score 0-100")
    impact: float = Field(..., description="Score 0-100")


class ResumeQualityReport(BaseModel):
    resume_id: Optional[uuid.UUID] = None
    health_score: float = Field(..., description="Overall score out of 100")
    rating: str = Field(..., description="e.g., EXCELLENT, GOOD, IMPROVEMENT_NEEDED, CRITICAL")
    score_breakdown: QualityScoreBreakdown
    completeness_percentage: float
    sections: List[SectionStatus] = Field(default_factory=list)
    date_analysis: DateAnalysis
    issues: List[ValidationIssue] = Field(default_factory=list)
    keywords: List[KeywordMatch] = Field(default_factory=list)
    normalized_skills: List[SkillNormalizationResult] = Field(default_factory=list)
    statistics: ResumeStats
    duplicate_entries_detected: List[Dict[str, Any]] = Field(default_factory=list)
