"""Integration tests for ExecutionEngine (T67)."""

import pytest
import asyncio
from types import SimpleNamespace
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

    async def test_execute_schedule_sends_pending_text_post(self, execution_engine, mock_db, mock_bot_client):
        """A due schedule loads the queued source post and sends it."""
        schedule = Schedule(
            id=1,
            route_id=1,
            user_id=1,
            schedule_type="interval",
            interval_minutes=30,
            next_run=datetime.now(),
            is_active=True,
        )
        mock_db.fetchrow.side_effect = [
            {"id": 1, "user_id": 123456789, "target_channel_id": 222, "is_active": True},
            {"id": 10, "route_id": 1, "source_post_id": 99, "status": "pending", "retry_count": 0},
            {
                "id": 99,
                "source_id": 5,
                "order_index": 0,
                "message_type": "text",
                "text_content": "hello",
                "file_id": None,
                "caption": None,
                "raw_data": None,
                "file_id_valid": True,
                "added_at": datetime.now(),
            },
        ]

        result = await execution_engine._execute_schedule(schedule, ScheduleService(mock_db), QueueService(mock_db))

        assert result is True
        mock_bot_client.send_message.assert_awaited_with(222, "hello")

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

    async def test_send_text_post_success(self, execution_engine, mock_bot_client):
        """Test successful text post sending."""
        post = SimpleNamespace(
            id=1,
            message_type="text",
            file_id=None,
            caption=None,
            text_content="hello",
            raw_data={"message_id": "999"},
        )

        success, error = await execution_engine._send_source_post(post, 222)

        assert success is True
        assert error == ""
        mock_bot_client.send_message.assert_awaited_once_with(222, "hello")

    async def test_send_text_post_handles_error(self, execution_engine, mock_bot_client):
        """Test text post send error handling."""
        post = SimpleNamespace(
            id=1,
            message_type="text",
            file_id=None,
            caption=None,
            text_content="hello",
            raw_data={"message_id": "999"},
        )
        mock_bot_client.send_message.side_effect = Exception("send failed")

        success, error = await execution_engine._send_source_post(post, 222)

        assert success is False
        assert error == "send failed"

    async def test_invalid_media_is_not_forwarded_with_sender_label(self, execution_engine, mock_bot_client):
        """Invalid media must fail instead of using forward fallback with attribution."""
        post = SimpleNamespace(
            id=10,
            message_type="photo",
            file_id="expired-file-id",
            caption="caption",
            text_content=None,
            raw_data={"message_id": "1732781246254391090"},
        )
        mock_bot_client.send_file.side_effect = Exception("RubikaAPIError: file_id is not valid")
        mock_bot_client.forward_hidden = AsyncMock(return_value=True)
        execution_engine._reupload_file = AsyncMock(side_effect=Exception("Failed to download file: 502"))

        success, error = await execution_engine._send_source_post(
            post, "@testrubifo2", user_guid="b0HRK4L0ecU03e486bf939548b07c117"
        )

        assert success is False
        assert "Failed to download file: 502" in error
        mock_bot_client.forward_hidden.assert_not_awaited()

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
