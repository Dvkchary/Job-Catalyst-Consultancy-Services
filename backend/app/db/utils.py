import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable, TypeVar, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import async_session_maker, async_engine

logger = logging.getLogger("app.db.utils")

RT = TypeVar("RT")


@asynccontextmanager
async def transaction_scope() -> AsyncGenerator[AsyncSession, None]:
    """
    Asynchronous context manager to guarantee atomic operations.
    If any block fails within the context, the session is rolled back.
    Otherwise, changes are committed upon exit.
    """
    session = async_session_maker()
    try:
        yield session
        await session.commit()
    except Exception as e:
        logger.error(f"Transaction failed, rolling back session: {str(e)}")
        await session.rollback()
        raise e
    finally:
        await session.close()


async def verify_db_connection() -> bool:
    """
    Executes a simple raw SQL command on the async connection pool
    to validate that PostgreSQL is awake and receptive.
    """
    try:
        async with async_session_maker() as session:
            # We run a low-overhead SELECT 1 ping query
            result = await session.execute(text("SELECT 1"))
            val = result.scalar()
            return val == 1
    except Exception as e:
        logger.error(f"Database connection validation failed: {str(e)}")
        return False


async def with_retry(
    func: Callable[..., RT],
    retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    *args: Any,
    **kwargs: Any
) -> RT:
    """
    Executes a database operations block with exponential backoff retry.
    Particularly useful to combat ephemeral network failures or serverless cold starts.
    """
    delay = initial_delay
    last_error: Optional[Exception] = None

    for attempt in range(1, retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_error = e
            logger.warning(
                f"Database operation failed on attempt {attempt}/{retries}. "
                f"Retrying in {delay}s. Error: {str(e)}"
            )
            if attempt == retries:
                break
            await asyncio.sleep(delay)
            delay *= backoff_factor

    raise last_error or Exception("Retry operation failed without recording exception.")
