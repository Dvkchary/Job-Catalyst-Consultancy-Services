import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from app.core.logging_config import correlation_id_ctx
import logging

logger = logging.getLogger("app.middleware")


class RequestIDAndTimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures every inbound request has a unique Request/Correlation ID.
    Injects 'X-Request-ID' into headers, maps it to the thread/async context logging engine,
    and calculates/logs total HTTP request duration.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()

        # Extract request ID from client headers if present, or generate a clean UUIDv4
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Bind the correlation ID to the logging context manager
        token = correlation_id_ctx.set(request_id)

        try:
            response = await call_next(request)
            
            # Attach correlation ID to outbound client headers
            response.headers["X-Request-ID"] = request_id
            
            # Log successful request completion and timing metric
            duration = time.perf_counter() - start_time
            logger.info(
                f"{request.method} {request.url.path} - HTTP {response.status_code} "
                f"(Duration: {duration:.4f}s)",
                extra={"extra_info": {"method": request.method, "path": request.url.path, "status": response.status_code, "duration_seconds": duration}}
            )
            return response

        except Exception as e:
            # Log any unhandled exception in downstream routing logic
            duration = time.perf_counter() - start_time
            logger.exception(
                f"Unhandled router error during {request.method} {request.url.path} after {duration:.4f}s: {str(e)}"
            )
            raise e
        finally:
            # Always clean up the correlation ID context token to prevent memory leak / cross-contamination
            correlation_id_ctx.reset(token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Enforces secure-by-default standard browser headers on all outgoing responses.
    Mitigates Clickjacking, MIME-sniffing, XSS, and Referrer leaks.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # Clickjacking mitigation
        response.headers["X-Frame-Options"] = "DENY"
        
        # MIME-sniffing mitigation
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Cross-site scripting filter
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer disclosure mitigation
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Strict Transport Security (HSTS) - enforce HTTPS
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Content Security Policy (CSP) - restrict resource loading
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; object-src 'none';"
        
        # Disable cache for authenticated/private endpoints to prevent local storage caching
        if "/api/" in request.url.path:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            
        return response
