from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.error_handlers import register_error_handlers
from app.core.health import evaluate_system_health, OverallHealthResponse
from app.middleware.standard import RequestIDAndTimingMiddleware, SecurityHeadersMiddleware
from app.core.cache_pool import HTTPClientProvider

import logging

logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages the application lifecycle lifespan events (Startup and Shutdown).
    Ensures safe, asynchronous setup of resources and log systems.
    """
    # 1. Startup phase
    setup_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} in environment: {settings.ENVIRONMENT.value}")
    logger.info(f"Loaded configuration settings. Version: {settings.PROJECT_VERSION}")
    
    try:
        yield
    finally:
        # 2. Shutdown phase
        logger.info(f"Shutting down {settings.PROJECT_NAME}...")
        try:
            await HTTPClientProvider.close_client()
        except Exception as e:
            logger.error(f"Error closing shared HTTP connection pool during shutdown: {str(e)}")


def create_app() -> FastAPI:
    """
    FastAPI Application Factory.
    Assembles, configures, and returns the production-grade API gateway instance.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description="Core API Gateway for JobCatalyst AI resume and job search matching.",
        lifespan=lifespan,
        docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
        redoc_url=None if settings.ENVIRONMENT == "production" else "/redoc",
        openapi_url=None if settings.ENVIRONMENT == "production" else "/openapi.json",
        default_response_class=ORJSONResponse
    )

    # ==============================================================================
    # Register Core Middlewares (Executed bottom-to-top)
    # ==============================================================================
    
    # 1. Trusted Host (Mitigates HTTP Host Header attacks)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.TRUSTED_HOSTS
    )

    # 2. CORS Policies
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )

    # 3. GZip Compression (Reduces outgoing bandwidth load)
    app.add_middleware(
        GZipMiddleware,
        minimum_size=1024  # Compress responses larger than 1KB
    )

    # 4. In-Memory Request ID Injector and Latency Logger
    app.add_middleware(RequestIDAndTimingMiddleware)

    # 5. Browser Security Defensive Headers
    app.add_middleware(SecurityHeadersMiddleware)

    # ==============================================================================
    # Register Global Handlers and Schemas
    # ==============================================================================
    register_error_handlers(app)

    # ==============================================================================
    # Core Infrastructure Probe & Version Routes (Self-Contained)
    # ==============================================================================

    @app.get("/", tags=["System"], include_in_schema=False)
    async def root_gateway() -> JSONResponse:
        """Standard welcoming JSON landing message."""
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Welcome to the {settings.PROJECT_NAME} gateway.",
                "status": "UP",
                "version": settings.PROJECT_VERSION
            }
        )

    @app.get("/live", tags=["Health"], status_code=status.HTTP_200_OK)
    async def liveness_probe() -> JSONResponse:
        """
        Liveness Probe.
        Simplest endpoint to verify that the webserver process is running.
        Does not check external DBs, just liveness.
        """
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "UP", "message": "Service process is alive."}
        )

    @app.get("/ready", tags=["Health"], status_code=status.HTTP_200_OK)
    async def readiness_probe() -> JSONResponse:
        """
        Readiness Probe.
        Verifies that the server is ready to handle incoming public requests.
        Can be extended to return 503 if the database connection pool is completely dead.
        """
        # Under normal startup operations, return UP.
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "UP", "message": "Service is ready to handle connections."}
        )

    @app.get("/health", response_model=OverallHealthResponse, tags=["Health"])
    async def system_health() -> OverallHealthResponse:
        """
        Deep System Diagnostics Check.
        Fetches internal CPU/RAM and performs active sub-component availability pings.
        """
        health_data = await evaluate_system_health(settings)
        return health_data

    # ==============================================================================
    # Register Module v1 API Routers
    # ==============================================================================
    from app.api.v1.endpoints.auth import router as auth_router
    from app.api.v1.endpoints.profile import router as profile_router
    from app.api.v1.endpoints.resume import router as resume_router
    from app.api.v1.endpoints.resume_analysis import router as resume_analysis_router
    from app.api.v1.endpoints.ats import router as ats_router
    from app.api.v1.endpoints.job import router as job_router
    from app.api.v1.endpoints.matching import router as matching_router
    from app.api.v1.endpoints.interview import router as interview_router
    from app.api.v1.endpoints.career import router as career_router
    from app.api.v1.endpoints.dashboard import router as dashboard_router
    from app.api.v1.endpoints.notification import router as notification_router
    from app.api.v1.endpoints.admin import router as admin_router
    from app.api.v1.endpoints.workflow import router as workflow_router
    from app.api.v1.endpoints.career_os import router as career_os_router

    app.include_router(auth_router, prefix=settings.API_V1_STR)
    app.include_router(profile_router, prefix=settings.API_V1_STR)
    app.include_router(resume_router, prefix=settings.API_V1_STR)
    app.include_router(resume_analysis_router, prefix=settings.API_V1_STR)
    app.include_router(ats_router, prefix=settings.API_V1_STR)
    app.include_router(job_router, prefix=settings.API_V1_STR)
    app.include_router(matching_router, prefix=settings.API_V1_STR)
    app.include_router(interview_router, prefix=settings.API_V1_STR)
    app.include_router(career_router, prefix=settings.API_V1_STR)
    app.include_router(dashboard_router, prefix=settings.API_V1_STR)
    app.include_router(notification_router, prefix=settings.API_V1_STR)
    app.include_router(admin_router, prefix=settings.API_V1_STR)
    app.include_router(workflow_router, prefix=settings.API_V1_STR)
    app.include_router(career_os_router, prefix=settings.API_V1_STR)

    @app.get(f"{settings.API_V1_STR}/version", tags=["System"], status_code=status.HTTP_200_OK)
    async def get_version_details() -> JSONResponse:
        """Returns the current software version metadata in the version structure."""
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "project": settings.PROJECT_NAME,
                "version": settings.PROJECT_VERSION,
                "api_prefix": settings.API_V1_STR,
                "environment": settings.ENVIRONMENT.value
            }
        )

    return app


# Create the runnable ASGI application instance
app = create_app()
