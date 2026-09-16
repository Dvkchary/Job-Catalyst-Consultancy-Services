import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.base_models import DatabaseModelMixin

# ==============================================================================
# Associative Tables for Many-to-Many Relationships
# ==============================================================================

# User <-> Role Many-to-Many association table
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
)

# Role <-> Permission Many-to-Many association table
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permission.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(Base, DatabaseModelMixin):
    """
    Granular action privileges mapped under roles for Role-Based Access Control (RBAC).
    Examples: 'user:write', 'jobs:create', 'resumes:delete'.
    """
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )


class Role(Base, DatabaseModelMixin):
    """
    A logical security boundary grouping multiple granular privileges.
    Standard Roles: ADMIN, USER, RECRUITER, CAREER_COACH.
    """
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    permissions: Mapped[List[Permission]] = relationship(
        Permission,
        secondary=role_permissions,
        back_populates="roles"
    )
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )


class User(Base, DatabaseModelMixin):
    """
    Core User Account entity containing password credentials, brute-force safeguards,
    MFA keys, verification details, and active status state management.
    """
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)  # ACTIVE, PENDING, LOCKED, SUSPENDED
    
    # Email verification attributes
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verification_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Password reset attributes
    reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reset_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Multi-Factor Authentication (TOTP Ready)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mfa_recovery_codes: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)  # comma-separated encrypted/plain recovery blocks

    # Brute Force Safeguards
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    roles: Mapped[List[Role]] = relationship(
        Role,
        secondary=user_roles,
        back_populates="users"
    )
    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class UserSession(Base, DatabaseModelMixin):
    """
    Device and active connection tracker to support Multi-Device tracking,
    Refresh Token rotation lookup, and instant centralized session revocation.
    """
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # supports IPv6 lengths
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    device_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    user: Mapped[User] = relationship(User, back_populates="sessions")


class TokenRevocation(Base, DatabaseModelMixin):
    """
    Centralized Token Denylist for immediate invalidation of signed Access Tokens (JWT JTI blocks)
    before their natural token expiration boundaries are hit.
    """
    token_jti: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
