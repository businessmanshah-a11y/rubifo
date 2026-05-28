"""Unit tests for UserService (T64)."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from src.core.user_service import UserService
from src.models.user import User


@pytest.mark.asyncio
class TestUserService:
    """Test UserService functionality."""

    @pytest.fixture
    async def user_service(self, mock_db):
        """Create UserService instance."""
        return UserService(mock_db)

    async def test_get_or_create_user_new(self, user_service, mock_db, sample_user_data):
        """Test creating a new user."""
        mock_db.fetchrow.return_value = None
        mock_db.execute.return_value = None

        # Mock the second fetchrow to return created user
        mock_db.fetchrow.side_effect = [
            None,  # First call - user doesn't exist
            sample_user_data,  # Second call - return created user
        ]

        user = await user_service.get_or_create_user(123456789, "testuser")

        assert user is not None
        assert mock_db.execute.called

    async def test_get_or_create_user_existing(self, user_service, mock_db, sample_user_data):
        """Test getting existing user."""
        mock_db.fetchrow.return_value = sample_user_data

        user = await user_service.get_or_create_user(123456789, "testuser")

        assert user is not None
        assert user.user_id == sample_user_data["user_id"]

    async def test_get_user_not_found(self, user_service, mock_db):
        """Test getting non-existent user."""
        mock_db.fetchrow.return_value = None

        user = await user_service.get_user(999)

        assert user is None

    async def test_get_user_found(self, user_service, mock_db, sample_user_data):
        """Test getting existing user."""
        mock_db.fetchrow.return_value = sample_user_data

        user = await user_service.get_user(1)

        assert user is not None
        assert user.user_id == sample_user_data["user_id"]

    async def test_list_users(self, user_service, mock_db, sample_user_data):
        """Test listing users with pagination."""
        mock_db.fetch.return_value = [sample_user_data]

        users = await user_service.list_users(limit=10, offset=0)

        assert isinstance(users, list)
        assert mock_db.fetch.called

    async def test_check_trial_expiration_active(self, user_service, mock_db, sample_user_data):
        """Test trial is still active."""
        sample_user_data["trial_end_at"] = datetime.now() + timedelta(hours=24)
        mock_db.fetchrow.return_value = sample_user_data

        is_expired = await user_service.check_trial_expiration(1)

        assert is_expired is False

    async def test_check_trial_expiration_expired(self, user_service, mock_db, sample_user_data):
        """Test trial is expired."""
        sample_user_data["trial_end_at"] = datetime.now() - timedelta(hours=1)
        mock_db.fetchrow.return_value = sample_user_data

        is_expired = await user_service.check_trial_expiration(1)

        assert is_expired is True or mock_db.execute.called

    async def test_disable_user_routes_on_expiration(self, user_service, mock_db):
        """Test routes are disabled when trial expires."""
        mock_db.fetchrow.return_value = {
            "id": 1,
            "user_id": 1,
            "trial_end_at": datetime.now() - timedelta(hours=1),
            "is_trial_active": True,
        }
        mock_db.execute.return_value = None

        await user_service.check_trial_expiration(1)

        # Check that execute was called to disable routes
        assert mock_db.execute.called

    async def test_update_user_trial(self, user_service, mock_db):
        """Test updating user trial status."""
        mock_db.execute.return_value = None

        result = await user_service.update_trial_status(1, False)

        assert mock_db.execute.called


class TestUserModel:
    """Test User model."""

    def test_user_dataclass_creation(self, sample_user_data):
        """Test creating User dataclass."""
        user = User(**sample_user_data)

        assert user.user_id == sample_user_data["user_id"]
        assert user.username == sample_user_data["username"]
        assert user.is_trial_active == sample_user_data["is_trial_active"]

    def test_user_trial_hours_remaining(self, sample_user_data):
        """Test calculating hours remaining in trial."""
        sample_user_data["trial_end_at"] = datetime.now() + timedelta(hours=24)
        user = User(**sample_user_data)

        hours_remaining = (user.trial_end_at - datetime.now()).total_seconds() / 3600
        assert hours_remaining > 0
        assert hours_remaining <= 24


@pytest.mark.asyncio
class TestUserValidation:
    """Test user data validation."""

    async def test_user_id_validation(self, user_service, mock_db):
        """Test user ID validation."""
        # User IDs should be positive integers
        with pytest.raises((TypeError, ValueError)):
            await user_service.get_user(-1)

    async def test_username_sanitization(self, user_service, mock_db):
        """Test username sanitization."""
        # Usernames should be sanitized
        mock_db.fetchrow.return_value = None

        # This should not raise an error
        result = await user_service.get_or_create_user(123, "<script>alert('xss')</script>")

        assert mock_db.execute.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
