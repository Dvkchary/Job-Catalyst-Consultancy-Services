import logging
from typing import AsyncGenerator, List, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, settings
from app.core.cache_pool import fast_cache
from app.db.repositories import (
    PermissionRepository,
    RoleRepository,
    TokenRevocationRepository,
    UserRepository,
    UserSessionRepository,
)
from app.db.profile_repositories import (
    UserProfileRepository,
    AccountSettingsRepository,
)
from app.db.resume_repositories import (
    ResumeRepository,
    ResumeTemplateRepository,
    ResumeVersionRepository,
)
from app.db.ats_repositories import ATSRepository
from app.db.matching_repositories import (
    MatchingRepository,
    AnalysisRepository,
    HistoryRepository
)
from app.services.matching import MatchingService
from app.db.job_repositories import (
    CompanyRepository,
    JobRepository,
    SavedJobRepository,
    SavedSearchRepository,
    SearchHistoryRepository
)
from app.db.session import get_db
from app.models.auth import User
from app.services.authentication import AuthenticationService
from app.services.authorization import AuthorizationService
from app.services.email import EmailService
from app.services.jwt import JWTService
from app.services.password import PasswordService
from app.services.profile import ProfileService
from app.services.settings import SettingsService
from app.services.resume import ResumeService
from app.services.resume_template import ResumeTemplateService
from app.services.ats import ATSService
from app.services.job_engine import (
    CompanyService,
    JobService,
    SearchService,
    ImportService
)
from app.db.interview_repositories import (
    InterviewRepository,
    QuestionRepository,
    HistoryRepository as InterviewHistoryRepository
)
from app.services.interview import InterviewService
from app.db.career_repositories import (
    CareerRepository,
    RoadmapRepository,
    RecommendationRepository
)
from app.services.career import (
    CareerService,
    RoadmapService,
    RecommendationService,
    AnalyticsService
)
from app.db.dashboard_repositories import (
    DashboardWidgetRepository,
    ExecutiveReportRepository,
    AnalyticsRepository
)
from app.services.dashboard import (
    DashboardService,
    PlatformAnalyticsService,
    ReportService,
    ExportService
)
from app.db.notification_repositories import (
    NotificationRepository,
    NotificationPreferenceRepository
)
from app.services.notification import (
    NotificationService,
    EmailService as NotificationEmailService,
    ReminderService
)


logger = logging.getLogger("app.dependencies")

# Bearer token extractor
security_bearer = HTTPBearer(auto_error=True)

# ==============================================================================
# 1. Settings Provider (Settings Container)
# ==============================================================================
def get_settings() -> Settings:
    """Provides the singular global validated configuration instance."""
    return settings


# ==============================================================================
# 2. Database Connection Container (Active Async Session)
# ==============================================================================
async def get_db_session(session: AsyncSession = Depends(get_db)) -> AsyncGenerator[AsyncSession, None]:
    """
    Asynchronous generator yielding an active, transaction-scoped SQLAlchemy AsyncSession.
    """
    yield session


# ==============================================================================
# 3. Cache & Message Broker Container (Redis Placeholder)
# ==============================================================================
class RedisContainer:
    """
    Mockable wrapper encapsulating client interaction with Redis caches
    and rate limit storage pools.
    """
    def __init__(self, current_settings: Settings = Depends(get_settings)) -> None:
        self.settings = current_settings
        self.client_connected = True

    async def get_key(self, key: str) -> Optional[str]:
        """Fetch cached string value from Redis registry."""
        val = await fast_cache.get(key)
        logger.debug(f"Cache READ: {key} (Hit: {val is not None})")
        return val

    async def set_key(self, key: str, value: str, expire_seconds: int = 3600) -> bool:
        """Cache key-value block with sliding expiration limits."""
        logger.debug(f"Cache WRITE: {key} TTL:{expire_seconds}")
        return await fast_cache.set(key, value, ttl_seconds=expire_seconds)


def get_redis_client(redis_container: RedisContainer = Depends()) -> RedisContainer:
    """Provides the configured cache connection wrapper instance."""
    return redis_container


# ==============================================================================
# 4. Individual Service & Repository Providers
# ==============================================================================
def get_password_service() -> PasswordService:
    return PasswordService()


def get_jwt_service() -> JWTService:
    return JWTService()


def get_email_service() -> EmailService:
    return EmailService()


def get_authorization_service() -> AuthorizationService:
    return AuthorizationService()


def get_user_repository(db: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return UserRepository(db=db)


def get_role_repository(db: AsyncSession = Depends(get_db_session)) -> RoleRepository:
    return RoleRepository(db=db)


def get_session_repository(db: AsyncSession = Depends(get_db_session)) -> UserSessionRepository:
    return UserSessionRepository(db=db)


def get_revocation_repository(db: AsyncSession = Depends(get_db_session)) -> TokenRevocationRepository:
    return TokenRevocationRepository(db=db)


def get_profile_repository(db: AsyncSession = Depends(get_db_session)) -> UserProfileRepository:
    return UserProfileRepository(db=db)


def get_settings_repository(db: AsyncSession = Depends(get_db_session)) -> AccountSettingsRepository:
    return AccountSettingsRepository(db=db)


def get_profile_service(
    profile_repo: UserProfileRepository = Depends(get_profile_repository)
) -> ProfileService:
    return ProfileService(profile_repo=profile_repo)


def get_settings_service(
    settings_repo: AccountSettingsRepository = Depends(get_settings_repository)
) -> SettingsService:
    return SettingsService(settings_repo=settings_repo)


def get_resume_repository(db: AsyncSession = Depends(get_db_session)) -> ResumeRepository:
    return ResumeRepository(db=db)


def get_resume_template_repository(db: AsyncSession = Depends(get_db_session)) -> ResumeTemplateRepository:
    return ResumeTemplateRepository(db=db)


def get_resume_version_repository(db: AsyncSession = Depends(get_db_session)) -> ResumeVersionRepository:
    return ResumeVersionRepository(db=db)


def get_resume_template_service(
    template_repo: ResumeTemplateRepository = Depends(get_resume_template_repository)
) -> ResumeTemplateService:
    return ResumeTemplateService(template_repo=template_repo)


def get_resume_service(
    resume_repo: ResumeRepository = Depends(get_resume_repository),
    template_repo: ResumeTemplateRepository = Depends(get_resume_template_repository),
    version_repo: ResumeVersionRepository = Depends(get_resume_version_repository)
) -> ResumeService:
    return ResumeService(
        resume_repo=resume_repo,
        template_repo=template_repo,
        version_repo=version_repo
    )


def get_ats_repository(db: AsyncSession = Depends(get_db_session)) -> ATSRepository:
    return ATSRepository(db=db)


def get_ats_service(
    ats_repo: ATSRepository = Depends(get_ats_repository),
    resume_repo: ResumeRepository = Depends(get_resume_repository)
) -> ATSService:
    return ATSService(ats_repo=ats_repo, resume_repo=resume_repo)


# ==============================================================================
# Job Engine Providers
# ==============================================================================

def get_company_repository(db: AsyncSession = Depends(get_db_session)) -> CompanyRepository:
    return CompanyRepository(db=db)


def get_job_repository(db: AsyncSession = Depends(get_db_session)) -> JobRepository:
    return JobRepository(db=db)


def get_saved_job_repository(db: AsyncSession = Depends(get_db_session)) -> SavedJobRepository:
    return SavedJobRepository(db=db)


def get_saved_search_repository(db: AsyncSession = Depends(get_db_session)) -> SavedSearchRepository:
    return SavedSearchRepository(db=db)


def get_search_history_repository(db: AsyncSession = Depends(get_db_session)) -> SearchHistoryRepository:
    return SearchHistoryRepository(db=db)


def get_company_service(
    company_repo: CompanyRepository = Depends(get_company_repository)
) -> CompanyService:
    return CompanyService(company_repo=company_repo)


def get_job_service(
    job_repo: JobRepository = Depends(get_job_repository),
    company_repo: CompanyRepository = Depends(get_company_repository),
    saved_job_repo: SavedJobRepository = Depends(get_saved_job_repository)
) -> JobService:
    return JobService(
        job_repo=job_repo,
        company_repo=company_repo,
        saved_job_repo=saved_job_repo
    )


def get_search_service(
    job_repo: JobRepository = Depends(get_job_repository),
    saved_search_repo: SavedSearchRepository = Depends(get_saved_search_repository),
    search_history_repo: SearchHistoryRepository = Depends(get_search_history_repository)
) -> SearchService:
    return SearchService(
        job_repo=job_repo,
        saved_search_repo=saved_search_repo,
        search_history_repo=search_history_repo
    )


def get_import_service(
    job_service: JobService = Depends(get_job_service),
    job_repo: JobRepository = Depends(get_job_repository)
) -> ImportService:
    return ImportService(
        job_service=job_service,
        job_repo=job_repo
    )


def get_matching_repository(db: AsyncSession = Depends(get_db_session)) -> MatchingRepository:
    return MatchingRepository(db=db)


def get_analysis_repository(db: AsyncSession = Depends(get_db_session)) -> AnalysisRepository:
    return AnalysisRepository(db=db)


def get_history_repository(db: AsyncSession = Depends(get_db_session)) -> HistoryRepository:
    return HistoryRepository(db=db)


def get_matching_service(
    match_repo: MatchingRepository = Depends(get_matching_repository),
    analysis_repo: AnalysisRepository = Depends(get_analysis_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
    resume_repo: ResumeRepository = Depends(get_resume_repository),
    job_repo: JobRepository = Depends(get_job_repository)
) -> MatchingService:
    return MatchingService(
        match_repo=match_repo,
        analysis_repo=analysis_repo,
        history_repo=history_repo,
        resume_repo=resume_repo,
        job_repo=job_repo
    )


def get_interview_repository(db: AsyncSession = Depends(get_db_session)) -> InterviewRepository:
    return InterviewRepository(db=db)


def get_question_repository(db: AsyncSession = Depends(get_db_session)) -> QuestionRepository:
    return QuestionRepository(db=db)


def get_interview_history_repository(db: AsyncSession = Depends(get_db_session)) -> InterviewHistoryRepository:
    return InterviewHistoryRepository(db=db)


def get_interview_service(
    interview_repo: InterviewRepository = Depends(get_interview_repository),
    question_repo: QuestionRepository = Depends(get_question_repository),
    history_repo: InterviewHistoryRepository = Depends(get_interview_history_repository),
    resume_repo: ResumeRepository = Depends(get_resume_repository),
    job_repo: JobRepository = Depends(get_job_repository)
) -> InterviewService:
    return InterviewService(
        interview_repo=interview_repo,
        question_repo=question_repo,
        history_repo=history_repo,
        resume_repo=resume_repo,
        job_repo=job_repo
    )


def get_career_repository(db: AsyncSession = Depends(get_db_session)) -> CareerRepository:
    return CareerRepository(db=db)


def get_roadmap_repository(db: AsyncSession = Depends(get_db_session)) -> RoadmapRepository:
    return RoadmapRepository(db=db)


def get_recommendation_repository(db: AsyncSession = Depends(get_db_session)) -> RecommendationRepository:
    return RecommendationRepository(db=db)


def get_career_service(
    career_repo: CareerRepository = Depends(get_career_repository)
) -> CareerService:
    return CareerService(career_repo=career_repo)


def get_roadmap_service(
    roadmap_repo: RoadmapRepository = Depends(get_roadmap_repository),
    career_repo: CareerRepository = Depends(get_career_repository)
) -> RoadmapService:
    return RoadmapService(roadmap_repo=roadmap_repo, career_repo=career_repo)


def get_recommendation_service(
    recommendation_repo: RecommendationRepository = Depends(get_recommendation_repository),
    career_repo: CareerRepository = Depends(get_career_repository)
) -> RecommendationService:
    return RecommendationService(recommendation_repo=recommendation_repo, career_repo=career_repo)


def get_analytics_service(
    db: AsyncSession = Depends(get_db_session)
) -> AnalyticsService:
    return AnalyticsService(db_session=db)


def get_dashboard_widget_repository(db: AsyncSession = Depends(get_db_session)) -> DashboardWidgetRepository:
    return DashboardWidgetRepository(db=db)


def get_executive_report_repository(db: AsyncSession = Depends(get_db_session)) -> ExecutiveReportRepository:
    return ExecutiveReportRepository(db=db)


def get_analytics_repository(db: AsyncSession = Depends(get_db_session)) -> AnalyticsRepository:
    return AnalyticsRepository(db=db)


def get_dashboard_service(
    widget_repo: DashboardWidgetRepository = Depends(get_dashboard_widget_repository),
    db: AsyncSession = Depends(get_db_session)
) -> DashboardService:
    return DashboardService(widget_repo=widget_repo, db_session=db)


def get_platform_analytics_service(
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repository)
) -> PlatformAnalyticsService:
    return PlatformAnalyticsService(analytics_repo=analytics_repo)


def get_report_service(
    report_repo: ExecutiveReportRepository = Depends(get_executive_report_repository),
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repository),
    db: AsyncSession = Depends(get_db_session)
) -> ReportService:
    return ReportService(report_repo=report_repo, analytics_repo=analytics_repo, db_session=db)


def get_export_service(
    report_repo: ExecutiveReportRepository = Depends(get_executive_report_repository)
) -> ExportService:
    return ExportService(report_repo=report_repo)


def get_notification_repository(db: AsyncSession = Depends(get_db_session)) -> NotificationRepository:
    return NotificationRepository(db=db)


def get_notification_preference_repository(db: AsyncSession = Depends(get_db_session)) -> NotificationPreferenceRepository:
    return NotificationPreferenceRepository(db=db)


def get_notification_email_service() -> NotificationEmailService:
    return NotificationEmailService()


def get_notification_service(
    notification_repo: NotificationRepository = Depends(get_notification_repository),
    pref_repo: NotificationPreferenceRepository = Depends(get_notification_preference_repository),
    email_svc: NotificationEmailService = Depends(get_notification_email_service),
    db: AsyncSession = Depends(get_db_session)
) -> NotificationService:
    return NotificationService(
        notification_repo=notification_repo,
        pref_repo=pref_repo,
        email_svc=email_svc,
        db_session=db
    )


def get_reminder_service(
    notif_svc: NotificationService = Depends(get_notification_service)
) -> ReminderService:
    return ReminderService(notif_svc=notif_svc)


# ==============================================================================
# Enterprise Admin Portal Providers (Module 16)
# ==============================================================================

def get_career_os_service(
    db: AsyncSession = Depends(get_db_session)
):
    from app.services.career_os import CareerOSService
    return CareerOSService(db=db)


def get_admin_repository(db: AsyncSession = Depends(get_db_session)):
    from app.db.admin_repositories import AdminRepository
    return AdminRepository(db=db)


def get_audit_repository(db: AsyncSession = Depends(get_db_session)):
    from app.db.admin_repositories import AuditRepository
    return AuditRepository(db=db)


def get_configuration_repository(db: AsyncSession = Depends(get_db_session)):
    from app.db.admin_repositories import ConfigurationRepository
    return ConfigurationRepository(db=db)


def get_feature_flag_repository(db: AsyncSession = Depends(get_db_session)):
    from app.db.admin_repositories import FeatureFlagRepository
    return FeatureFlagRepository(db=db)


def get_admin_resume_template_repository(db: AsyncSession = Depends(get_db_session)):
    from app.db.admin_repositories import ResumeTemplateRepository
    return ResumeTemplateRepository(db=db)


def get_admin_job_source_repository(db: AsyncSession = Depends(get_db_session)):
    from app.db.admin_repositories import JobSourceRepository
    return JobSourceRepository(db=db)


def get_audit_service(audit_repo=Depends(get_audit_repository)):
    from app.services.admin import AuditService
    return AuditService(audit_repo=audit_repo)


def get_monitoring_service(db: AsyncSession = Depends(get_db_session)):
    from app.services.admin import MonitoringService
    return MonitoringService(db=db)


def get_configuration_service(
    config_repo=Depends(get_configuration_repository),
    flag_repo=Depends(get_feature_flag_repository)
):
    from app.services.admin import ConfigurationService
    return ConfigurationService(config_repo=config_repo, flag_repo=flag_repo)


def get_admin_service(
    admin_repo=Depends(get_admin_repository),
    audit_svc=Depends(get_audit_service),
    monitoring_svc=Depends(get_monitoring_service),
    template_repo=Depends(get_admin_resume_template_repository),
    job_source_repo=Depends(get_admin_job_source_repository),
    db: AsyncSession = Depends(get_db_session)
):
    from app.services.admin import AdminService
    return AdminService(
        admin_repo=admin_repo,
        audit_svc=audit_svc,
        monitoring_svc=monitoring_svc,
        template_repo=template_repo,
        job_source_repo=job_source_repo,
        db_session=db
    )


def get_workflow_service(db: AsyncSession = Depends(get_db_session)):
    from app.services.workflow_service import WorkflowService
    return WorkflowService(db=db)



def get_authentication_service(
    user_repo: UserRepository = Depends(get_user_repository),
    role_repo: RoleRepository = Depends(get_role_repository),
    session_repo: UserSessionRepository = Depends(get_session_repository),
    revocation_repo: TokenRevocationRepository = Depends(get_revocation_repository),
    password_svc: PasswordService = Depends(get_password_service),
    jwt_svc: JWTService = Depends(get_jwt_service),
    email_svc: EmailService = Depends(get_email_service),
) -> AuthenticationService:
    """
    Factory injecting core infrastructure services into unified AuthenticationService.
    """
    return AuthenticationService(
        user_repo=user_repo,
        role_repo=role_repo,
        session_repo=session_repo,
        revocation_repo=revocation_repo,
        password_svc=password_svc,
        jwt_svc=jwt_svc,
        email_svc=email_svc,
    )


# ==============================================================================
# 5. Security & RBAC Middleware Dependencies
# ==============================================================================
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_bearer),
    jwt_svc: JWTService = Depends(get_jwt_service),
    user_repo: UserRepository = Depends(get_user_repository),
    revocation_repo: TokenRevocationRepository = Depends(get_revocation_repository),
) -> User:
    """
    Decodes Access Token, verifies claims, validates denylist, and returns the User profile.
    """
    token = credentials.credentials
    try:
        payload = jwt_svc.verify_token(token, expected_type="access")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    token_jti = payload.get("jti")
    user_id_str = payload.get("sub")

    # 1. Denylist Revocation Verification
    if await revocation_repo.is_revoked(token_jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Fetch Active Account Profile
    user_id = uuid_to_object = None
    try:
        import uuid
        user_id = uuid.UUID(user_id_str)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token subject identifier.",
        ) from e

    user = await user_repo.get_with_roles(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated or missing.",
        )

    # Attach token JTI to user object dynamically for downstream audit tracking (e.g., logout route)
    setattr(user, "current_token_jti", token_jti)
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Guarantees user is fully verified and holds active state (not suspended or locked).
    """
    if current_user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User account is inactive. Current status: {current_user.status}"
        )
    return current_user


def require_permission(permission: str):
    """
    RBAC Permission Dependency Gate.
    Restricts route access to accounts possessing explicit permissions.
    """
    async def dependency(
        current_user: User = Depends(get_current_active_user),
        auth_svc: AuthorizationService = Depends(get_authorization_service),
    ) -> User:
        user_roles = [role.name for role in current_user.roles]
        if not auth_svc.has_permission(user_roles, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required security privilege is missing: {permission}"
            )
        return current_user
    return dependency


def require_role(role_name: str):
    """
    RBAC Role Dependency Gate.
    Restricts route access to accounts carrying standard functional roles.
    """
    async def dependency(
        current_user: User = Depends(get_current_active_user),
        auth_svc: AuthorizationService = Depends(get_authorization_service),
    ) -> User:
        user_roles = [role.name for role in current_user.roles]
        if not auth_svc.has_any_role(user_roles, [role_name]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required user role is missing: {role_name}"
            )
        return current_user
    return dependency


# ==============================================================================
# Legacy / Container Classes Compatibility mapping
# ==============================================================================
class RepositoryContainer:
    def __init__(self, db: AsyncSession = Depends(get_db_session)) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)
        self.sessions = UserSessionRepository(db)
        self.revocations = TokenRevocationRepository(db)
        self.profiles = UserProfileRepository(db)
        self.settings = AccountSettingsRepository(db)
        self.resumes = ResumeRepository(db)
        self.templates = ResumeTemplateRepository(db)
        self.versions = ResumeVersionRepository(db)
        self.ats = ATSRepository(db)


class ServiceContainer:
    def __init__(
        self,
        repos: RepositoryContainer = Depends(),
        cache: RedisContainer = Depends(get_redis_client),
        password_svc: PasswordService = Depends(get_password_service),
        jwt_svc: JWTService = Depends(get_jwt_service),
        email_svc: EmailService = Depends(get_email_service),
        auth_svc: AuthorizationService = Depends(get_authorization_service),
        profile_svc: ProfileService = Depends(get_profile_service),
        settings_svc: SettingsService = Depends(get_settings_service),
        resume_template_svc: ResumeTemplateService = Depends(get_resume_template_service),
        resume_svc: ResumeService = Depends(get_resume_service),
        ats_svc: ATSService = Depends(get_ats_service),
    ) -> None:
        self.repos = repos
        self.cache = cache
        self.password = password_svc
        self.jwt = jwt_svc
        self.email = email_svc
        self.auth = auth_svc
        self.profile = profile_svc
        self.settings = settings_svc
        self.resume_template = resume_template_svc
        self.resume = resume_svc
        self.ats = ats_svc
        self.authentication = AuthenticationService(
            user_repo=repos.users,
            role_repo=repos.roles,
            session_repo=repos.sessions,
            revocation_repo=repos.revocations,
            password_svc=password_svc,
            jwt_svc=jwt_svc,
            email_svc=email_svc,
        )


def get_repository_container(container: RepositoryContainer = Depends()) -> RepositoryContainer:
    return container


def get_service_container(container: ServiceContainer = Depends()) -> ServiceContainer:
    return container
