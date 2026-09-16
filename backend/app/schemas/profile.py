import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field


# ==============================================================================
# 1. User Profile Detail Subschemas
# ==============================================================================

class EducationSchema(BaseModel):
    school: str = Field(..., description="Name of the educational institution")
    degree: str = Field(..., description="Degree type (e.g., Bachelor, Master, PhD)")
    field_of_study: str = Field(..., description="Major field of study")
    start_date: str = Field(..., description="Start date format (YYYY-MM or YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date format (YYYY-MM or YYYY-MM-DD). Null if ongoing")
    description: Optional[str] = Field(None, max_length=1000, description="Brief details of academic focus")


class ExperienceSchema(BaseModel):
    company: str = Field(..., description="Name of the employing company")
    title: str = Field(..., description="Job role or title")
    location: Optional[str] = Field(None, description="Physical location of employment")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD). Null if current role")
    current: bool = Field(False, description="Is this your current employer?")
    description: Optional[str] = Field(None, max_length=2000, description="Details of tasks and accomplishments")


class CertificationSchema(BaseModel):
    name: str = Field(..., description="Name of the certification credential")
    issuer: str = Field(..., description="Issuing authority or platform")
    issue_date: Optional[str] = Field(None, description="Issuance date (YYYY-MM-DD)")
    expiration_date: Optional[str] = Field(None, description="Expiration date (YYYY-MM-DD) if applicable")
    credential_id: Optional[str] = Field(None, description="Unique certification/credential ID")
    credential_url: Optional[str] = Field(None, description="Verification hyperlink URL")


class SocialLinksSchema(BaseModel):
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    github: Optional[str] = Field(None, description="GitHub profile URL")
    portfolio: Optional[str] = Field(None, description="Personal portfolio website URL")
    twitter: Optional[str] = Field(None, description="Twitter/X profile URL")


class PreferredSalarySchema(BaseModel):
    min_salary: Optional[float] = Field(None, description="Minimum acceptable salary limit")
    max_salary: Optional[float] = Field(None, description="Maximum targeted salary limit")
    currency: str = Field("USD", description="Currency standard code (e.g. USD, EUR, GBP)")
    rate_type: str = Field("YEARLY", description="Rate frequency indicator (YEARLY, MONTHLY, HOURLY)")


class WorkAuthorizationSchema(BaseModel):
    visa_status: str = Field(..., description="Current status (e.g., Citizen, Green Card, H1B, F1, OPT, STEM OPT)")
    needs_sponsorship: bool = Field(False, description="Whether sponsorship is required for future employment")
    opt_stem_opt: Optional[bool] = Field(None, description="Whether user qualifies for standard or STEM OPT extensions")


class AvailabilitySchema(BaseModel):
    start_date: Optional[str] = Field(None, description="Target availability date")
    notice_period: Optional[str] = Field(None, description="Notice period (e.g., Immediate, 2 weeks, 1 month)")
    employment_type: str = Field("FULL_TIME", description="Preferred model (FULL_TIME, CONTRACT, PART_TIME, INTERN)")


class LanguageProficiencySchema(BaseModel):
    language: str = Field(..., description="Language name (e.g., English, Spanish)")
    proficiency: str = Field("PROFICIENT", description="Skill rating (NATIVE, FLUENT, PROFICIENT, ELEMENTARY)")


# ==============================================================================
# 2. Main User Profile Creation & Update Schemas
# ==============================================================================

class UserProfileCreate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=30)
    headline: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = Field(None, max_length=2000)
    
    skills: List[str] = Field(default_factory=list)
    education: List[EducationSchema] = Field(default_factory=list)
    experience: List[ExperienceSchema] = Field(default_factory=list)
    certifications: List[CertificationSchema] = Field(default_factory=list)
    social_links: SocialLinksSchema = Field(default_factory=SocialLinksSchema)
    
    preferred_job_locations: List[str] = Field(default_factory=list)
    preferred_roles: List[str] = Field(default_factory=list)
    preferred_salary: PreferredSalarySchema = Field(default_factory=PreferredSalarySchema)
    
    work_authorization: WorkAuthorizationSchema = Field(
        default_factory=lambda: WorkAuthorizationSchema(visa_status="Citizen", needs_sponsorship=False)
    )
    availability: AvailabilitySchema = Field(default_factory=AvailabilitySchema)
    timezone: str = Field("UTC", max_length=100)
    languages: List[LanguageProficiencySchema] = Field(default_factory=list)


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=30)
    headline: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = Field(None, max_length=2000)
    
    skills: Optional[List[str]] = None
    education: Optional[List[EducationSchema]] = None
    experience: Optional[List[ExperienceSchema]] = None
    certifications: Optional[List[CertificationSchema]] = None
    social_links: Optional[SocialLinksSchema] = None
    
    preferred_job_locations: Optional[List[str]] = None
    preferred_roles: Optional[List[str]] = None
    preferred_salary: Optional[PreferredSalarySchema] = None
    
    work_authorization: Optional[WorkAuthorizationSchema] = None
    availability: Optional[AvailabilitySchema] = None
    timezone: Optional[str] = Field(None, max_length=100)
    languages: Optional[List[LanguageProficiencySchema]] = None


class UserProfileOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    
    skills: List[str] = []
    education: List[Dict[str, Any]] = []
    experience: List[Dict[str, Any]] = []
    certifications: List[Dict[str, Any]] = []
    social_links: Dict[str, str] = {}
    
    preferred_job_locations: List[str] = []
    preferred_roles: List[str] = []
    preferred_salary: Dict[str, Any] = {}
    
    work_authorization: Dict[str, Any] = {}
    availability: Dict[str, Any] = {}
    timezone: Optional[str] = "UTC"
    languages: List[Dict[str, Any]] = []
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# 3. Account Settings Schemas
# ==============================================================================

class NotificationPreferencesSchema(BaseModel):
    email_alerts: bool = Field(True, description="Enable automated matches email alert bulletins")
    marketing_emails: bool = Field(False, description="Enable occasional product newsletters")
    push_notifications: bool = Field(True, description="Enable instant web browser push notes")


class PrivacySettingsSchema(BaseModel):
    profile_visibility: str = Field("PUBLIC", description="Visibility status: PUBLIC, PRIVATE, or RECRUITERS_ONLY")
    search_index_allowed: bool = Field(True, description="Allow external search engines to index profile")
    anonymous_mode: bool = Field(False, description="Hide real name/avatar and only present professional criteria")


class SecurityPreferencesSchema(BaseModel):
    mfa_required: bool = Field(False, description="Mandate Multi-Factor Authenticator check at login")
    session_timeout_minutes: int = Field(60, description="Auto-expire inactive sessions after specified minutes")


class AccountSettingsUpdate(BaseModel):
    theme: Optional[str] = Field(None, max_length=50, description="Display style: light, dark, system")
    language: Optional[str] = Field(None, max_length=10, description="Standard locale (en, es, etc.)")
    notification_preferences: Optional[NotificationPreferencesSchema] = None
    privacy_settings: Optional[PrivacySettingsSchema] = None
    security_preferences: Optional[SecurityPreferencesSchema] = None


class AccountSettingsOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    theme: str
    language: str
    notification_preferences: Dict[str, bool]
    privacy_settings: Dict[str, Any]
    security_preferences: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# 4. Profile Completion Engine Schemas
# ==============================================================================

class ProfileCompletionRecommendation(BaseModel):
    section: str = Field(..., description="Target section needing detail (e.g. experience, certifications)")
    priority: str = Field(..., description="Action priority (HIGH, MEDIUM, LOW)")
    tip: str = Field(..., description="Actionable recommendation description to improve completion percentage")


class ProfileCompletionStatus(BaseModel):
    completion_percentage: int = Field(..., description="Aggregate user profile completion rate (0-100%)")
    missing_fields: List[str] = Field(..., description="Detailed collection of attributes currently unpopulated")
    recommendations: List[ProfileCompletionRecommendation] = Field(..., description="Helpful tips to improve the profile strength")


# ==============================================================================
# 5. Avatar Action Schemas
# ==============================================================================

class AvatarActionResponse(BaseModel):
    avatar_url: str = Field(..., description="Absolute verified location URL of updated avatar image")
    status: str = Field("success", description="Status string indicating success or failure")


class AvatarCropSchema(BaseModel):
    x: int = Field(0, description="Horizontal top-left pixel offset")
    y: int = Field(0, description="Vertical top-left pixel offset")
    width: int = Field(..., description="Target cropped image width")
    height: int = Field(..., description="Target cropped image height")


# ==============================================================================
# 6. Profile Search Schemas
# ==============================================================================

class ProfileSearchQuery(BaseModel):
    skills: Optional[List[str]] = None
    roles: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    limit: int = Field(20, ge=1, le=100)
    skip: int = Field(0, ge=0)


class ProfileSearchResponse(BaseModel):
    results: List[UserProfileOut]
    total_count: int
    limit: int
    skip: int
