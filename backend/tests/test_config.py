from app.core.config import Settings, EnvironmentType


def test_default_settings():
    """Verifies that core system defaults are correctly defined and initializable."""
    settings = Settings()
    assert settings.PROJECT_NAME == "JobCatalyst AI API"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.SERVER_HOST == "0.0.0.0"
    assert settings.SERVER_PORT == 8000
    assert settings.ENVIRONMENT == EnvironmentType.DEVELOPMENT


def test_cors_origin_parsing():
    """Verifies that ALLOWED_ORIGINS comma-separated values are correctly parsed into a list."""
    settings = Settings(ALLOWED_ORIGINS="http://domain-a.com, http://domain-b.com")
    assert settings.ALLOWED_ORIGINS == ["http://domain-a.com", "http://domain-b.com"]


def test_trusted_hosts_parsing():
    """Verifies that TRUSTED_HOSTS comma-separated values are correctly parsed into a list."""
    settings = Settings(TRUSTED_HOSTS="domain-a.com, domain-b.com")
    assert settings.TRUSTED_HOSTS == ["domain-a.com", "domain-b.com"]


def test_database_and_redis_uris():
    """Verifies the proper compilation of SQLAlchemy and Redis connection URIs."""
    settings = Settings(
        POSTGRES_USER="test_user",
        POSTGRES_PASSWORD="test_password",
        POSTGRES_HOST="test_host",
        POSTGRES_PORT=5432,
        POSTGRES_DB="test_db",
        REDIS_HOST="test_redis",
        REDIS_PORT=6379,
        REDIS_DB=1
    )
    assert settings.SQLALCHEMY_DATABASE_URI == "postgresql+asyncpg://test_user:test_password@test_host:5432/test_db"
    assert settings.REDIS_URL == "redis://test_redis:6379/1"
