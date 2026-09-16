import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


# ==============================================================================
# 1. Company Schemas
# ==============================================================================

class CompanyBase(BaseModel):
    name: str = Field(..., max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=255)
    size: Optional[str] = Field(None, max_length=50)  # e.g. "10-50", "1000+"
    logo_url: Optional[str] = Field(None, max_length=500)
    rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    locations: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=255)
    size: Optional[str] = Field(None, max_length=50)
    logo_url: Optional[str] = Field(None, max_length=500)
    rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    locations: Optional[List[str]] = None
    description: Optional[str] = None


class CompanyOut(CompanyBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# 2. Job Schemas
# ==============================================================================

class JobBase(BaseModel):
    company_name: str = Field(..., max_length=255)
    title: str = Field(..., max_length=255)
    location: str = Field(..., max_length=255)
    employment_type: str = Field("Full-time", max_length=50)  # Full-time, Part-time, Contract, etc.
    salary_min: Optional[float] = Field(None, ge=0.0)
    salary_max: Optional[float] = Field(None, ge=0.0)
    currency: str = Field("USD", max_length=10)
    experience_level: str = Field("Mid-level", max_length=50)  # Entry, Mid-level, Senior, Executive
    remote_status: str = Field("Onsite", max_length=50)  # Remote, Hybrid, Onsite
    visa_sponsorship: bool = Field(False)
    work_authorization: Optional[str] = Field(None, max_length=255)
    expires_at: Optional[datetime] = None
    skills: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    description: str
    url: Optional[str] = Field(None, max_length=500)
    source: str = Field(..., max_length=50)  # LinkedIn, Indeed, Glassdoor, Greenhouse, etc.
    source_id: Optional[str] = Field(None, max_length=100)


class JobCreate(JobBase):
    company_id: Optional[uuid.UUID] = None


class JobUpdate(BaseModel):
    company_id: Optional[uuid.UUID] = None
    company_name: Optional[str] = Field(None, max_length=255)
    title: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    employment_type: Optional[str] = Field(None, max_length=50)
    salary_min: Optional[float] = Field(None, ge=0.0)
    salary_max: Optional[float] = Field(None, ge=0.0)
    currency: Optional[str] = Field(None, max_length=10)
    experience_level: Optional[str] = Field(None, max_length=50)
    remote_status: Optional[str] = Field(None, max_length=50)
    visa_sponsorship: Optional[bool] = None
    work_authorization: Optional[str] = Field(None, max_length=255)
    expires_at: Optional[datetime] = None
    skills: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    description: Optional[str] = None
    url: Optional[str] = Field(None, max_length=500)
    source: Optional[str] = Field(None, max_length=50)
    source_id: Optional[str] = Field(None, max_length=100)


class JobOut(JobBase):
    id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    posted_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# 3. Saved Job / Bookmark Schemas
# ==============================================================================

class SavedJobCreate(BaseModel):
    job_id: uuid.UUID
    folder: str = Field("Favorites", max_length=100)


class SavedJobOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    folder: str
    job: JobOut
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# 4. Saved Search Schemas
# ==============================================================================

class SavedSearchCreate(BaseModel):
    name: str = Field(..., max_length=100)
    query_params: Dict[str, Any] = Field(default_factory=dict)
    notifications_enabled: bool = Field(False)


class SavedSearchUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    query_params: Optional[Dict[str, Any]] = None
    notifications_enabled: Optional[bool] = None


class SavedSearchOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    query_params: Dict[str, Any]
    notifications_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# 5. Search History Schemas
# ==============================================================================

class SearchHistoryCreate(BaseModel):
    query: str = Field(..., max_length=255)
    filters: Dict[str, Any] = Field(default_factory=dict)


class SearchHistoryOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    query: str
    filters: Dict[str, Any]
    timestamp: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# 6. Pagination & Search Results Wrapper
# ==============================================================================

class JobSearchResponse(BaseModel):
    items: List[JobOut]
    total: int
    skip: int
    limit: int
