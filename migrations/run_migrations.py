import asyncio
import asyncpg
import os
from pathlib import Path
from src.logger import logger
from src.config import DATABASE_URL


async def run_migrations() -> None:
    """Run all SQL migration files in order."""
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        migrations_dir = Path(__file__).parent
        sql_files = sorted([f for f in migrations_dir.glob("*.sql")])

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename TEXT PRIMARY KEY,
                applied_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
            """
        )

        for sql_file in sql_files:
            already_applied = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM schema_migrations WHERE filename = $1)",
                sql_file.name,
            )
            if already_applied:
                logger.info(f"Skipping migration already applied: {sql_file.name}")
                continue

            logger.info(f"Running migration: {sql_file.name}")
            with open(sql_file, "r") as f:
                sql = f.read()

            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO schema_migrations (filename) VALUES ($1)",
                    sql_file.name,
                )
            logger.info(f"Migration {sql_file.name} completed")

        logger.info("All migrations completed successfully")

    except Exception as e:
        logger.error(f"Migration error: {e}")
        raise

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migrations())
