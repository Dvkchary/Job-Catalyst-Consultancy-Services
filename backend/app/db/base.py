# ==============================================================================
# JobCatalyst AI - Global Database Model Manifest Registry
# ==============================================================================
# This file is used by Alembic to discover all registered declarative tables on 
# the MetaData. We import all database models here so Alembic can safely autogenerate
# migrations. Note: As domain models are added in Module 4+, they MUST be imported here.

from app.db.base_class import Base
from app.db.base_models import DatabaseModelMixin
from app.models.auth import User, Role, Permission, UserSession, TokenRevocation, user_roles, role_permissions
from app.models.profile import UserProfile, AccountSettings
from app.models.resume import Resume, ResumeTemplate, ResumeVersion
from app.models.ats import ATSReport
from app.models.job import Company, Job, SavedJob, SavedSearch, SearchHistory
from app.models.interview import InterviewSession, InterviewQuestion
from app.models.career import CareerProfile, CareerRoadmap, CareerRecommendation
from app.models.workflow import Workflow, WorkflowExecution, WorkflowTemplate, WorkflowLog
from app.models.career_os import (
    AICareerAssistantSession, AICareerAssistantMessage, CareerMemory,
    CareerGoal, CareerHabit, CareerTimelineEvent, CareerDocument, AIWorkspaceProject
)

# Export schemas for unified access
__all__ = [
    "Base",
    "DatabaseModelMixin",
    "User",
    "Role",
    "Permission",
    "UserSession",
    "TokenRevocation",
    "UserProfile",
    "AccountSettings",
    "Resume",
    "ResumeTemplate",
    "ResumeVersion",
    "ATSReport",
    "Company",
    "Job",
    "SavedJob",
    "SavedSearch",
    "SearchHistory",
    "InterviewSession",
    "InterviewQuestion",
    "CareerProfile",
    "CareerRoadmap",
    "CareerRecommendation",
    "Workflow",
    "WorkflowExecution",
    "WorkflowTemplate",
    "WorkflowLog",
    "AICareerAssistantSession",
    "AICareerAssistantMessage",
    "CareerMemory",
    "CareerGoal",
    "CareerHabit",
    "CareerTimelineEvent",
    "CareerDocument",
    "AIWorkspaceProject",
]

