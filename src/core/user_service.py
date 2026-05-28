from typing import Optional
from datetime import datetime, timedelta
from src.models.user import User
from src.config import TRIAL_DURATION_HOURS
from src.logger import logger
from src.utils import now_tehran


class UserService:
    """Service for user management and operations."""

    def __init__(self, db):
        self.db = db

    async def get_or_create_user(
        self, user_id: str, username: Optional[str] = None
    ) -> User:
        """Get existing user or create new one with trial.

        Args:
            user_id: Rubika user ID
            username: Optional username

        Returns:
            User instance
        """
        result = await self.db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)

        if result:
            logger.info(f"User {user_id} found in database")
            return User(**result)

        logger.info(f"Creating new user {user_id} with trial")
        trial_end = now_tehran() + timedelta(hours=TRIAL_DURATION_HOURS)

        await self.db.execute(
            "INSERT INTO users (user_id, username, trial_end_at) VALUES ($1, $2, $3)",
            user_id,
            username,
            trial_end,
        )

        return await self.get_user(user_id)

    async def get_user(self, user_id: str) -> Optional[User]:
        """Fetch user by user_id.

        Args:
            user_id: Rubika user ID

        Returns:
            User instance or None if not found
        """
        if isinstance(user_id, int) and user_id < 0:
            raise ValueError("user_id must be positive")
        result = await self.db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        return User(**dict(result)) if result else None

    async def list_users(self, limit: int = 100, offset: int = 0):
        """List users with pagination.

        Args:
            limit: Number of users to return
            offset: Offset for pagination

        Returns:
            List of User instances
        """
        results = await self.db.fetch(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2",
            limit,
            offset,
        )
        return [User(**dict(row)) for row in results]

    async def check_trial_expiration(self, user_id: str) -> bool:
        """Check if trial has expired and disable routes if needed.

        Args:
            user_id: Rubika user ID

        Returns:
            True if trial expired, False otherwise
        """
        user = await self.get_user(user_id)

        if not user:
            return False

        if user.is_trial_active and now_tehran() > user.trial_end_at:
            logger.info(f"Trial expired for user {user_id}, disabling routes")

            await self.db.execute(
                "UPDATE routes SET is_active = false WHERE user_id = $1", user_id
            )

            await self.db.execute(
                "UPDATE users SET is_trial_active = false WHERE user_id = $1", user_id
            )

            return True

        return False

    async def update_trial_end(self, user_id: str, hours: int) -> None:
        """Update trial end date for a user.

        Args:
            user_id: Rubika user ID
            hours: Number of hours to extend trial by
        """
        new_end = now_tehran() + timedelta(hours=hours)
        await self.db.execute(
            "UPDATE users SET trial_end_at = $1, is_trial_active = true "
            "WHERE user_id = $2",
            new_end,
            user_id,
        )
        logger.info(f"Trial extended for user {user_id} by {hours} hours")

    async def update_trial_status(self, user_id: str, is_active: bool) -> None:
        """Update trial active flag for a user."""
        await self.db.execute(
            "UPDATE users SET is_trial_active = $1 WHERE user_id = $2",
            is_active,
            user_id,
        )
        logger.info(f"Trial status updated for user {user_id}: {is_active}")
