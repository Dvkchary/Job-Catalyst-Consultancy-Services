import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =====================================================================
# SYSTEM OVERVIEW / DASHBOARD SCHEMAS
# =====================================================================

class SystemHealthDetails(BaseModel):
    status: str = "healthy"  # healthy, degraded, down
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    db_connected: bool = True
    redis_connected: bool = True
    queue_backlog: int = 0
    active_workers: int = 2


class RecentActivityItem(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    username: Optional[str] = "System"
    category: str
    action: str
    description: str
    timestamp: datetime


class AdminDashboardOverviewResponse(BaseModel):
    total_users: int
    active_users_last_24h: int
    active_sessions: int
    total_revenue_usd: float
    total_ai_tokens_used: int
    total_ai_cost_usd: float
    system_health: SystemHealthDetails
    recent_activities: List[RecentActivityItem]


# =====================================================================
# USER MANAGEMENT SCHEMAS
# =====================================================================

class AdminUserUpdatePayload(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = Field(None, description="ACTIVE, PENDING, LOCKED, SUSPENDED")
    email_verified: Optional[bool] = None


class AdminUserResetPasswordPayload(BaseModel):
    new_password: str = Field(..., min_length=8)


class AdminUserRoleAssignmentPayload(BaseModel):
    role_names: List[str] = Field(..., description="List of role names to assign in bulk.")


class AdminUserDetailResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    status: str
    email_verified: bool
    last_login: Optional[datetime] = None
    failed_login_attempts: int
    roles: List[str]
    created_at: Any
    updated_at: Any

    class Config:
        from_attributes = True


# =====================================================================
# RBAC SCHEMAS
# =====================================================================

class PermissionResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    permissions: List[PermissionResponse]

    class Config:
        from_attributes = True


class RolePermissionMatrixResponse(BaseModel):
    roles: List[RoleResponse]
    all_permissions: List[PermissionResponse]


# =====================================================================
# AI CONFIGURATION SCHEMAS
# =====================================================================

class AIProviderSettingsUpdate(BaseModel):
    provider_name: str = "google"
    api_key_masked: Optional[str] = None
    default_model: str = "gemini-2.5-flash"
    fallback_model: str = "gemini-1.5-pro"
    max_tokens_per_request: int = 4096
    temperature: float = 0.7
    timeout_seconds: int = 30


class AIUsageCostAnalytics(BaseModel):
    total_tokens: int
    estimated_cost_usd: float
    success_rate: float
    avg_latency_ms: float


class AISystemStatus(BaseModel):
    provider: str
    status: str  # healthy, warning, offline
    api_key_configured: bool
    latency_ms: float
    fallback_active: bool
    usage_stats: AIUsageCostAnalytics


# =====================================================================
# JOB SOURCE SCHEMAS
# =====================================================================

class JobSourceUpdatePayload(BaseModel):
    is_enabled: Optional[bool] = None
    plugin_name: Optional[str] = None


class JobSourceResponse(BaseModel):
    id: uuid.UUID
    name: str
    plugin_name: str
    is_enabled: bool
    last_imported_at: Optional[datetime] = None
    import_status: str
    import_metadata: Dict[str, Any]

    class Config:
        from_attributes = True


# =====================================================================
# RESUME TEMPLATE SCHEMAS
# =====================================================================

class ResumeTemplateCreatePayload(BaseModel):
    name: str
    category: str = "Professional"
    template_content: Dict[str, Any] = Field(default_factory=dict)
    is_published: bool = True
    description: Optional[str] = None


class ResumeTemplateUpdatePayload(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    template_content: Optional[Dict[str, Any]] = None
    is_published: Optional[bool] = None
    description: Optional[str] = None


class ResumeTemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    category: str
    template_content: Dict[str, Any]
    is_published: bool
    description: Optional[str]

    class Config:
        from_attributes = True


# =====================================================================
# SYSTEM CONFIGURATION SCHEMAS
# =====================================================================

class SystemConfigurationUpdatePayload(BaseModel):
    category: str
    config_value: Dict[str, Any]
    description: Optional[str] = None
    is_secret: bool = False


class SystemConfigurationResponse(BaseModel):
    id: uuid.UUID
    config_key: str
    category: str
    config_value: Dict[str, Any]
    description: Optional[str]
    is_secret: bool

    class Config:
        from_attributes = True


# =====================================================================
# FEATURE FLAG SCHEMAS
# =====================================================================

class FeatureFlagCreatePayload(BaseModel):
    name: str
    description: Optional[str] = None
    is_enabled: bool = False
    rollout_percentage: float = 100.0


class FeatureFlagUpdatePayload(BaseModel):
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    rollout_percentage: Optional[float] = None


class FeatureFlagResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    is_enabled: bool
    rollout_percentage: float

    class Config:
        from_attributes = True


# =====================================================================
# AUDIT LOG SCHEMAS
# =====================================================================

class AuditLogQueryRequest(BaseModel):
    category: Optional[str] = None
    action: Optional[str] = None
    user_id: Optional[uuid.UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    category: str
    action: str
    description: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    context_data: Dict[str, Any]
    created_at: Any

    class Config:
        from_attributes = True
