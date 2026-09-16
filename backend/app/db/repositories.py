import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.repository import BaseRepository
from app.models.auth import Permission, Role, TokenRevocation, User, UserSession


class UserRepository(BaseRepository[User]):
    """
    Data-access repository for managing User entity persistence and eager relations loading.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=User, db=db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieves an active user with matching email address."""
        email_clean = email.strip().lower()
        query = select(self.model).where(
            and_(
                self.model.email == email_clean,
                self.model.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Retrieves an active user with matching username."""
        username_clean = username.strip()
        query = select(self.model).where(
            and_(
                self.model.username == username_clean,
                self.model.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_or_none()

    async def get_with_roles(self, user_id: uuid.UUID) -> Optional[User]:
        """Retrieves a user and eager-loads associated Roles and Permissions."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.id == user_id,
                    self.model.deleted_at.is_(None)
                )
            )
            .options(
                selectinload(self.model.roles).selectinload(Role.permissions)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_or_none()


class RoleRepository(BaseRepository[Role]):
    """
    Data-access repository for User authorization Roles.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=Role, db=db)

    async def get_by_name(self, name: str) -> Optional[Role]:
        """Retrieves a role matching standard names (e.g., ADMIN, USER)."""
        query = select(self.model).where(
            and_(
                self.model.name == name.upper().strip(),
                self.model.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_or_none()

    async def get_all_with_permissions(self) -> List[Role]:
        """Retrieves all roles with associated granular Permissions pre-loaded."""
        query = select(self.model).where(self.model.deleted_at.is_(None)).options(selectinload(self.model.permissions))
        result = await self.db.execute(query)
        return list(result.scalars().all())


class PermissionRepository(BaseRepository[Permission]):
    """
    Data-access repository for security permissions.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=Permission, db=db)

    async def get_by_name(self, name: str) -> Optional[Permission]:
        """Retrieves permission by unique string value."""
        query = select(self.model).where(
            and_(
                self.model.name == name.lower().strip(),
                self.model.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_or_none()


class UserSessionRepository(BaseRepository[UserSession]):
    """
    Data-access repository for tracking device connections and Refresh Token validation.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=UserSession, db=db)

    async def get_active_by_token_id(self, refresh_token_id: str) -> Optional[UserSession]:
        """Retrieves active session matched to unique Refresh Token ID."""
        query = select(self.model).where(
            and_(
                self.model.refresh_token_id == refresh_token_id,
                self.model.is_active == True,
                self.model.expires_at > datetime.utcnow(),
                self.model.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_or_none()

    async def get_all_active_by_user_id(self, user_id: uuid.UUID) -> List[UserSession]:
        """Retrieves all active sessions logged into a user account."""
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.is_active == True,
                self.model.expires_at > datetime.utcnow(),
                self.model.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def deactivate_all_by_user_id(self, user_id: uuid.UUID, exclude_token_id: Optional[str] = None) -> int:
        """Deactivates active sessions to trigger global logout (or other-device logouts)."""
        active_sessions = await self.get_all_active_by_user_id(user_id)
        count = 0
        for sess in active_sessions:
            if exclude_token_id and sess.refresh_token_id == exclude_token_id:
                continue
            sess.is_active = False
            self.db.add(sess)
            count += 1
        if count > 0:
            await self.db.flush()
        return count


class TokenRevocationRepository(BaseRepository[TokenRevocation]):
    """
    Data-access repository for denying signed Access Tokens.
    """
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=TokenRevocation, db=db)

    async def is_revoked(self, token_jti: str) -> bool:
        """Checks if a JTI (JWT uniquely signed identifier) is blacklisted."""
        query = select(self.model).where(
            and_(
                self.model.token_jti == token_jti,
                self.model.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_or_none() is not None
