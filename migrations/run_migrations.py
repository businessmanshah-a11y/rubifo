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

        for sql_file in sql_files:
            logger.info(f"Running migration: {sql_file.name}")
            with open(sql_file, "r") as f:
                sql = f.read()

            await conn.execute(sql)
            logger.info(f"Migration {sql_file.name} completed")

        logger.info("All migrations completed successfully")

    except Exception as e:
        logger.error(f"Migration error: {e}")
        raise

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migrations())
