import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.dependencies import (
    get_authentication_service,
    get_current_active_user,
    require_permission,
)
from app.models.auth import User
from app.schemas.auth import (
    PasswordResetConfirmSchema,
    PasswordResetRequestSchema,
    RefreshTokenRequest,
    TOTPSetupResponse,
    TOTPVerifyRequest,
    TokenResponse,
    UserLogin,
    UserOut,
    UserRegister,
    VerifyEmailRequestSchema,
)
from app.services.authentication import AuthenticationService
from app.services.mfa import MFAService

logger = logging.getLogger("app.api.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegister,
    auth_svc: AuthenticationService = Depends(get_authentication_service),
) -> Any:
    """
    Registers a new user account, creates credentials, and fires verification email.
    """
    try:
        user = await auth_svc.register_user(
            email=payload.email,
            username=payload.username,
            password=payload.password,
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    payload: UserLogin,
    auth_svc: AuthenticationService = Depends(get_authentication_service),
) -> Any:
    """
    Authenticates account credentials, logs device details, and returns JWT session tokens.
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        _, access_token, refresh_token = await auth_svc.authenticate_user(
            identity=payload.identity,
            password=payload.password,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e


@router.post("/refresh", response_model=TokenResponse)
async def refresh_session(
    request: Request,
    payload: RefreshTokenRequest,
    auth_svc: AuthenticationService = Depends(get_authentication_service),
) -> Any:
    """
    Executes Refresh Token Rotation (RTR). Returns rotated token pair.
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        new_access, new_refresh = await auth_svc.rotate_refresh_token(
            refresh_token=payload.refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    payload: RefreshTokenRequest,
    current_user: User = Depends(get_current_active_user),
    auth_svc: AuthenticationService = Depends(get_authentication_service),
) -> Any:
    """
    Deactivates current device session and blacklists Access Token JTI.
    """
    access_jti = getattr(current_user, "current_token_jti", None)
    await auth_svc.terminate_session(
        refresh_token=payload.refresh_token,
        access_token_jti=access_jti,
    )
    return {"detail": "Successfully logged out of current device session."}


@router.post("/logout-all", status_code=status.HTTP_200_OK)
async def logout_all_devices(
    current_user: User = Depends(get_current_active_user),
    auth_svc: AuthenticationService = Depends(get_authentication_service),
) -> Any:
    """
    Centralized remote logout. Revokes all active sessions for this account.
    """
    await auth_svc.session_repo.deactivate_all_by_user_id(current_user.id)
    return {"detail": "Successfully logged out of all active devices."}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    payload: PasswordResetRequestSchema,
    auth_svc: AuthenticationService = Depends(get_authentication_service),
) -> Any:
    """
    Triggers password recovery. Dispatches secure link to owner if registered.
    """
    await auth_svc.request_password_reset(email=payload.email)
    return {"detail": "If the email is registered, a password recovery link has been dispatched."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    payload: PasswordResetConfirmSchema,
    auth_svc: AuthenticationService = Depends(get_authentication_service),
) -> Any:
    """
    Validates reset token and saves updated, re-hashed credentials.
    """
    try:
        await auth_svc.reset_password(
            reset_token=payload.token,
            new_password=payload.new_password,
        )
        return {"detail": "Credentials updated successfully. All devices logged out."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    payload: VerifyEmailRequestSchema,
    auth_svc: AuthenticationService = Depends(get_authentication_service),
) -> Any:
    """
    Saves verified status on profile matching active activation token.
    """
    try:
        await auth_svc.verify_email_address(token=payload.token)
        return {"detail": "Email verified successfully. Account fully activated."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(
    payload: PasswordResetRequestSchema,  # reuse email schema
    auth_svc: AuthenticationService = Depends(get_authentication_service),
) -> Any:
    """
    Regenerates and resends registration email link.
    """
    try:
        await auth_svc.resend_verification_link(email=payload.email)
        return {"detail": "Verification link has been resent successfully."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/me", response_model=UserOut)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieves the authenticated active user profile details.
    """
    return current_user


# ==============================================================================
# Multi-Factor Authentication (TOTP Ready) Routes
# ==============================================================================

@router.post("/mfa/setup", response_model=TOTPSetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_active_user),
    auth_svc: AuthenticationService = Depends(get_authentication_service),
) -> Any:
    """
    Initializes MFA configuration. Generates a secret seed and QR Uri.
    """
    if current_user.mfa_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is already enabled on this account.")

    secret = MFAService.generate_totp_secret()
    uri = MFAService.get_totp_provisioning_uri(secret, current_user.email)

    # Save secret temporarily (unverified)
    current_user.mfa_secret = secret
    auth_svc.user_repo.db.add(current_user)
    await auth_svc.user_repo.db.flush()

    return TOTPSetupResponse(
        secret=secret,
        provisioning_uri=uri,
    )


@router.post("/mfa/enable", status_code=status.HTTP_200_OK)
async def enable_mfa(
    payload: TOTPVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    auth_svc: AuthenticationService = Depends(get_authentication_service),
) -> Any:
    """
    Validates setup token. Activates account MFA state and issues recovery backup codes.
    """
    if current_user.mfa_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is already enabled.")

    if not current_user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA setup has not been initialized.")

    # Validate incoming verification code
    is_valid = MFAService.verify_totp_code(current_user.mfa_secret, payload.code)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP code. Setup failed.")

    # Set flag and issue recovery codes
    current_user.mfa_enabled = True
    recovery_codes = MFAService.generate_recovery_codes()
    # Save recovery codes as comma-separated
    current_user.mfa_recovery_codes = ",".join(recovery_codes)

    auth_svc.user_repo.db.add(current_user)
    await auth_svc.user_repo.db.flush()

    return {
        "detail": "Multi-Factor Authentication enabled successfully.",
        "recovery_codes": recovery_codes,
    }


@router.post("/mfa/disable", status_code=status.HTTP_200_OK)
async def disable_mfa(
    payload: TOTPVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    auth_svc: AuthenticationService = Depends(get_authentication_service),
) -> Any:
    """
    Disables MFA after validating current OTP token to confirm ownership.
    """
    if not current_user.mfa_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not enabled.")

    is_valid = MFAService.verify_totp_code(current_user.mfa_secret, payload.code)
    # Check recovery code bypass too!
    if not is_valid and current_user.mfa_recovery_codes:
        codes = current_user.mfa_recovery_codes.split(",")
        if payload.code.strip() in codes:
            is_valid = True
            # Remove used recovery code
            codes.remove(payload.code.strip())
            current_user.mfa_recovery_codes = ",".join(codes)

    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code.")

    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    current_user.mfa_recovery_codes = None

    auth_svc.user_repo.db.add(current_user)
    await auth_svc.user_repo.db.flush()

    return {"detail": "Multi-Factor Authentication disabled successfully."}
