import uuid
import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import select, and_, or_, update, delete, desc, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import BaseRepository
from app.models.auth import User, Role, Permission, UserSession
from app.models.admin import AuditLog, SystemConfiguration, FeatureFlag, ResumeTemplate, JobSource


class AdminRepository(BaseRepository[User]):
    """
    Handles user discovery, role allocations, user state modifications,
    and consolidates session/metric statistics for the primary overview card.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=User, db=db)

    async def search_users(
        self, 
        search_query: Optional[str] = None, 
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[User]:
        """
        Queries the user database, checking username and email against queries, and filtering by status.
        Loads users' roles eagerly to avoid N+1 queries.
        """
        query = select(self.model).options(selectinload(self.model.roles))
        conditions = []

        if hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None))

        if status_filter:
            conditions.append(self.model.status == status_filter)

        if search_query:
            term = f"%{search_query}%"
            conditions.append(
                or_(
                    self.model.username.ilike(term),
                    self.model.email.ilike(term)
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(self.model.created_at)).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_user_detail(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Loads a single user details and pre-fetches associated security roles eagerly.
        """
        query = select(self.model).options(selectinload(self.model.roles)).where(
            and_(
                self.model.id == user_id,
                self.model.deleted_at.is_(None) if hasattr(self.model, "deleted_at") else True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_or_none()

    async def update_user_roles(self, user_id: uuid.UUID, role_names: List[str]) -> bool:
        """
        Re-allocates user roles based on an authoritative list of target role names.
        """
        user = await self.get_user_detail(user_id)
        if not user:
            return False

        # Load roles
        role_query = select(Role).where(Role.name.in_(role_names))
        role_res = await self.db.execute(role_query)
        target_roles = list(role_res.scalars().all())

        user.roles = target_roles
        self.db.add(user)
        await self.db.flush()
        return True

    # --- Role and Permission Management queries ---
    async def get_all_roles(self) -> List[Role]:
        query = select(Role).options(selectinload(Role.permissions))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_all_permissions(self) -> List[Permission]:
        query = select(Permission)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_role_if_not_exists(self, name: str, description: Optional[str] = None) -> Role:
        query = select(Role).where(Role.name == name)
        res = await self.db.execute(query)
        role = res.scalar_or_none()
        if not role:
            role = Role(name=name, description=description)
            self.db.add(role)
            await self.db.flush()
        return role

    async def create_permission_if_not_exists(self, name: str, description: Optional[str] = None) -> Permission:
        query = select(Permission).where(Permission.name == name)
        res = await self.db.execute(query)
        perm = res.scalar_or_none()
        if not perm:
            perm = Permission(name=name, description=description)
            self.db.add(perm)
            await self.db.flush()
        return perm

    # --- Aggregates & Mock calculations to populate Overview ---
    async def get_active_session_count(self) -> int:
        query = select(func.count(UserSession.id)).where(UserSession.is_active == True)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_user_count_last_24h(self) -> int:
        yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        query = select(func.count(User.id)).where(User.last_login >= yesterday)
        result = await self.db.execute(query)
        return result.scalar() or 0


class AuditRepository(BaseRepository[AuditLog]):
    """
    Manages structured security logging, indexing system errors,
    and fetching audit trails with precise criteria filters.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=AuditLog, db=db)

    async def search_audit_logs(
        self,
        category: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        query = select(self.model).options(selectinload(self.model.user))
        conditions = []

        if category:
            conditions.append(self.model.category == category)
        if action:
            conditions.append(self.model.action == action)
        if user_id:
            conditions.append(self.model.user_id == user_id)
        if start_date:
            conditions.append(self.model.created_at >= start_date)
        if end_date:
            conditions.append(self.model.created_at <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(self.model.created_at)).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())


class ConfigurationRepository(BaseRepository[SystemConfiguration]):
    """
    Retrieves and patches application configuration payloads with dynamic caching safety.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=SystemConfiguration, db=db)

    async def get_by_key(self, key: str) -> Optional[SystemConfiguration]:
        query = select(self.model).where(self.model.config_key == key)
        result = await self.db.execute(query)
        return result.scalar_or_none()

    async def save_config_value(
        self, 
        key: str, 
        category: str, 
        value: Dict[str, Any], 
        description: Optional[str] = None,
        is_secret: bool = False
    ) -> SystemConfiguration:
        config = await self.get_by_key(key)
        if config:
            config.config_value = value
            config.category = category
            if description:
                config.description = description
            config.is_secret = is_secret
        else:
            config = SystemConfiguration(
                config_key=key,
                category=category,
                config_value=value,
                description=description,
                is_secret=is_secret
            )
            self.db.add(config)
            
        await self.db.flush()
        return config


class FeatureFlagRepository(BaseRepository[FeatureFlag]):
    """
    Fetches, rolls out, and updates localized user toggles.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=FeatureFlag, db=db)

    async def get_by_name(self, name: str) -> Optional[FeatureFlag]:
        query = select(self.model).where(self.model.name == name)
        result = await self.db.execute(query)
        return result.scalar_or_none()


class ResumeTemplateRepository(BaseRepository[ResumeTemplate]):
    """
    Persists global templates of resume designs with responsive category listings.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=ResumeTemplate, db=db)

    async def get_by_name(self, name: str) -> Optional[ResumeTemplate]:
        query = select(self.model).where(self.model.name == name)
        result = await self.db.execute(query)
        return result.scalar_or_none()


class JobSourceRepository(BaseRepository[JobSource]):
    """
    Queries, enables, and manages pluggable job crawler references.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=JobSource, db=db)

    async def get_by_name(self, name: str) -> Optional[JobSource]:
        query = select(self.model).where(self.model.name == name)
        result = await self.db.execute(query)
        return result.scalar_or_none()
