import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.core.config import settings


class JWTService:
    """
    Enterprise-grade JSON Web Token (JWT) management service.
    Handles cryptographic signing, verification, and claims checking for Access and Refresh tokens.
    """
    
    def __init__(self) -> None:
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_lifetime = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_lifetime = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(self, user_id: uuid.UUID, roles: List[str]) -> str:
        """
        Generates a short-lived cryptographically signed Access Token.
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.access_lifetime)
        
        claims = {
            "sub": str(user_id),
            "jti": str(uuid.uuid4()),
            "type": "access",
            "roles": roles,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp())
        }
        
        return jwt.encode(claims, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: uuid.UUID) -> Tuple[str, str]:
        """
        Generates a long-lived cryptographically signed Refresh Token.
        Returns a tuple of (token_string, token_jti).
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.refresh_lifetime)
        token_id = str(uuid.uuid4())
        
        claims = {
            "sub": str(user_id),
            "jti": token_id,
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp())
        }
        
        token_str = jwt.encode(claims, self.secret_key, algorithm=self.algorithm)
        return token_str, token_id

    def decode_token(self, token: str) -> Dict[str, any]:
        """
        Decodes and cryptographically verifies claims of a JWT string.
        Raises ExpiredSignatureError or InvalidTokenError on validation failures.
        """
        # pyjwt decode raises ExpiredSignatureError if expired
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

    def verify_token(self, token: str, expected_type: str = "access") -> Dict[str, any]:
        """
        Validates token signature, expiration boundary, and token structural properties.
        """
        try:
            payload = self.decode_token(token)
        except ExpiredSignatureError as e:
            raise ValueError("Token signature has expired.") from e
        except InvalidTokenError as e:
            raise ValueError("Token signature is invalid.") from e

        # Assert token category boundaries
        if payload.get("type") != expected_type:
            raise ValueError(f"Invalid token type. Expected {expected_type}.")

        if not payload.get("sub"):
            raise ValueError("Subject claim (sub) is missing from token payload.")

        if not payload.get("jti"):
            raise ValueError("Unique token identifier (jti) is missing from token payload.")

        return payload
