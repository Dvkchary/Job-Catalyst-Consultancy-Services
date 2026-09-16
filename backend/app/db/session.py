import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
import orjson
from app.core.config import settings

logger = logging.getLogger("app.db.session")

# ==============================================================================
# Connection Pool & Engine Configuration
# ==============================================================================
# We define timeouts and validation parameters to prevent stale connections,
# especially in serverless environments like Google Cloud Run.
POSTGRES_POOL_RECYCLE = 1800  # Recycle connections after 30 minutes
POSTGRES_POOL_TIMEOUT = 30    # Max seconds to wait for a connection from pool
POSTGRES_PRE_PING = True      # Connection validation before checkout (pre-ping)

def _orjson_dumps(v):
    return orjson.dumps(v).decode("utf-8")

def create_db_engine(database_url: str) -> AsyncEngine:
    """
    Factory function to initialize a high-performance AsyncEngine.
    """
    logger.info("Initializing async database engine...")
    try:
        engine = create_async_engine(
            database_url,
            pool_size=settings.POSTGRES_POOL_SIZE,
            max_overflow=settings.POSTGRES_MAX_OVERFLOW,
            pool_recycle=POSTGRES_POOL_RECYCLE,
            pool_timeout=POSTGRES_POOL_TIMEOUT,
            pool_pre_ping=POSTGRES_PRE_PING,
            json_serializer=_orjson_dumps,
            json_deserializer=orjson.loads,
            echo=False,  # Set to True only for heavy query debugging in development
        )
        return engine
    except Exception as e:
        logger.critical(f"Failed to instantiate SQLAlchemy engine: {str(e)}")
        raise e


# Instantiate the global asynchronous engine
async_engine: AsyncEngine = create_db_engine(settings.SQLALCHEMY_DATABASE_URI)

# Instantiate the thread-safe session maker
async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ==============================================================================
# Async Session Dependency
# ==============================================================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding an isolated, transaction-scoped AsyncSession.
    Ensures safe resource reclamation and automatic rollbacks on failure.
    """
    session: AsyncSession = async_session_maker()
    logger.debug("Database async session created.")
    try:
        yield session
    except Exception as e:
        logger.warning(f"Database session encountered error, initiating rollback: {str(e)}")
        await session.rollback()
        raise e
    finally:
        logger.debug("Closing database async session.")
        await session.close()
