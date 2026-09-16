import logging
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import BaseAppException

logger = logging.getLogger("app.errors")


class ErrorDetail(BaseModel):
    """Structured details of specific errors (e.g., parameter validation failures)."""
    loc: Optional[List[str]] = Field(default=None, description="Location of the invalid attribute (path/query/body)")
    msg: str = Field(..., description="Human-readable issue description")
    type: str = Field(..., description="Validation type or error subclass identifier")


class ErrorResponse(BaseModel):
    """Centralized standard error structure returned by all JobCatalyst APIs."""
    success: bool = Field(default=False, description="Flag indicating failed request status")
    error_code: str = Field(..., description="Systemic unique string identifier for categorizing errors")
    message: str = Field(..., description="General human-readable error summary")
    details: Optional[List[ErrorDetail]] = Field(default=None, description="Granular property-specific validations list")
    correlation_id: str = Field(..., description="The X-Request-ID tracking context of this transaction")


def register_error_handlers(app: FastAPI) -> None:
    """
    Registers all exception handlers on the FastAPI application instance.
    Standardizes responses for validation, framework, custom, and general system failures.
    """

    @app.exception_handler(BaseAppException)
    async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
        """Handles all domain-specific custom exceptions raised inside our application layer."""
        correlation_id = request.headers.get("X-Request-ID", "-")
        
        # Log warning (4xx client-error) or error (5xx server-error) appropriately
        if exc.status_code >= 500:
            logger.error(f"Application exception {exc.error_code}: {exc.message} | Correlation: {correlation_id}")
        else:
            logger.warning(f"Client request warning {exc.error_code}: {exc.message} | Correlation: {correlation_id}")

        content = ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=[ErrorDetail(msg=v, type="custom_info") for v in exc.details.values()] if isinstance(exc.details, dict) and exc.details else None,
            correlation_id=correlation_id
        ).model_dump()

        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handles Pydantic input body and query parameter validation failures."""
        correlation_id = request.headers.get("X-Request-ID", "-")
        logger.warning(f"Validation failure | URL: {request.url.path} | Correlation: {correlation_id}")

        details: List[ErrorDetail] = []
        for err in exc.errors():
            details.append(
                ErrorDetail(
                    loc=[str(loc_val) for loc_val in err.get("loc", [])],
                    msg=err.get("msg", "Invalid parameter"),
                    type=err.get("type", "value_error")
                )
            )

        content = ErrorResponse(
            error_code="VALIDATION_FAILED",
            message="Request parameters or payload schema validation failed.",
            details=details,
            correlation_id=correlation_id
        ).model_dump()

        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=content)

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handles default Starlette/FastAPI HTTPExceptions (e.g. 404 Route Not Found, 405 Method Not Allowed)."""
        correlation_id = request.headers.get("X-Request-ID", "-")
        logger.warning(f"HTTP exception {exc.status_code} on {request.url.path} | Correlation: {correlation_id}")

        # Map standard status codes to error codes
        error_code = "HTTP_ERROR"
        if exc.status_code == 404:
            error_code = "ENDPOINT_NOT_FOUND"
        elif exc.status_code == 405:
            error_code = "METHOD_NOT_ALLOWED"

        content = ErrorResponse(
            error_code=error_code,
            message=exc.detail,
            correlation_id=correlation_id
        ).model_dump()

        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all handler for completely unexpected internal backend crashes."""
        correlation_id = request.headers.get("X-Request-ID", "-")
        logger.error(f"Critical crash on {request.method} {request.url.path} | Correlation: {correlation_id}", exc_info=exc)

        # Do NOT leak the raw traceback to the client to avoid information disclosure vulnerability
        content = ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected system failure occurred. Please contact support with the correlation ID.",
            correlation_id=correlation_id
        ).model_dump()

        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=content)
