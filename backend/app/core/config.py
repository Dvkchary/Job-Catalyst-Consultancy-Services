import os
from enum import Enum
from typing import List, Optional
from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """
    JobCatalyst AI - Global Configuration Settings (Enterprise Base Layer).
    Uses Pydantic v2 to load, validate, and enforce environment-specific properties.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # General Project Settings
    PROJECT_NAME: str = Field(default="JobCatalyst AI API", description="The descriptive name of the system")
    API_V1_STR: str = Field(default="/api/v1", description="Global versioned endpoint prefix")
    PROJECT_VERSION: str = Field(default="1.0.0", description="SemVer version of the backend API")
    ENVIRONMENT: EnvironmentType = Field(default=EnvironmentType.DEVELOPMENT, description="Execution environment")

    # Server Bindings
    SERVER_HOST: str = Field(default="0.0.0.0", description="IP host binding")
    SERVER_PORT: int = Field(default=8000, description="Network port binding")

    # Security & Cryptography
    SECRET_KEY: str = Field(
        default="SUPER_SECRET_REPLACE_ME_BEFORE_PRODUCTION_1234567890",
        description="Core encryption key for signing tokens and sessions"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="Symmetric cryptographic signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Access Token lifespan")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh Token lifespan")

    # CORS & Trusted Hosts
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    TRUSTED_HOSTS: List[str] = Field(
        default=["127.0.0.1", "localhost"],
        description="Allowed host headers to mitigate HTTP Host Header attacks"
    )

    # Database (PostgreSQL) - Provisioned via Cloud SQL in staging/prod
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_DB: str = Field(default="jobcatalyst")
    POSTGRES_POOL_SIZE: int = Field(default=20)
    POSTGRES_MAX_OVERFLOW: int = Field(default=10)

    # Redis Cache & Broker
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: Optional[str] = Field(default=None)

    # AWS S3 Storage Isolation for Resumes
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None)
    AWS_REGION: str = Field(default="us-east-1")
    S3_BUCKET_NAME: str = Field(default="jobcatalyst-resumes")

    # Third-Party API Integrations (Stripe & AI Providers)
    STRIPE_SECRET_KEY: Optional[str] = Field(default=None)
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(default=None)

    GEMINI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)

    # Cost-Control & Rate Limiting Thresholds
    DAILY_TOKEN_QUOTA_PER_USER: int = Field(default=50000, description="Token consumption quota per client IP/User")
    GENERAL_RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Sliding window request threshold")
    AUTH_RATE_LIMIT_PER_MINUTE: int = Field(default=10, description="Strict throttling on authentication gates")

    # Observability & Log Levels
    LOG_LEVEL: str = Field(default="INFO", description="Standard logging verbose filter")
    LOG_JSON_FORMAT: bool = Field(default=False, description="Enable structured logging formatted as JSON")

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("TRUSTED_HOSTS", mode="before")
    @classmethod
    def assemble_trusted_hosts(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["localhost", "127.0.0.1"]

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Helper to generate database connection URL."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def REDIS_URL(self) -> str:
        """Helper to generate Redis connection string."""
        auth_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


# Instantiation of Settings Object (Single Instance Configuration State)
settings = Settings()
