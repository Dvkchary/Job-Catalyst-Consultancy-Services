import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ==============================================================================
# 1. Resume Builder Detail Subschemas
# ==============================================================================

class PersonalInfoSchema(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=30)
    website: Optional[str] = Field(None, max_length=255)
    linkedin: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=255)
    summary: Optional[str] = Field(None, max_length=3000)
    job_title: Optional[str] = Field(None, max_length=255)


class ResumeEducationSchema(BaseModel):
    school: str = Field(..., max_length=255)
    degree: str = Field(..., max_length=100)
    field_of_study: str = Field(..., max_length=255)
    start_date: str = Field(..., description="Start Date (YYYY-MM or YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End Date. Null if ongoing")
    description: Optional[str] = Field(None, max_length=2000)


class ResumeExperienceSchema(BaseModel):
    company: str = Field(..., max_length=255)
    title: str = Field(..., max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    start_date: str = Field(..., description="Start Date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End Date. Null if current role")
    current: bool = Field(False)
    description: Optional[str] = Field(None, max_length=4000)


class ProjectSchema(BaseModel):
    name: str = Field(..., max_length=255)
    role: Optional[str] = Field(None, max_length=100)
    start_date: Optional[str] = Field(None)
    end_date: Optional[str] = Field(None)
    url: Optional[str] = Field(None, max_length=512)
    description: Optional[str] = Field(None, max_length=4000)
    technologies: List[str] = Field(default_factory=list)


class ResumeSkillSchema(BaseModel):
    name: str = Field(..., max_length=100)
    level: str = Field("INTERMEDIATE", description="BEGINNER, INTERMEDIATE, EXPERT")
    category: Optional[str] = Field(None, max_length=100)


class ResumeCertificationSchema(BaseModel):
    name: str = Field(..., max_length=255)
    issuer: str = Field(..., max_length=255)
    issue_date: Optional[str] = Field(None)
    expiration_date: Optional[str] = Field(None)
    credential_id: Optional[str] = Field(None, max_length=100)
    credential_url: Optional[str] = Field(None, max_length=512)


class AwardSchema(BaseModel):
    title: str = Field(..., max_length=255)
    issuer: str = Field(..., max_length=255)
    date: Optional[str] = Field(None)
    description: Optional[str] = Field(None, max_length=2000)


class ResumeLanguageSchema(BaseModel):
    language: str = Field(..., max_length=100)
    proficiency: str = Field("PROFICIENT", description="NATIVE, FLUENT, PROFICIENT, ELEMENTARY")


class VolunteerSchema(BaseModel):
    organization: str = Field(..., max_length=255)
    role: str = Field(..., max_length=100)
    start_date: Optional[str] = Field(None)
    end_date: Optional[str] = Field(None)
    description: Optional[str] = Field(None, max_length=2000)


class PublicationSchema(BaseModel):
    title: str = Field(..., max_length=255)
    publisher: Optional[str] = Field(None, max_length=255)
    date: Optional[str] = Field(None)
    url: Optional[str] = Field(None, max_length=512)
    description: Optional[str] = Field(None, max_length=2000)


class ReferenceSchema(BaseModel):
    name: str = Field(..., max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None)
    phone: Optional[str] = Field(None)
    relationship: Optional[str] = Field(None, max_length=255)
    text: Optional[str] = Field(None, max_length=2000)


class CustomSectionFieldSchema(BaseModel):
    label: str = Field(..., max_length=100)
    value: str = Field(..., max_length=1000)


class CustomSectionSchema(BaseModel):
    section_title: str = Field(..., max_length=255)
    fields: List[CustomSectionFieldSchema] = Field(default_factory=list)


# ==============================================================================
# 2. Main Nested Resume Content Schema
# ==============================================================================

class ResumeContentSchema(BaseModel):
    personal_info: Optional[PersonalInfoSchema] = Field(default_factory=PersonalInfoSchema)
    education: List[ResumeEducationSchema] = Field(default_factory=list)
    experience: List[ResumeExperienceSchema] = Field(default_factory=list)
    projects: List[ProjectSchema] = Field(default_factory=list)
    skills: List[ResumeSkillSchema] = Field(default_factory=list)
    certifications: List[ResumeCertificationSchema] = Field(default_factory=list)
    awards: List[AwardSchema] = Field(default_factory=list)
    languages: List[ResumeLanguageSchema] = Field(default_factory=list)
    volunteer: List[VolunteerSchema] = Field(default_factory=list)
    publications: List[PublicationSchema] = Field(default_factory=list)
    references: List[ReferenceSchema] = Field(default_factory=list)
    custom_sections: List[CustomSectionSchema] = Field(default_factory=list)
    section_ordering: List[str] = Field(
        default_factory=lambda: [
            "personal_info", "experience", "education", "projects", "skills",
            "certifications", "awards", "languages", "volunteer", "publications", "references"
        ]
    )


# ==============================================================================
# 3. Resume CRUD Schemas
# ==============================================================================

class ResumeCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    template_code: Optional[str] = Field(None, max_length=50)
    language: str = Field("en", max_length=10)
    visibility: str = Field("PRIVATE", max_length=50)  # PUBLIC, PRIVATE
    content: Optional[ResumeContentSchema] = Field(default_factory=ResumeContentSchema)


class ResumeUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, max_length=50)
    is_primary: Optional[bool] = None
    template_code: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    visibility: Optional[str] = Field(None, max_length=50)
    content: Optional[ResumeContentSchema] = None


class ResumeOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: str
    is_primary: bool
    resume_version: int
    template_code: Optional[str] = None
    language: str
    visibility: str
    content: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# 4. Resume Versioning Schemas
# ==============================================================================

class ResumeVersionOut(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    version_number: int
    title: str
    description: Optional[str] = None
    content_snapshot: Dict[str, Any]
    metadata_snapshot: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeCompareResponse(BaseModel):
    version_a: int
    version_b: int
    diff: Dict[str, Any]


# ==============================================================================
# 5. Resume Template Schemas
# ==============================================================================

class ResumeTemplateCreate(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    category: str = Field("Standard", max_length=50)
    layout_config: Dict[str, Any] = Field(default_factory=dict)


class ResumeTemplateOut(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    description: Optional[str] = None
    category: str
    layout_config: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# 6. Resume Parser Schemas
# ==============================================================================

class ParsedEducation(BaseModel):
    school: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ParsedExperience(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class ParsedResumeResponse(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    education: List[ParsedEducation] = Field(default_factory=list)
    experience: List[ParsedExperience] = Field(default_factory=list)
    raw_text: str = Field(..., description="Complete extracted plaintext format of document")
