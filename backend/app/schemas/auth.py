import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Payload for signing up a new user account."""
    email: EmailStr = Field(..., description="A valid, unique email address")
    username: str = Field(..., min_length=3, max_length=50, description="A unique username")
    password: str = Field(..., min_length=8, description="A strong, complex password")


class UserLogin(BaseModel):
    """Payload for establishing account credentials session."""
    identity: str = Field(..., description="The user's registered email or username")
    password: str = Field(..., description="The user's password credentials")


class UserOut(BaseModel):
    """The public/secure output model for user profiles."""
    id: uuid.UUID
    email: str
    username: str
    status: str
    email_verified: bool
    mfa_enabled: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Successful authentication response payload."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class RefreshTokenRequest(BaseModel):
    """Payload for rotating active session JWTs."""
    refresh_token: str


class PasswordResetRequestSchema(BaseModel):
    """Payload to initiate a password recovery invitation email."""
    email: EmailStr


class PasswordResetConfirmSchema(BaseModel):
    """Payload to establish new credentials via recovery token."""
    token: str
    new_password: str = Field(..., min_length=8)


class VerifyEmailRequestSchema(BaseModel):
    """Payload to verify account state using verification token."""
    token: str


class TOTPSetupResponse(BaseModel):
    """Response payload for initiating MFA configuration."""
    secret: str
    provisioning_uri: str


class TOTPVerifyRequest(BaseModel):
    """Payload for validating a Time-Based One-Time Password."""
    code: str
