"""Pytest configuration and fixtures (T63)."""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
import os
from dotenv import load_dotenv

load_dotenv(".env.test")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_db():
    """Mock database connection."""
    db = AsyncMock()
    db.execute = AsyncMock(return_value=None)
    db.fetch = AsyncMock(return_value=[])
    db.fetchrow = AsyncMock(return_value=None)
    db.fetchval = AsyncMock(return_value=None)
    return db


@pytest.fixture
async def mock_bot_client():
    """Mock Rubika bot client."""
    client = AsyncMock()
    client.send_message = AsyncMock(return_value=True)
    client.get_message = AsyncMock(return_value=None)
    client.get_channel_posts = AsyncMock(return_value=[])
    return client


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": 1,
        "user_id": 123456789,
        "username": "testuser",
        "trial_start_at": datetime.now(),
        "trial_end_at": datetime.now() + timedelta(hours=48),
        "is_trial_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@pytest.fixture
def sample_subscription_data():
    """Sample subscription data."""
    return {
        "id": 1,
        "user_id": 1,
        "tier": "basic",
        "start_date": datetime.now().date(),
        "end_date": (datetime.now() + timedelta(days=30)).date(),
        "is_active": True,
        "created_at": datetime.now(),
    }


@pytest.fixture
def sample_route_data():
    """Sample route data."""
    return {
        "id": 1,
        "user_id": 1,
        "source_channel_id": 111111,
        "target_channel_id": 222222,
        "is_active": True,
        "created_at": datetime.now(),
    }


@pytest.fixture
def sample_post_queue_data():
    """Sample post queue item data."""
    return {
        "id": 1,
        "route_id": 1,
        "message_id_in_source": 999,
        "source_date": datetime.now() - timedelta(minutes=10),
        "status": "pending",
        "retry_count": 0,
        "last_error": None,
        "created_at": datetime.now(),
    }


@pytest.fixture
def sample_schedule_data():
    """Sample schedule data."""
    return {
        "id": 1,
        "route_id": 1,
        "user_id": 1,
        "schedule_type": "interval",
        "interval_minutes": 30,
        "daily_count": None,
        "next_run": datetime.now() + timedelta(minutes=30),
        "is_active": True,
        "created_at": datetime.now(),
    }


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data."""
    return {
        "id": 1,
        "user_id": 1,
        "amount": 50000,
        "tier": "basic",
        "status": "completed",
        "reference_id": "ref_123456",
        "created_at": datetime.now(),
    }


@pytest.fixture
def sample_zarinpal_response():
    """Sample Zarinpal API response."""
    return {
        "result": 100,
        "ref_id": "123456789",
        "authority": "auth_123456789",
    }


@pytest.fixture
def sample_zarinpal_verify():
    """Sample Zarinpal verification response."""
    return {
        "result": 100,
        "ref_id": "123456789",
    }


@pytest.fixture(scope="session")
def pytest_configure(config):
    """Configure pytest."""
    # Set asyncio mode
    config.addinivalue_line(
        "asyncio_mode",
        "auto"
    )


# Configure asyncio for pytest-asyncio
pytestmark = pytest.mark.asyncio
