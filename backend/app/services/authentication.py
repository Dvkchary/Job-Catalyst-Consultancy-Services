import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from app.core.config import settings
from app.db.repositories import (
    PermissionRepository,
    RoleRepository,
    TokenRevocationRepository,
    UserRepository,
    UserSessionRepository,
)
from app.models.auth import User, UserSession
from app.services.email import EmailService
from app.services.jwt import JWTService
from app.services.password import PasswordService


class AuthenticationService:
    """
    Unified Authentication Service coordinating credential validation, session creation,
    Refresh Token rotation, rate limiting tracking, lockouts, and email dispatch boundaries.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        role_repo: RoleRepository,
        session_repo: UserSessionRepository,
        revocation_repo: TokenRevocationRepository,
        password_svc: PasswordService,
        jwt_svc: JWTService,
        email_svc: EmailService,
    ) -> None:
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.session_repo = session_repo
        self.revocation_repo = revocation_repo
        self.password_svc = password_svc
        self.jwt_svc = jwt_svc
        self.email_svc = email_svc

    async def register_user(
        self,
        email: str,
        username: str,
        password: str,
        role_names: Optional[List[str]] = None,
    ) -> User:
        """
        Signs up a new user account, enforces password rules, assigns standard roles,
        and triggers verification email link generation.
        """
        # 1. Duplication Safeguards
        existing_email = await self.user_repo.get_by_email(email)
        if existing_email:
            raise ValueError("An account with this email address already exists.")

        existing_user = await self.user_repo.get_by_username(username)
        if existing_user:
            raise ValueError("This username is already taken.")

        # 2. Password Strength Validation
        is_strong, msg = self.password_svc.validate_password_strength(password)
        if not is_strong:
            raise ValueError(msg)

        # 3. Credential Hashing
        pwd_hash = self.password_svc.hash_password(password)

        # 4. Resolve Roles
        roles_to_assign = []
        if not role_names:
            role_names = ["USER"]

        for name in role_names:
            role = await self.role_repo.get_by_name(name)
            if not role:
                # Let's seed missing roles on the fly to support quick setup
                role = await self.role_repo.create({"name": name.upper().strip()})
            roles_to_assign.append(role)

        # 5. Verification Token Generation
        verification_token = str(uuid.uuid4())
        expiry = datetime.now(timezone.utc) + timedelta(hours=24)

        # 6. Entity Instantiation
        user_payload = {
            "email": email.strip().lower(),
            "username": username.strip(),
            "password_hash": pwd_hash,
            "status": "ACTIVE",
            "email_verified": False,
            "verification_token": verification_token,
            "verification_token_expires_at": expiry,
        }

        user = await self.user_repo.create(user_payload)
        user.roles = roles_to_assign
        await self.user_repo.db.flush()

        # 7. Verification Email Dispatch
        self.email_svc.send_verification_email(user.email, verification_token)

        return user

    async def authenticate_user(
        self,
        identity: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[User, str, str]:
        """
        Authenticates a user, tracks failed logins, enforces lockouts, and returns (user, access_token, refresh_token).
        """
        # Look up by either email or username
        user = await self.user_repo.get_by_email(identity)
        if not user:
            user = await self.user_repo.get_by_username(identity)

        if not user:
            raise ValueError("Invalid authentication credentials.")

        now = datetime.now(timezone.utc)

        # 1. Evaluate Lockout Threshold
        if user.status == "LOCKED" or user.locked_until:
            if user.locked_until and user.locked_until > now:
                diff_mins = int((user.locked_until - now).total_seconds() / 60) + 1
                raise ValueError(f"Account is temporarily locked due to security limits. Retry in {diff_mins} minutes.")
            else:
                # Lockout time has elapsed, restore account
                user.status = "ACTIVE"
                user.failed_login_attempts = 0
                user.locked_until = None
                self.user_repo.db.add(user)

        # 2. Check Password Verification
        is_valid_pwd = self.password_svc.verify_password(user.password_hash, password)
        if not is_valid_pwd:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.status = "LOCKED"
                user.locked_until = now + timedelta(minutes=15)
                self.user_repo.db.add(user)
                await self.user_repo.db.flush()
                raise ValueError("Account locked. Too many failed verification attempts.")
            
            self.user_repo.db.add(user)
            await self.user_repo.db.flush()
            raise ValueError("Invalid authentication credentials.")

        # 3. Successful Login State Transition
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = now
        self.user_repo.db.add(user)

        # Eager load roles
        user_with_roles = await self.user_repo.get_with_roles(user.id)
        role_names = [role.name for role in user_with_roles.roles] if user_with_roles else []

        # 4. Generate Tokens
        access_token = self.jwt_svc.create_access_token(user.id, role_names)
        refresh_token, refresh_jti = self.jwt_svc.create_refresh_token(user.id)

        # 5. Create Session Entity
        session_expiry = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        session_payload = {
            "user_id": user.id,
            "refresh_token_id": refresh_jti,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "is_active": True,
            "expires_at": session_expiry,
        }
        await self.session_repo.create(session_payload)

        return user, access_token, refresh_token

    async def rotate_refresh_token(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Executes Refresh Token Rotation (RTR).
        Rotates the active session and returns (new_access_token, new_refresh_token).
        """
        try:
            payload = self.jwt_svc.verify_token(refresh_token, expected_type="refresh")
        except ValueError as e:
            raise ValueError(f"Invalid refresh token: {str(e)}") from e

        user_id = uuid.UUID(payload["sub"])
        token_jti = payload["jti"]

        # Look up session mapped to token JTI
        session = await self.session_repo.get_active_by_token_id(token_jti)
        if not session:
            # Mitigation: Potential token theft or reuse. Invalidate all user sessions.
            await self.session_repo.deactivate_all_by_user_id(user_id)
            raise ValueError("Refresh token reuse detected or session is revoked. Logged out everywhere.")

        # Eager load user and roles
        user_with_roles = await self.user_repo.get_with_roles(user_id)
        if not user_with_roles:
            raise ValueError("Associated user account is missing or suspended.")

        role_names = [role.name for role in user_with_roles.roles]

        # Issue new pair
        new_access = self.jwt_svc.create_access_token(user_id, role_names)
        new_refresh, new_refresh_jti = self.jwt_svc.create_refresh_token(user_id)

        # Update and rotate active session details
        session.refresh_token_id = new_refresh_jti
        session.ip_address = ip_address
        session.user_agent = user_agent
        session.expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        self.session_repo.db.add(session)
        await self.session_repo.db.flush()

        return new_access, new_refresh

    async def terminate_session(self, refresh_token: str, access_token_jti: Optional[str] = None) -> bool:
        """
        Logs out a user session, revoking the active Refresh Token and Access Token.
        """
        try:
            payload = self.jwt_svc.verify_token(refresh_token, expected_type="refresh")
            token_jti = payload["jti"]
            session = await self.session_repo.get_active_by_token_id(token_jti)
            if session:
                session.is_active = False
                self.session_repo.db.add(session)
                await self.session_repo.db.flush()
        except Exception:
            # Graceful logging or ignore on parsing issues for unauthenticated/bad tokens
            pass

        # Blacklist Access Token JTI if supplied
        if access_token_jti:
            now = datetime.now(timezone.utc)
            # Expire revocation entry after ACCESS_TOKEN_EXPIRE_MINUTES
            exp = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            await self.revocation_repo.create({
                "token_jti": access_token_jti,
                "revoked_at": now,
                "expires_at": exp,
            })

        return True

    async def request_password_reset(self, email: str) -> bool:
        """
        Initiates password reset workflows, generates reset tokens, and dispatches links.
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            # To prevent username harvesting/enumeration, we return True as if the request succeeded.
            return True

        reset_token = str(uuid.uuid4())
        expiry = datetime.now(timezone.utc) + timedelta(hours=1)

        user.reset_token = reset_token
        user.reset_token_expires_at = expiry
        self.user_repo.db.add(user)
        await self.user_repo.db.flush()

        # Dispatch Reset Mail
        self.email_svc.send_password_reset_email(user.email, reset_token)
        return True

    async def reset_password(self, reset_token: str, new_password: str) -> bool:
        """
        Completes password recovery after validating the token.
        """
        query = self.user_repo.db.execute(
            self.user_repo.model.__table__.select().where(
                self.user_repo.model.reset_token == reset_token
            )
        )
        # Fallback to general lookup
        # Direct select query
        from sqlalchemy import select
        res = await self.user_repo.db.execute(
            select(User).where(User.reset_token == reset_token)
        )
        user = res.scalar_or_none()
        if not user:
            raise ValueError("Invalid password reset token.")

        now = datetime.now(timezone.utc)
        if not user.reset_token_expires_at or user.reset_token_expires_at < now:
            raise ValueError("The password reset link has expired.")

        # Password strength checks
        is_strong, msg = self.password_svc.validate_password_strength(new_password)
        if not is_strong:
            raise ValueError(msg)

        # Save credentials
        user.password_hash = self.password_svc.hash_password(new_password)
        user.reset_token = None
        user.reset_token_expires_at = None
        
        # Deactivate all active sessions to force re-auth across all devices after credentials reset!
        await self.session_repo.deactivate_all_by_user_id(user.id)

        self.user_repo.db.add(user)
        await self.user_repo.db.flush()
        return True

    async def verify_email_address(self, token: str) -> bool:
        """
        Authenticates verification token and sets email verified flag to True.
        """
        from sqlalchemy import select
        res = await self.user_repo.db.execute(
            select(User).where(User.verification_token == token)
        )
        user = res.scalar_or_none()
        if not user:
            raise ValueError("Invalid email verification link.")

        now = datetime.now(timezone.utc)
        if not user.verification_token_expires_at or user.verification_token_expires_at < now:
            raise ValueError("This verification link has expired.")

        user.email_verified = True
        user.verification_token = None
        user.verification_token_expires_at = None

        self.user_repo.db.add(user)
        await self.user_repo.db.flush()
        return True

    async def resend_verification_link(self, email: str) -> bool:
        """
        Regenerates and dispatches a fresh verification link.
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("Account not found.")

        if user.email_verified:
            raise ValueError("This email address is already verified.")

        verification_token = str(uuid.uuid4())
        expiry = datetime.now(timezone.utc) + timedelta(hours=24)

        user.verification_token = verification_token
        user.verification_token_expires_at = expiry

        self.user_repo.db.add(user)
        await self.user_repo.db.flush()

        self.email_svc.send_verification_email(user.email, verification_token)
        return True
