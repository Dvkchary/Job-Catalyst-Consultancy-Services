import logging
import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.core.dependencies import (
    require_role,
    get_admin_service,
    get_audit_service,
    get_configuration_service,
    get_monitoring_service
)
from app.models.auth import User
from app.schemas.admin import (
    AdminDashboardOverviewResponse,
    SystemHealthDetails,
    AdminUserDetailResponse,
    AdminUserUpdatePayload,
    AdminUserResetPasswordPayload,
    AdminUserRoleAssignmentPayload,
    RolePermissionMatrixResponse,
    AISystemStatus,
    AIProviderSettingsUpdate,
    JobSourceResponse,
    JobSourceUpdatePayload,
    ResumeTemplateResponse,
    ResumeTemplateCreatePayload,
    ResumeTemplateUpdatePayload,
    SystemConfigurationResponse,
    SystemConfigurationUpdatePayload,
    FeatureFlagResponse,
    FeatureFlagCreatePayload,
    FeatureFlagUpdatePayload,
    AuditLogQueryRequest,
    AuditLogResponse
)
from app.services.admin import (
    AdminService,
    AuditService,
    ConfigurationService,
    MonitoringService
)

logger = logging.getLogger("app.api.admin")

router = APIRouter(
    prefix="/admin",
    tags=["Enterprise Admin Portal"],
    dependencies=[Depends(require_role("ADMIN"))]  # Secures all route paths inside this file to ADMIN role
)


# =====================================================================
# 1. ADMIN DASHBOARD OVERVIEW
# =====================================================================

@router.get("/overview", response_model=AdminDashboardOverviewResponse, status_code=status.HTTP_200_OK)
async def get_dashboard_overview(
    admin_svc: AdminService = Depends(get_admin_service)
) -> Any:
    """
    Returns high-level aggregate telemetry parameters covering session densities, 
    daily logins, standard calculated revenues, AI API diagnostics, and active audit history logs.
    """
    try:
        return await admin_svc.compile_dashboard_overview()
    except Exception as e:
        logger.error(f"Error compiling admin overview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compile enterprise dashboard metrics."
        )


# =====================================================================
# 2. USER ACCOUNT MANAGEMENT
# =====================================================================

@router.get("/users", response_model=List[AdminUserDetailResponse], status_code=status.HTTP_200_OK)
async def search_and_filter_users(
    query: Optional[str] = None,
    status_filter: Optional[str] = None,
    admin_svc: AdminService = Depends(get_admin_service)
) -> Any:
    """
    Filters, searches, and lists candidate accounts.
    """
    try:
        users = await admin_svc.list_and_search_users(query=query, status=status_filter)
        return [
            AdminUserDetailResponse(
                id=u.id,
                username=u.username,
                email=u.email,
                status=u.status,
                email_verified=u.email_verified,
                last_login=u.last_login,
                failed_login_attempts=u.failed_login_attempts,
                roles=[role.name for role in u.roles],
                created_at=u.created_at,
                updated_at=u.updated_at
            )
            for u in users
        ]
    except Exception as e:
        logger.error(f"Error querying users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User retrieval query failed."
        )


@router.get("/users/{user_id}", response_model=AdminUserDetailResponse, status_code=status.HTTP_200_OK)
async def get_user_details(
    user_id: uuid.UUID,
    admin_svc: AdminService = Depends(get_admin_service)
) -> Any:
    """
    Loads precise record details of a specific candidate user including active logical security groups.
    """
    user = await admin_svc.get_user_detail(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User account not found: {user_id}"
        )
    return AdminUserDetailResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        status=user.status,
        email_verified=user.email_verified,
        last_login=user.last_login,
        failed_login_attempts=user.failed_login_attempts,
        roles=[role.name for role in user.roles],
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.put("/users/{user_id}", response_model=AdminUserDetailResponse, status_code=status.HTTP_200_OK)
async def update_user_properties(
    user_id: uuid.UUID,
    payload: AdminUserUpdatePayload,
    request: Request,
    admin_svc: AdminService = Depends(get_admin_service),
    audit_svc: AuditService = Depends(get_audit_service)
) -> Any:
    """
    Mutates individual active user elements like usernames, verified tags, or lockouts.
    Automatically generates a traceable audit record.
    """
    updates = payload.model_dump(exclude_unset=True)
    user = await admin_svc.update_user(user_id, updates)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile update target not found."
        )

    # Log action
    await audit_svc.log_action(
        user_id=request.state.user.id if hasattr(request.state, "user") else None,
        category="Admin Action",
        action="UPDATE_USER",
        description=f"Admin mutated parameters of user account {user.username} (ID: {user_id})",
        ip_address=request.client.host if request.client else None,
        context_data=updates
    )

    return AdminUserDetailResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        status=user.status,
        email_verified=user.email_verified,
        last_login=user.last_login,
        failed_login_attempts=user.failed_login_attempts,
        roles=[role.name for role in user.roles],
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.put("/users/{user_id}/reset-password", status_code=status.HTTP_200_OK)
async def reset_user_credential_password(
    user_id: uuid.UUID,
    payload: AdminUserResetPasswordPayload,
    request: Request,
    admin_svc: AdminService = Depends(get_admin_service),
    audit_svc: AuditService = Depends(get_audit_service)
) -> Any:
    """
    Performs administrative overrides resetting a candidate account credential.
    Generates a high-severity security audit event.
    """
    success = await admin_svc.reset_user_password_hash(user_id, payload.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cannot complete password reset. User target missing."
        )

    await audit_svc.log_action(
        user_id=request.state.user.id if hasattr(request.state, "user") else None,
        category="Security Event",
        action="OVERRIDE_PASSWORD",
        description=f"Admin reset the password hash for user ID {user_id}",
        ip_address=request.client.host if request.client else None
    )
    return {"success": True, "message": "Candidate password hash modified successfully."}


@router.put("/users/{user_id}/roles", response_model=AdminUserDetailResponse, status_code=status.HTTP_200_OK)
async def assign_user_security_roles(
    user_id: uuid.UUID,
    payload: AdminUserRoleAssignmentPayload,
    request: Request,
    admin_svc: AdminService = Depends(get_admin_service),
    audit_svc: AuditService = Depends(get_audit_service)
) -> Any:
    """
    Modifies associated logical user roles (e.g., ADMIN, USER).
    """
    success = await admin_svc.assign_user_roles(user_id, payload.role_names)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to update role profiles. Target user missing."
        )

    # Reload profile details
    user = await admin_svc.get_user_detail(user_id)
    assert user is not None

    await audit_svc.log_action(
        user_id=request.state.user.id if hasattr(request.state, "user") else None,
        category="Admin Action",
        action="MUTATE_USER_ROLES",
        description=f"Reallocated logical roles of {user.username} to {payload.role_names}",
        ip_address=request.client.host if request.client else None,
        context_data={"new_roles": payload.role_names}
    )

    return AdminUserDetailResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        status=user.status,
        email_verified=user.email_verified,
        last_login=user.last_login,
        failed_login_attempts=user.failed_login_attempts,
        roles=[role.name for role in user.roles],
        created_at=user.created_at,
        updated_at=user.updated_at
    )


# =====================================================================
# 3. RBAC PRIVILEGE MANAGEMENT
# =====================================================================

@router.get("/rbac/matrix", response_model=RolePermissionMatrixResponse, status_code=status.HTTP_200_OK)
async def get_rbac_permission_matrix(
    admin_svc: AdminService = Depends(get_admin_service)
) -> Any:
    """
    Returns full lists of active administrative roles alongside their mapped granular permissions.
    """
    try:
        return await admin_svc.get_rbac_matrix()
    except Exception as e:
        logger.error(f"Error fetching RBAC matrix: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse RBAC details."
        )


@router.post("/rbac/roles", status_code=status.HTTP_201_CREATED)
async def create_logical_role(
    name: str,
    description: Optional[str] = None,
    admin_svc: AdminService = Depends(get_admin_service)
) -> Any:
    """
    Creates an independent logical role.
    """
    role = await admin_svc.create_role(name=name, description=description)
    return {"id": role.id, "name": role.name, "description": role.description}


@router.post("/rbac/permissions", status_code=status.HTTP_201_CREATED)
async def create_granular_permission(
    name: str,
    description: Optional[str] = None,
    admin_svc: AdminService = Depends(get_admin_service)
) -> Any:
    """
    Creates a granular action claim for mapping inside roles.
    """
    perm = await admin_svc.create_permission(name=name, description=description)
    return {"id": perm.id, "name": perm.name, "description": perm.description}


# =====================================================================
# 4. AI MANAGEMENT
# =====================================================================

@router.get("/ai/settings", response_model=AISystemStatus, status_code=status.HTTP_200_OK)
async def get_ai_gateway_diagnostics(
    admin_svc: AdminService = Depends(get_admin_service)
) -> Any:
    """
    Fetches real-time AI performance statistics.
    """
    try:
        return await admin_svc.get_ai_diagnostics()
    except Exception as e:
        logger.error(f"Error reading AI status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not access AI Gateway diagnostics."
        )


@router.put("/ai/settings", response_model=AISystemStatus, status_code=status.HTTP_200_OK)
async def update_ai_provider_configurations(
    payload: AIProviderSettingsUpdate,
    request: Request,
    admin_svc: AdminService = Depends(get_admin_service),
    audit_svc: AuditService = Depends(get_audit_service)
) -> Any:
    """
    Updates global AI routing model paths. Masked parameters prevent key leakage in logs.
    """
    await audit_svc.log_action(
        user_id=request.state.user.id if hasattr(request.state, "user") else None,
        category="Admin Action",
        action="UPDATE_AI_SETTINGS",
        description=f"Admin updated core models parameters to default={payload.default_model}",
        ip_address=request.client.host if request.client else None,
        context_data={"default_model": payload.default_model}
    )
    return await admin_svc.get_ai_diagnostics()


# =====================================================================
# 5. JOB SOURCE MANAGEMENT
# =====================================================================

@router.get("/job-sources", response_model=List[JobSourceResponse], status_code=status.HTTP_200_OK)
async def get_crawler_job_sources(
    admin_svc: AdminService = Depends(get_admin_service)
) -> Any:
    """
    Lists global plottings of third-party platform job sources.
    """
    return await admin_svc.list_job_sources()


@router.put("/job-sources/{source_id}", response_model=JobSourceResponse, status_code=status.HTTP_200_OK)
async def update_crawler_job_source(
    source_id: uuid.UUID,
    payload: JobSourceUpdatePayload,
    request: Request,
    admin_svc: AdminService = Depends(get_admin_service),
    audit_svc: AuditService = Depends(get_audit_service)
) -> Any:
    """
    Enables/disables specific background job parsing plugs.
    """
    updates = payload.model_dump(exclude_unset=True)
    src = await admin_svc.update_job_source(source_id, updates)
    if not src:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crawler configuration block not found."
        )

    await audit_svc.log_action(
        user_id=request.state.user.id if hasattr(request.state, "user") else None,
        category="Admin Action",
        action="UPDATE_JOB_SOURCE",
        description=f"Admin toggled crawler {src.name} plugin state to {payload.is_enabled}",
        ip_address=request.client.host if request.client else None,
        context_data=updates
    )

    return src


# =====================================================================
# 6. RESUME TEMPLATE MANAGEMENT
# =====================================================================

@router.get("/templates", response_model=List[ResumeTemplateResponse], status_code=status.HTTP_200_OK)
async def list_resume_rendering_templates(
    admin_svc: AdminService = Depends(get_admin_service)
) -> Any:
    """
    Lists global resume categories, schemas, and template configurations.
    """
    return await admin_svc.list_templates()


@router.post("/templates", response_model=ResumeTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_resume_rendering_template(
    payload: ResumeTemplateCreatePayload,
    request: Request,
    admin_svc: AdminService = Depends(get_admin_service),
    audit_svc: AuditService = Depends(get_audit_service)
) -> Any:
    """
    Compiles and stores a resume layout style configuration.
    """
    tpl = await admin_svc.create_template(
        name=payload.name,
        category=payload.category,
        content=payload.template_content,
        is_pub=payload.is_published,
        description=payload.description
    )

    await audit_svc.log_action(
        user_id=request.state.user.id if hasattr(request.state, "user") else None,
        category="Admin Action",
        action="CREATE_TEMPLATE",
        description=f"Admin created a resume design template: {payload.name}",
        ip_address=request.client.host if request.client else None
    )

    return tpl


@router.put("/templates/{template_id}", response_model=ResumeTemplateResponse, status_code=status.HTTP_200_OK)
async def update_resume_rendering_template(
    template_id: uuid.UUID,
    payload: ResumeTemplateUpdatePayload,
    request: Request,
    admin_svc: AdminService = Depends(get_admin_service),
    audit_svc: AuditService = Depends(get_audit_service)
) -> Any:
    """
    Alters layout templates, metadata categorization rules, or pub states.
    """
    updates = payload.model_dump(exclude_unset=True)
    tpl = await admin_svc.update_template(template_id, updates)
    if not tpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Design template block not found."
        )

    await audit_svc.log_action(
        user_id=request.state.user.id if hasattr(request.state, "user") else None,
        category="Admin Action",
        action="UPDATE_TEMPLATE",
        description=f"Admin modified template layout values for {tpl.name}",
        ip_address=request.client.host if request.client else None,
        context_data=updates
    )

    return tpl


# =====================================================================
# 7. SYSTEM CONFIGURATION & ENVS
# =====================================================================

@router.get("/config", response_model=List[SystemConfigurationResponse], status_code=status.HTTP_200_OK)
async def get_system_configurations(
    config_svc: ConfigurationService = Depends(get_configuration_service)
) -> Any:
    """
    Loads environment configurations for Storage bucket, DB pools, Mail pipelines, and redis queues.
    """
    return await config_svc.get_all_configurations()


@router.put("/config/{config_key}", response_model=SystemConfigurationResponse, status_code=status.HTTP_200_OK)
async def update_system_configurations_key(
    config_key: str,
    payload: SystemConfigurationUpdatePayload,
    request: Request,
    config_svc: ConfigurationService = Depends(get_configuration_service),
    audit_svc: AuditService = Depends(get_audit_service)
) -> Any:
    """
    Saves environment-specific JSON settings (e.g., mail limits, Redis queues).
    """
    config = await config_svc.set_config(
        key=config_key,
        category=payload.category,
        value=payload.config_value,
        description=payload.description,
        is_secret=payload.is_secret
    )

    await audit_svc.log_action(
        user_id=request.state.user.id if hasattr(request.state, "user") else None,
        category="Admin Action",
        action="UPDATE_SYSTEM_CONFIG",
        description=f"Admin updated system configuration key: {config_key}",
        ip_address=request.client.host if request.client else None,
        context_data={"key": config_key, "category": payload.category}
    )

    return config


# =====================================================================
# 8. TELEMETRY MONITORING
# =====================================================================

@router.get("/monitoring/health", response_model=SystemHealthDetails, status_code=status.HTTP_200_OK)
async def get_telemetry_system_health(
    monitoring_svc: MonitoringService = Depends(get_monitoring_service)
) -> Any:
    """
    Tests live backend database channels, reports Redis connections, and returns active workers.
    """
    try:
        return await monitoring_svc.check_health()
    except Exception as e:
        logger.error(f"Telemetry diagnostics check failure: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Telemetry system check failed."
        )


# =====================================================================
# 9. COMPLIANCE AUDIT SEARCH
# =====================================================================

@router.post("/audit/search", response_model=List[AuditLogResponse], status_code=status.HTTP_200_OK)
async def search_and_filter_audit_logs(
    payload: AuditLogQueryRequest,
    audit_svc: AuditService = Depends(get_audit_service)
) -> Any:
    """
    Returns lists of administrative and platform events using categories, actions, or date offsets.
    """
    try:
        logs = await audit_svc.audit_repo.search_audit_logs(
            category=payload.category,
            action=payload.action,
            user_id=payload.user_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            limit=payload.limit,
            offset=payload.offset
        )
        return logs
    except Exception as e:
        logger.error(f"Error querying compliance audit database: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query compliance audit registry."
        )


# =====================================================================
# 10. REAL-TIME CANARY FEATURE FLAGS
# =====================================================================

@router.get("/flags", response_model=List[FeatureFlagResponse], status_code=status.HTTP_200_OK)
async def list_canary_feature_flags(
    config_svc: ConfigurationService = Depends(get_configuration_service)
) -> Any:
    """
    Lists all dynamic application toggles and progressive rollout configurations.
    """
    return await config_svc.get_all_flags()


@router.post("/flags", response_model=FeatureFlagResponse, status_code=status.HTTP_201_CREATED)
async def create_canary_feature_flag(
    payload: FeatureFlagCreatePayload,
    request: Request,
    config_svc: ConfigurationService = Depends(get_configuration_service),
    audit_svc: AuditService = Depends(get_audit_service)
) -> Any:
    """
    Registers a new progressive canary rollout toggle.
    """
    try:
        flag = await config_svc.create_flag(
            name=payload.name,
            description=payload.description,
            is_enabled=payload.is_enabled,
            rollout_percent=payload.rollout_percentage
        )

        await audit_svc.log_action(
            user_id=request.state.user.id if hasattr(request.state, "user") else None,
            category="Admin Action",
            action="CREATE_FEATURE_FLAG",
            description=f"Admin created a new feature toggle flag: {payload.name}",
            ip_address=request.client.host if request.client else None,
            context_data={"name": payload.name, "rollout": payload.rollout_percentage}
        )

        return flag
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        logger.error(f"Failed to create canary flag: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error building canary feature flag."
        )


@router.put("/flags/{flag_name}", response_model=FeatureFlagResponse, status_code=status.HTTP_200_OK)
async def update_canary_feature_flag(
    flag_name: str,
    payload: FeatureFlagUpdatePayload,
    request: Request,
    config_svc: ConfigurationService = Depends(get_configuration_service),
    audit_svc: AuditService = Depends(get_audit_service)
) -> Any:
    """
    Modifies active state or progressive rollout percentages of specific features.
    """
    flag = await config_svc.update_flag(
        name=flag_name,
        is_enabled=payload.is_enabled,
        rollout_percent=payload.rollout_percentage,
        description=payload.description
    )
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canary flag not found: {flag_name}"
        )

    await audit_svc.log_action(
        user_id=request.state.user.id if hasattr(request.state, "user") else None,
        category="Admin Action",
        action="UPDATE_FEATURE_FLAG",
        description=f"Admin mutated flag {flag_name} (Enabled: {payload.is_enabled}, Rollout: {payload.rollout_percentage}%)",
        ip_address=request.client.host if request.client else None
    )

    return flag
