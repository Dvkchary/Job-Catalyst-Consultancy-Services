import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.models.auth import Role, User, UserSession
from app.services.authorization import AuthorizationService
from app.services.jwt import JWTService
from app.services.mfa import MFAService
from app.services.password import PasswordService
from app.services.authentication import AuthenticationService


# ==============================================================================
# 1. Password Security Service Tests
# ==============================================================================
def test_password_service_hashing():
    pwd_svc = PasswordService()
    pwd = "Secr3t_Pa$$word!"
    
    hashed = pwd_svc.hash_password(pwd)
    assert hashed != pwd
    assert hashed.startswith("$argon2")
    
    assert pwd_svc.verify_password(hashed, pwd) is True
    assert pwd_svc.verify_password(hashed, "wrong_password") is False


def test_password_complexity_validator():
    pwd_svc = PasswordService()
    
    # Too short
    ok, msg = pwd_svc.validate_password_strength("Short1!")
    assert ok is False
    assert "at least 8" in msg

    # Missing uppercase
    ok, msg = pwd_svc.validate_password_strength("lowercase123!")
    assert ok is False
    assert "uppercase" in msg

    # Missing lowercase
    ok, msg = pwd_svc.validate_password_strength("UPPERCASE123!")
    assert ok is False
    assert "lowercase" in msg

    # Missing numerical digit
    ok, msg = pwd_svc.validate_password_strength("NoNumbersHere!")
    assert ok is False
    assert "numerical" in msg

    # Missing special character
    ok, msg = pwd_svc.validate_password_strength("NoSpecialChar123")
    assert ok is False
    assert "special character" in msg

    # Perfect strength
    ok, msg = pwd_svc.validate_password_strength("St0ng_P@ss!")
    assert ok is True


# ==============================================================================
# 2. JWT Cryptographic Service Tests
# ==============================================================================
def test_jwt_service_issuance_and_verification():
    jwt_svc = JWTService()
    user_id = uuid.uuid4()
    roles = ["USER"]

    # Test Access Token
    access_token = jwt_svc.create_access_token(user_id, roles)
    payload = jwt_svc.verify_token(access_token, expected_type="access")
    
    assert payload["sub"] == str(user_id)
    assert payload["roles"] == roles
    assert payload["type"] == "access"

    # Test Refresh Token
    refresh_token, jti = jwt_svc.create_refresh_token(user_id)
    payload_refresh = jwt_svc.verify_token(refresh_token, expected_type="refresh")
    
    assert payload_refresh["sub"] == str(user_id)
    assert payload_refresh["type"] == "refresh"
    assert payload_refresh["jti"] == jti


def test_jwt_invalid_signature_or_expired():
    jwt_svc = JWTService()
    
    # Invalid Signature Test
    with pytest.raises(ValueError, match="signature is invalid"):
        jwt_svc.verify_token("invalid_token_string")

    # Wrong Token Type Test
    user_id = uuid.uuid4()
    access_token = jwt_svc.create_access_token(user_id, ["USER"])
    with pytest.raises(ValueError, match="Invalid token type"):
        jwt_svc.verify_token(access_token, expected_type="refresh")


# ==============================================================================
# 3. RBAC & Matrix Authorization Tests
# ==============================================================================
def test_rbac_matrix_evaluations():
    auth_svc = AuthorizationService()

    # User Permissions check
    user_perms = auth_svc.get_permissions_for_roles(["USER"])
    assert "resumes:read" in user_perms
    assert "admin:all" not in user_perms

    assert auth_svc.has_permission(["USER"], "resumes:read") is True
    assert auth_svc.has_permission(["USER"], "coach:session") is False

    # Recruiter Permissions check
    assert auth_svc.has_permission(["RECRUITER"], "jobs:create") is True
    assert auth_svc.has_permission(["RECRUITER"], "coach:session") is False

    # Admin wildcard overrides
    assert auth_svc.has_permission(["ADMIN"], "coach:session") is True
    assert auth_svc.has_permission(["ADMIN"], "user:delete") is True


# ==============================================================================
# 4. Multi-Factor (TOTP Ready) Service Tests
# ==============================================================================
def test_mfa_setup_and_verification():
    secret = MFAService.generate_totp_secret()
    assert len(secret) == 32
    
    uri = MFAService.get_totp_provisioning_uri(secret, "user@test.com")
    assert "otpauth://totp" in uri
    assert "user%40test.com" in uri

    # Verify backup codes are formatted correctly
    codes = MFAService.generate_recovery_codes(count=5)
    assert len(codes) == 5
    for c in codes:
        assert len(c) == 14  # XXXX-XXXX-XXXX format
        assert "-" in c


# ==============================================================================
# 5. Core Authentication Service Flows (Mocks Integration)
# ==============================================================================
@pytest.mark.asyncio
async def test_user_lockout_after_failed_attempts():
    """Verifies user account transitions to locked state after 5 failed authentication attempts."""
    mock_user = User(
        id=uuid.uuid4(),
        email="test_lockout@test.com",
        username="lockout_user",
        password_hash="argon_hash",
        status="ACTIVE",
        failed_login_attempts=4,  # Next failure will trigger lockout
        locked_until=None
    )
    
    # Repositories mocks
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_email = AsyncMock(return_value=mock_user)
    
    mock_password_svc = MagicMock()
    mock_password_svc.verify_password.return_value = False  # Always fail
    
    auth_svc = AuthenticationService(
        user_repo=mock_user_repo,
        role_repo=MagicMock(),
        session_repo=MagicMock(),
        revocation_repo=MagicMock(),
        password_svc=mock_password_svc,
        jwt_svc=MagicMock(),
        email_svc=MagicMock(),
    )
    
    with pytest.raises(ValueError, match="Account locked"):
        await auth_svc.authenticate_user(
            identity="test_lockout@test.com",
            password="wrong_password"
        )
        
    assert mock_user.status == "LOCKED"
    assert mock_user.locked_until is not None
    assert mock_user.failed_login_attempts == 5
