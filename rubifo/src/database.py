"""
Database connection and utilities
"""

import asyncpg
from src.config import DATABASE_URL

pool = None


async def init_db():
    """Initialize database connection pool"""
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)


async def close_db():
    """Close database connection pool"""
    global pool
    if pool:
        await pool.close()


async def get_connection():
    """Get a database connection from the pool"""
    return await pool.acquire()
