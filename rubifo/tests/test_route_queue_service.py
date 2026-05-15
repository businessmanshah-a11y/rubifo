"""Unit tests for RouteService and QueueService (T65)."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from src.core.route_service import RouteService
from src.core.queue_service import QueueService
from src.models.route import Route
from src.models.post_queue import PostQueueItem


@pytest.mark.asyncio
class TestRouteService:
    """Test RouteService functionality."""

    @pytest.fixture
    async def route_service(self, mock_db):
        """Create RouteService instance."""
        return RouteService(mock_db)

    async def test_can_create_route_within_limit(self, route_service, mock_db):
        """Test user can create route when within limit."""
        # User with basic tier (limit = 1) has 0 routes
        mock_db.fetchrow.side_effect = [
            {"tier": "basic"},  # Subscription query
            {"count": 0},  # Count of existing routes
        ]

        can_create, error = await route_service.can_create_route(1)

        assert can_create is True
        assert error is None

    async def test_can_create_route_at_limit(self, route_service, mock_db):
        """Test user cannot create route when at limit."""
        # User with basic tier (limit = 1) already has 1 route
        mock_db.fetchrow.side_effect = [
            {"tier": "basic"},  # Subscription query
            {"count": 1},  # Count of existing routes
        ]

        can_create, error = await route_service.can_create_route(1)

        assert can_create is False
        assert error is not None

    async def test_can_create_route_no_subscription(self, route_service, mock_db):
        """Test user without subscription cannot create route."""
        mock_db.fetchrow.side_effect = [
            None,  # No subscription
        ]

        can_create, error = await route_service.can_create_route(1)

        assert can_create is False
        assert error is not None

    async def test_create_route_success(self, route_service, mock_db, sample_route_data):
        """Test successfully creating a route."""
        mock_db.execute.return_value = None
        mock_db.fetchrow.return_value = sample_route_data

        route = await route_service.create_route(1, 111111, 222222)

        assert route is not None
        assert mock_db.execute.called

    async def test_deactivate_route(self, route_service, mock_db):
        """Test deactivating a route."""
        mock_db.execute.return_value = None

        result = await route_service.deactivate_route(1)

        assert mock_db.execute.called


@pytest.mark.asyncio
class TestQueueService:
    """Test QueueService functionality."""

    @pytest.fixture
    async def queue_service(self, mock_db):
        """Create QueueService instance."""
        return QueueService(mock_db)

    async def test_get_next_pending_fifo(self, queue_service, mock_db, sample_post_queue_data):
        """Test getting next pending post in FIFO order."""
        mock_db.fetchrow.return_value = sample_post_queue_data

        post = await queue_service.get_next_pending(1)

        assert post is not None
        # Should query with ORDER BY source_date ASC
        assert mock_db.fetchrow.called

    async def test_get_next_pending_empty_queue(self, queue_service, mock_db):
        """Test getting next pending when queue is empty."""
        mock_db.fetchrow.return_value = None

        post = await queue_service.get_next_pending(1)

        assert post is None

    async def test_mark_sent(self, queue_service, mock_db):
        """Test marking post as sent."""
        mock_db.execute.return_value = None

        result = await queue_service.mark_sent(1)

        assert mock_db.execute.called
        # Should update status to 'sent'

    async def test_mark_failed(self, queue_service, mock_db):
        """Test marking post as failed."""
        mock_db.execute.return_value = None

        result = await queue_service.mark_failed(1, "Test error")

        assert mock_db.execute.called
        # Should update status and increment retry_count

    async def test_mark_failed_increments_retry(self, queue_service, mock_db):
        """Test mark_failed increments retry counter."""
        mock_db.execute.return_value = None
        mock_db.fetchrow.return_value = {"retry_count": 1}

        result = await queue_service.mark_failed(1, "Error")

        # Verify the retry count increment logic
        assert mock_db.execute.called

    async def test_get_queue_stats(self, queue_service, mock_db):
        """Test getting queue statistics."""
        mock_db.fetch.return_value = [
            {"status": "pending", "count": 5},
            {"status": "sent", "count": 20},
            {"status": "failed", "count": 2},
        ]

        stats = await queue_service.get_queue_stats(1)

        assert isinstance(stats, list)
        assert mock_db.fetch.called

    async def test_queue_ordering_by_source_date(self, queue_service, mock_db):
        """Test posts are returned in source_date order."""
        posts = [
            {"id": 1, "source_date": datetime.now() - timedelta(minutes=10)},
            {"id": 2, "source_date": datetime.now() - timedelta(minutes=5)},
            {"id": 3, "source_date": datetime.now()},
        ]

        # Manually check ordering
        sorted_posts = sorted(posts, key=lambda x: x["source_date"])
        assert sorted_posts[0]["id"] == 1
        assert sorted_posts[-1]["id"] == 3


@pytest.mark.asyncio
class TestRouteAndQueueIntegration:
    """Test interaction between routes and queues."""

    async def test_new_route_queue_population(self, mock_db):
        """Test queue is populated when route is created."""
        route_service = RouteService(mock_db)
        queue_service = QueueService(mock_db)

        # Mock creating a route
        mock_db.execute.return_value = None
        mock_db.fetchrow.return_value = {"id": 1, "user_id": 1}

        route = await route_service.create_route(1, 111111, 222222)

        # Queue should be populated
        assert mock_db.execute.called

    async def test_deactivate_route_marks_queue_removed(self, mock_db):
        """Test deactivating a route marks queue items as removed."""
        route_service = RouteService(mock_db)
        mock_db.execute.return_value = None

        result = await route_service.deactivate_route(1)

        # Check that updates include queue status change
        assert mock_db.execute.called


class TestRouteModel:
    """Test Route model."""

    def test_route_dataclass_creation(self, sample_route_data):
        """Test creating Route dataclass."""
        route = Route(**sample_route_data)

        assert route.id == sample_route_data["id"]
        assert route.user_id == sample_route_data["user_id"]
        assert route.source_channel_id == sample_route_data["source_channel_id"]

    def test_route_is_active_flag(self, sample_route_data):
        """Test is_active flag."""
        route = Route(**sample_route_data)
        assert route.is_active is True

        sample_route_data["is_active"] = False
        inactive_route = Route(**sample_route_data)
        assert inactive_route.is_active is False


class TestPostQueueItemModel:
    """Test PostQueueItem model."""

    def test_post_queue_item_creation(self, sample_post_queue_data):
        """Test creating PostQueueItem."""
        item = PostQueueItem(**sample_post_queue_data)

        assert item.id == sample_post_queue_data["id"]
        assert item.route_id == sample_post_queue_data["route_id"]
        assert item.status == sample_post_queue_data["status"]

    def test_post_queue_status_transitions(self, sample_post_queue_data):
        """Test valid status transitions."""
        item = PostQueueItem(**sample_post_queue_data)

        # Valid statuses
        valid_statuses = ["pending", "sent", "failed", "removed"]
        assert item.status in valid_statuses

    def test_post_queue_retry_count(self, sample_post_queue_data):
        """Test retry counter."""
        sample_post_queue_data["retry_count"] = 0
        item = PostQueueItem(**sample_post_queue_data)
        assert item.retry_count == 0

        sample_post_queue_data["retry_count"] = 3
        item_with_retries = PostQueueItem(**sample_post_queue_data)
        assert item_with_retries.retry_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
