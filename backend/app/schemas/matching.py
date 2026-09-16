import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MatchResumeRequest(BaseModel):
    resume_id: uuid.UUID = Field(..., description="The ID of the resume to evaluate.")
    job_id: Optional[uuid.UUID] = Field(None, description="Optional ID of a saved job listing.")
    job_description: Optional[str] = Field(None, description="Optional raw text of the target job description.")


class CompareResumeRequest(BaseModel):
    resume_a_id: uuid.UUID = Field(..., description="The ID of the first resume (A).")
    resume_b_id: uuid.UUID = Field(..., description="The ID of the second resume (B).")
    job_id: Optional[uuid.UUID] = Field(None, description="Optional ID of a saved job listing.")
    job_description: Optional[str] = Field(None, description="Optional raw text of the target job description.")


class MatchingScoreBreakdown(BaseModel):
    overall_match: float = Field(..., description="Weighted average overall match percentage.")
    ats_score: float = Field(..., description="Keyword-level scanning compatibility.")
    skill_score: float = Field(..., description="Technical and soft skills alignment.")
    experience_score: float = Field(..., description="Years and relevant experience match.")
    education_score: float = Field(..., description="Academic degree and major match.")
    location_score: float = Field(..., description="Workplace setup and geolocation compatibility.")
    visa_score: float = Field(..., description="Work authorization and sponsorship status.")
    salary_score: float = Field(..., description="Compensation and expected salary match.")
    confidence_score: float = Field(..., description="Confidence rating of the AI Matching Engine.")


class SkillGapAnalysis(BaseModel):
    missing_skills: List[str] = Field(default_list=[], description="Target skills in the job description missing from the resume.")
    matching_skills: List[str] = Field(default_list=[], description="Overlapping skills present in both resume and JD.")
    recommended_skills: List[str] = Field(default_list=[], description="Highly related adjacent skills to acquire.")
    learning_suggestions: List[str] = Field(default_list=[], description="Actionable courses or resources to close the skill gap.")
    certification_suggestions: List[str] = Field(default_list=[], description="Key certifications favored by hiring managers.")


class ExperienceMatchResult(BaseModel):
    years_match: bool = Field(..., description="True if years of experience satisfy requirements.")
    relevant_match: bool = Field(..., description="True if role history matches target profile scope.")
    domain_match: bool = Field(..., description="True if the candidate has background in this industry sector.")
    project_match: bool = Field(..., description="True if project descriptions align with JD accomplishments.")
    candidate_years: float = Field(..., description="Total extracted years of work history.")
    required_years: float = Field(..., description="Estimated required years based on JD.")


class EducationMatchResult(BaseModel):
    degree_match: bool = Field(..., description="True if candidate holds the minimum required academic level.")
    major_match: bool = Field(..., description="True if candidate's field of study aligns with target domain.")
    required_education: str = Field(..., description="Required academic qualifications (e.g., Bachelor's Degree).")
    candidate_education: List[str] = Field(default_list=[], description="Extracted academic credentials.")


class LocationMatchResult(BaseModel):
    remote_match: bool = Field(..., description="True if workplace preferences are compatible (Remote/Hybrid/Onsite).")
    preferred_match: bool = Field(..., description="True if location overlaps preferred locations.")
    relocation_needed: bool = Field(..., description="True if candidate is onsite/hybrid but in a different city and has not specified relocation willingness.")
    workplace_setting: str = Field(..., description="Desired setting specified by the JD (e.g., Hybrid).")


class VisaMatchResult(BaseModel):
    sponsorship_match: bool = Field(..., description="True if candidate does not need sponsorship, or if company provides it.")
    work_auth_match: bool = Field(..., description="True if work authorization matches requirements.")
    sponsorship_required_by_candidate: bool = Field(..., description="True if the candidate requires visa sponsorship.")
    sponsorship_offered_by_company: bool = Field(..., description="True if the company offers visa sponsorship.")


class SalaryMatchResult(BaseModel):
    salary_match_score: float = Field(..., description="Score showing alignment of salary expectations with budget.")
    market_salary_range: str = Field(..., description="Estimated market compensation range for this position.")
    salary_match_notes: str = Field(..., description="Detailed evaluation of compensation compatibility.")


class AIRecommendations(BaseModel):
    resume_improvements: List[str] = Field(default_list=[], description="Suggested structural/context revisions for the resume.")
    skills_to_add: List[str] = Field(default_list=[], description="Target high-frequency keywords to integrate.")
    projects_to_add: List[str] = Field(default_list=[], description="Recommended project focus areas to showcase skill application.")
    keywords_to_add: List[str] = Field(default_list=[], description="ATS buzzwords missing from descriptions.")
    certifications: List[str] = Field(default_list=[], description="Top industry credentials matching this role.")


class ExplainabilityResult(BaseModel):
    why_matched: str = Field(..., description="Detailed prose explanation of why the candidate is a fit.")
    why_not_matched: str = Field(..., description="Detailed prose explanation of what prevents a higher score.")
    strengths: List[str] = Field(default_list=[], description="Core strengths demonstrated by the candidate's profile.")
    weaknesses: List[str] = Field(default_list=[], description="Functional gaps or weaknesses detected relative to the job.")


class MatchingReportResponse(BaseModel):
    id: uuid.UUID = Field(..., description="Unique ID for the persisted match report.")
    resume_id: uuid.UUID = Field(..., description="The ID of the evaluated resume.")
    job_id: Optional[uuid.UUID] = Field(None, description="The ID of the job description (if saved in DB).")
    job_title: str = Field(..., description="Target job title.")
    company_name: Optional[str] = Field(None, description="Target company name.")
    match_score_breakdown: MatchingScoreBreakdown = Field(..., description="Scoring metrics category breakdown.")
    skill_gap_analysis: SkillGapAnalysis = Field(..., description="Skill gap and learning suggestions.")
    experience_matching: ExperienceMatchResult = Field(..., description="Work history scope alignment.")
    education_matching: EducationMatchResult = Field(..., description="Academic credential validation.")
    location_matching: LocationMatchResult = Field(..., description="Geographical setup compatibilities.")
    visa_matching: VisaMatchResult = Field(..., description="Immigration status & work permission matching.")
    salary_analysis: SalaryMatchResult = Field(..., description="Compensation package alignment.")
    ai_recommendations: AIRecommendations = Field(..., description="Targeted improvements and learning plans.")
    explainability: ExplainabilityResult = Field(..., description="Context prose explaining strengths/weaknesses.")


class MatchHistoryItem(BaseModel):
    id: uuid.UUID = Field(..., description="Unique ID of the saved match report.")
    resume_id: uuid.UUID = Field(..., description="Associated Resume ID.")
    job_title: str = Field(..., description="Evaluated Job Title.")
    company_name: Optional[str] = Field(None, description="Target Company Name.")
    overall_match: float = Field(..., description="Stored overall match score.")
    created_at: Any = Field(..., description="Timestamp of the analysis.")
