from typing import Any, Dict, Optional


class BaseAppException(Exception):
    """
    Core Exception Base class for JobCatalyst AI.
    All application, repository, service, and custom business layer exceptions inherit from this.
    """
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class NotFoundException(BaseAppException):
    """Raised when a requested resource (user, resume, job) does not exist."""
    def __init__(self, message: str, error_code: str = "RESOURCE_NOT_FOUND", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, error_code=error_code, status_code=404, details=details)


class AuthenticationException(BaseAppException):
    """Raised when authentication credentials fail, expire, or are missing."""
    def __init__(self, message: str = "Authentication failed", error_code: str = "AUTHENTICATION_FAILED", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, error_code=error_code, status_code=401, details=details)


class AuthorizationException(BaseAppException):
    """Raised when user permissions or resource ownership validation fails."""
    def __init__(self, message: str = "Insufficient permissions", error_code: str = "AUTHORIZATION_FAILED", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, error_code=error_code, status_code=403, details=details)


class ValidationException(BaseAppException):
    """Raised when incoming parameters or document structures fail validation criteria."""
    def __init__(self, message: str, error_code: str = "VALIDATION_FAILED", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, error_code=error_code, status_code=422, details=details)


class RateLimitException(BaseAppException):
    """Raised when a client exceeds traffic rate-limiting or AI budget consumption."""
    def __init__(self, message: str = "Rate limit exceeded", error_code: str = "RATE_LIMIT_EXCEEDED", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, error_code=error_code, status_code=429, details=details)


class ExternalServiceException(BaseAppException):
    """Raised when third-party gateways (Stripe, OpenAI, Gemini) return errors."""
    def __init__(self, message: str, error_code: str = "EXTERNAL_SERVICE_FAILURE", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, error_code=error_code, status_code=502, details=details)


class ConfigurationException(Exception):
    """Raised on critical configuration or startup failures."""
    pass
