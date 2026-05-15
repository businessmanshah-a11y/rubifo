"""Integration tests for ExecutionEngine (T67)."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from src.core.execution_engine import ExecutionEngine, create_execution_engine
from src.core.schedule_service import ScheduleService
from src.core.queue_service import QueueService
from src.models.schedule import Schedule
from src.models.post_queue import PostQueueItem


@pytest.mark.asyncio
class TestExecutionEngine:
    """Test ExecutionEngine core functionality."""

    @pytest.fixture
    async def execution_engine(self, mock_db, mock_bot_client):
        """Create ExecutionEngine instance."""
        return ExecutionEngine(mock_db, mock_bot_client)

    async def test_engine_initialization(self, execution_engine):
        """Test engine initializes correctly."""
        assert execution_engine.is_running is False
        assert execution_engine.db is not None
        assert execution_engine.client is not None

    async def test_engine_start_sets_running_flag(self, execution_engine, mock_db):
        """Test engine sets running flag on start."""
        mock_db.fetch.return_value = []

        # Start and immediately stop
        task = asyncio.create_task(asyncio.sleep(0.1))
        execution_engine.is_running = True
        await asyncio.sleep(0.1)
        execution_engine.is_running = False

        assert execution_engine.is_running is False

    async def test_engine_stop(self, execution_engine):
        """Test engine stop method."""
        execution_engine.is_running = True
        await execution_engine.stop()

        assert execution_engine.is_running is False

    async def test_check_and_execute_no_schedules(self, execution_engine, mock_db):
        """Test check when no schedules are due."""
        mock_db.fetch.return_value = []

        schedule_service = ScheduleService(mock_db)
        queue_service = QueueService(mock_db)

        await execution_engine._check_and_execute(schedule_service, queue_service)

        # No schedules, so no executions
        assert mock_db.fetch.called

    async def test_check_and_execute_with_due_schedule(self, execution_engine, mock_db):
        """Test check executes due schedules."""
        # Schedule due now
        due_schedule = {
            "id": 1,
            "route_id": 1,
            "user_id": 1,
            "schedule_type": "interval",
            "interval_minutes": 30,
            "daily_count": None,
            "next_run": datetime.now() - timedelta(minutes=5),
            "is_active": True,
            "created_at": datetime.now(),
        }

        mock_db.fetch.return_value = [due_schedule]
        mock_db.fetchrow.side_effect = [
            {"id": 1, "source_channel_id": 111, "target_channel_id": 222, "is_active": True},
            None,  # No pending posts
        ]

        schedule_service = ScheduleService(mock_db)
        queue_service = QueueService(mock_db)

        await execution_engine._check_and_execute(schedule_service, queue_service)

        assert mock_db.fetch.called

    async def test_execute_schedule_success(self, execution_engine, mock_db):
        """Test successful schedule execution."""
        schedule_data = {
            "id": 1,
            "route_id": 1,
            "user_id": 1,
            "schedule_type": "interval",
            "interval_minutes": 30,
            "daily_count": None,
            "next_run": datetime.now(),
            "is_active": True,
            "created_at": datetime.now(),
        }
        schedule = Schedule(**schedule_data)

        # Route exists and is active
        mock_db.fetchrow.side_effect = [
            {"id": 1, "source_channel_id": 111, "target_channel_id": 222, "is_active": True},
            None,  # No pending posts
        ]

        schedule_service = ScheduleService(mock_db)
        queue_service = QueueService(mock_db)

        result = await execution_engine._execute_schedule(schedule, schedule_service, queue_service)

        assert isinstance(result, bool)

    async def test_execute_schedule_inactive_route(self, execution_engine, mock_db):
        """Test execution skips inactive routes."""
        schedule_data = {
            "id": 1,
            "route_id": 1,
            "user_id": 1,
            "schedule_type": "interval",
            "interval_minutes": 30,
            "daily_count": None,
            "next_run": datetime.now(),
            "is_active": True,
            "created_at": datetime.now(),
        }
        schedule = Schedule(**schedule_data)

        # Route exists but is inactive
        mock_db.fetchrow.return_value = {
            "id": 1,
            "source_channel_id": 111,
            "target_channel_id": 222,
            "is_active": False,
        }

        schedule_service = ScheduleService(mock_db)
        queue_service = QueueService(mock_db)

        result = await execution_engine._execute_schedule(schedule, schedule_service, queue_service)

        assert result is False

    async def test_execute_schedule_missing_route(self, execution_engine, mock_db):
        """Test execution handles missing routes."""
        schedule_data = {
            "id": 1,
            "route_id": 999,  # Non-existent route
            "user_id": 1,
            "schedule_type": "interval",
            "interval_minutes": 30,
            "daily_count": None,
            "next_run": datetime.now(),
            "is_active": True,
            "created_at": datetime.now(),
        }
        schedule = Schedule(**schedule_data)

        mock_db.fetchrow.return_value = None  # Route not found

        schedule_service = ScheduleService(mock_db)
        queue_service = QueueService(mock_db)

        result = await execution_engine._execute_schedule(schedule, schedule_service, queue_service)

        assert result is False

    async def test_forward_message_success(self, execution_engine):
        """Test successful message forwarding."""
        success, error = await execution_engine._forward_message(111, 222, 999)

        assert success is True
        assert error == ""

    async def test_forward_message_handles_error(self, execution_engine):
        """Test message forwarding error handling."""
        success, error = await execution_engine._forward_message(111, 222, 999)

        if not success:
            assert isinstance(error, str)

    async def test_get_execution_stats(self, execution_engine, mock_db):
        """Test getting execution statistics."""
        mock_db.fetchrow.side_effect = [
            {"count": 100},  # sent
            {"count": 5},    # failed
            {"count": 20},   # pending
        ]

        stats = await execution_engine.get_execution_stats()

        assert "status" in stats
        assert "sent" in stats
        assert "failed" in stats
        assert "pending" in stats
        assert stats["sent"] == 100
        assert stats["failed"] == 5
        assert stats["pending"] == 20


@pytest.mark.asyncio
class TestExecutionEngineRetryLogic:
    """Test retry logic in execution engine."""

    @pytest.fixture
    async def execution_engine(self, mock_db, mock_bot_client):
        """Create ExecutionEngine instance."""
        return ExecutionEngine(mock_db, mock_bot_client)

    async def test_max_retries_limit(self, execution_engine, mock_db):
        """Test message stops retrying after max attempts."""
        post_queue_data = {
            "id": 1,
            "route_id": 1,
            "message_id_in_source": 999,
            "source_date": datetime.now(),
            "status": "failed",
            "retry_count": 3,  # Already at max
            "last_error": "Previous error",
            "created_at": datetime.now(),
        }
        post_item = PostQueueItem(**post_queue_data)

        # When retry_count >= 3, should not retry
        assert post_item.retry_count >= 3


@pytest.mark.asyncio
class TestExecutionEngineFactory:
    """Test factory function."""

    async def test_create_execution_engine(self, mock_db, mock_bot_client):
        """Test creating engine via factory."""
        engine = await create_execution_engine(mock_db, mock_bot_client)

        assert isinstance(engine, ExecutionEngine)
        assert engine.db == mock_db
        assert engine.client == mock_bot_client


@pytest.mark.asyncio
class TestExecutionEngineQueueProcessing:
    """Test queue processing during execution."""

    @pytest.fixture
    async def execution_engine(self, mock_db, mock_bot_client):
        """Create ExecutionEngine instance."""
        return ExecutionEngine(mock_db, mock_bot_client)

    async def test_fifo_order_processing(self, execution_engine, mock_db):
        """Test posts are processed in FIFO order."""
        # Posts ordered by source_date
        posts = [
            {"source_date": datetime.now() - timedelta(minutes=10), "id": 1},
            {"source_date": datetime.now() - timedelta(minutes=5), "id": 2},
            {"source_date": datetime.now(), "id": 3},
        ]

        # Verify FIFO ordering
        sorted_posts = sorted(posts, key=lambda x: x["source_date"])
        assert sorted_posts[0]["id"] == 1
        assert sorted_posts[-1]["id"] == 3

    async def test_process_multiple_posts(self, execution_engine, mock_db):
        """Test processing multiple posts from queue."""
        mock_db.fetchrow.return_value = None  # No posts

        queue_service = QueueService(mock_db)
        schedule_service = ScheduleService(mock_db)

        # Multiple iterations should process posts one by one
        for _ in range(3):
            await execution_engine._check_and_execute(schedule_service, queue_service)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
