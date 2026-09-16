import os
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import settings

# Force settings TRUSTED_HOSTS to include the test server host header
if "testserver" not in settings.TRUSTED_HOSTS:
    settings.TRUSTED_HOSTS.append("testserver")


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Overrides default environment properties to safeguard unit testing states."""
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["LOG_JSON_FORMAT"] = "False"
    os.environ["SECRET_KEY"] = "MOCK_UNIT_TEST_SECRET_KEY_JWT_1234567890"
    yield
    # Cleanup env changes if necessary
    os.environ.pop("ENVIRONMENT", None)


@pytest.fixture
def client():
    """Provides a thread-safe, synchronous test client for FastAPI router evaluations."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
