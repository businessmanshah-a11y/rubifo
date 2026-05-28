"""Migration ledger coverage for the publishing-program release."""

from unittest.mock import AsyncMock

import pytest

from migrations import run_migrations


class _Transaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _LegacyDatabase:
    def __init__(self):
        self.applied = set()
        self.executed = []

    async def execute(self, sql, *args):
        self.executed.append((sql, args))
        if "INSERT INTO schema_migrations" in sql and args:
            self.applied.add(args[0])

    async def fetchval(self, sql, *args):
        if "to_regclass" in sql:
            return True
        if "COUNT(*) FROM schema_migrations" in sql:
            return len(self.applied)
        if "SELECT EXISTS" in sql:
            return args[0] in self.applied
        raise AssertionError(f"Unexpected fetchval: {sql}")

    def transaction(self):
        return _Transaction()

    async def close(self):
        return None


@pytest.mark.asyncio
async def test_purge_migration_runs_only_once_on_existing_database(monkeypatch):
    database = _LegacyDatabase()
    monkeypatch.setattr(run_migrations.asyncpg, "connect", AsyncMock(return_value=database))

    await run_migrations.run_migrations()
    await run_migrations.run_migrations()

    purge_executions = [
        sql for sql, _args in database.executed if "TRUNCATE TABLE transactions" in sql
    ]
    assert len(purge_executions) == 1
    assert "010_publishing_program_onboarding.sql" in database.applied

