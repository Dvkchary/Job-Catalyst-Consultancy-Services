import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CareerProfileCreate(BaseModel):
    current_role: str = Field(..., description="Current job title.")
    target_role: str = Field(..., description="Desired target job title.")
    industry: str = Field(..., description="The industry/vertical, e.g. Fintech, Healthcare, Cloud Services.")
    experience_level: str = Field("Mid", description="Junior, Mid, Senior, Lead, Executive.")
    skills: List[str] = Field(default_factory=list, description="List of existing skills.")
    career_goals: List[str] = Field(default_factory=list, description="Immediate and long-term targets.")
    preferred_countries: List[str] = Field(default_factory=list, description="Target geographical regions.")
    visa_status: str = Field("Not Required", description="Work visa sponsorship requirements, e.g., H1B, Green Card, etc.")
    timeline: str = Field("6 Months", description="Target timeframe to achieve target role.")


class SalaryIntelligence(BaseModel):
    current_salary: float = Field(..., description="Current compensation.")
    market_salary: float = Field(..., description="Estimated market rate average.")
    expected_salary: float = Field(..., description="Target compensation.")
    negotiation_advice: str = Field(..., description="AI generated guidance for interview compensation rounds.")
    salary_trend: str = Field(..., description="Visual description of compensation curves inside target vertical.")


class CareerInsights(BaseModel):
    promotion_readiness: float = Field(..., description="Percentage indicating promotion alignment (1-100).")
    resume_readiness: float = Field(..., description="Percentage indicating resume alignment with target role (1-100).")
    interview_readiness: float = Field(..., description="Percentage indicating mock interview performance readiness (1-100).")
    application_readiness: float = Field(..., description="Percentage indicating overall job application readiness (1-100).")
    career_score: float = Field(..., description="Weighted composite rating (1-100).")


class CareerProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    current_role: str
    target_role: str
    industry: str
    experience_level: str
    skills: List[str]
    career_goals: List[str]
    preferred_countries: List[str]
    visa_status: str
    timeline: str
    career_score: float
    salary_intelligence: SalaryIntelligence
    readiness_insights: CareerInsights
    created_at: Any
    updated_at: Any

    class Config:
        from_attributes = True


class MilestoneItem(BaseModel):
    title: str = Field(..., description="Name of the milestone.")
    description: str = Field(..., description="Steps or context.")
    is_completed: bool = Field(False, description="Whether milestone is met.")
    target_date: Optional[str] = Field(None, description="ISO format or relative timeframe.")


class CareerRoadmapSection(BaseModel):
    goals: List[str] = Field(default_factory=list, description="List of high-level objectives.")
    milestones: List[MilestoneItem] = Field(default_factory=list, description="Milestones inside this timeline bracket.")


class CareerRoadmapData(BaseModel):
    short_term: CareerRoadmapSection = Field(..., description="0-6 Months actions.")
    medium_term: CareerRoadmapSection = Field(..., description="6-18 Months actions.")
    long_term: CareerRoadmapSection = Field(..., description="18+ Months actions.")


class GoalItem(BaseModel):
    id: str = Field(..., description="Unique ID for goal item.")
    title: str = Field(..., description="Action title.")
    is_completed: bool = Field(False, description="Completion status.")
    category: str = Field("Skill Acquisition", description="E.g., Skill Acquisition, Networking, Interview.")


class UpdateGoalsRequest(BaseModel):
    weekly_goals: Optional[List[GoalItem]] = None
    monthly_goals: Optional[List[GoalItem]] = None


class CareerRoadmapResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    career_profile_id: uuid.UUID
    roadmap_data: CareerRoadmapData
    weekly_goals: List[GoalItem] = Field(default_factory=list)
    monthly_goals: List[GoalItem] = Field(default_factory=list)
    learning_progress: Dict[str, Any] = Field(default_factory=dict)
    created_at: Any
    updated_at: Any

    class Config:
        from_attributes = True


class SkillGapItem(BaseModel):
    skill_name: str = Field(..., description="The name of the skill.")
    priority_ranking: str = Field("High", description="High, Medium, Low prioritization.")
    learning_difficulty: str = Field("Medium", description="Easy, Medium, Hard learning difficulty.")
    learning_time_estimate: str = Field("2 Weeks", description="Estimated learning time.")


class RecommendationCourse(BaseModel):
    title: str
    provider: str
    url: Optional[str] = None


class RecommendationCertification(BaseModel):
    name: str
    issuing_organization: str
    relevance_score: float


class RecommendationProject(BaseModel):
    title: str
    description: str
    key_technologies: List[str]


class LearningRecommendations(BaseModel):
    courses: List[RecommendationCourse] = Field(default_factory=list)
    certifications: List[RecommendationCertification] = Field(default_factory=list)
    books: List[str] = Field(default_factory=list)
    projects: List[RecommendationProject] = Field(default_factory=list)
    open_source_contributions: List[str] = Field(default_factory=list)
    practice_platforms: List[str] = Field(default_factory=list)


class AIRecommendationsResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    career_profile_id: uuid.UUID
    next_best_action: str = Field(..., description="Actionable recommended immediate next step.")
    skill_gap_analysis: List[SkillGapItem] = Field(default_factory=list)
    learning_recommendations: LearningRecommendations
    resume_improvements: List[str] = Field(default_factory=list)
    interview_practice_suggestions: List[str] = Field(default_factory=list)
    job_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: Any
    updated_at: Any

    class Config:
        from_attributes = True


class ProgressTrackingResponse(BaseModel):
    learning_progress: Dict[str, Any] = Field(..., description="Aggregate course/project/skill metrics.")
    applications_count: int = Field(..., description="Total tracked applications count from ATS.")
    interviews_count: int = Field(..., description="Total mock/actual interviews.")
    offers_count: int = Field(..., description="Tracked job offers received.")
    career_growth_percentage: float = Field(..., description="Progression percentage indicating delta metric.")
