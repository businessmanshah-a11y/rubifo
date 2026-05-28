import asyncpg
from typing import Any, List
from src.config import DATABASE_URL
from src.logger import logger

pool = None


async def init_db() -> None:
    """Initialize asyncpg connection pool with error handling."""
    global pool
    try:
        pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=10,
            max_size=20,
            timeout=30,
            command_timeout=10
        )
        logger.info("Database pool initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        raise


async def close_db() -> None:
    """Close database connection pool gracefully."""
    global pool
    try:
        if pool:
            await pool.close()
            logger.info("Database pool closed successfully")
    except Exception as e:
        logger.error(f"Error closing database pool: {e}")


async def execute(query: str, *args: Any) -> str:
    """Execute a query (INSERT, UPDATE, DELETE) and return result."""
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


async def fetch(query: str, *args: Any) -> List[dict]:
    """Fetch multiple rows as list of dictionaries."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(row) for row in rows]


async def fetchrow(query: str, *args: Any) -> dict:
    """Fetch a single row as dictionary."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None
