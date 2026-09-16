from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.exceptions import NotFoundException, AuthorizationException


def test_request_id_and_security_headers(client: TestClient):
    """
    Verifies that the Request ID Middleware generates tracking headers,
    and the Security Headers Middleware applies robust defense guidelines.
    """
    response = client.get("/")
    assert response.status_code == 200
    
    # 1. Assert correlation headers exist and look like a UUIDv4
    assert "X-Request-ID" in response.headers
    req_id = response.headers["X-Request-ID"]
    assert len(req_id) == 36  # Length of UUIDv4 string representation
    
    # 2. Assert standard security headers are attached
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_api_endpoint_cache_busting_headers(client: TestClient):
    """Verifies that public API routes set browser cache-busting directives."""
    # /api/v1/version matches the /api/ prefix trigger
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    assert "Cache-Control" in response.headers
    assert "no-store" in response.headers["Cache-Control"]
    assert response.headers["Pragma"] == "no-cache"


def test_custom_domain_exception_handling():
    """
    Verifies that custom application exceptions (like NotFoundException)
    are intercepted and formatted according to our standard ErrorResponse contract.
    """
    app = create_app()
    
    # Define an ephemeral test route that intentionally raises a custom error
    @app.get("/test-raise-not-found")
    async def trigger_not_found():
        raise NotFoundException("Specific resource was not found in database.")

    client = TestClient(app)
    response = client.get("/test-raise-not-found")
    
    assert response.status_code == 404
    data = response.json()
    
    assert data["success"] is False
    assert data["error_code"] == "RESOURCE_NOT_FOUND"
    assert "Specific resource was not found" in data["message"]
    assert "correlation_id" in data
    assert len(data["correlation_id"]) == 36


def test_unhandled_crash_exception_handling():
    """
    Verifies that general unhandled server-side code crashes are intercepted,
    formatted as structured JSON, and that sensitive traceback details are masked.
    """
    app = create_app()

    # Define an ephemeral test route that crashes with an unhandled ZeroDivisionError
    @app.get("/test-raise-crash")
    async def trigger_crash():
        return 1 / 0

    client = TestClient(app)
    response = client.get("/test-raise-crash")
    
    assert response.status_code == 500
    data = response.json()
    
    # Assert tracebacks are masked and user sees standard message
    assert data["success"] is False
    assert data["error_code"] == "INTERNAL_SERVER_ERROR"
    assert "unexpected system failure" in data["message"]
    assert "ZeroDivisionError" not in data["message"]  # Strict security check (No leaks!)
    assert "correlation_id" in data
