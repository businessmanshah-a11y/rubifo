from typing import Optional
from datetime import datetime, date, timedelta
from src.models.subscription import Subscription
from src.logger import logger


class SubscriptionService:
    """Service for subscription management."""

    TIER_LIMITS = {"basic": 1, "pro": 3, "enterprise": 10}

    def __init__(self, db):
        self.db = db

    async def get_active_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get current active subscription for user.

        Args:
            user_id: Rubika user ID

        Returns:
            Subscription instance or None
        """
        result = await self.db.fetchrow(
            "SELECT * FROM subscriptions WHERE user_id = $1 AND is_active = true",
            user_id,
        )

        return Subscription(**result) if result else None

    async def check_route_limit(self, user_id: int) -> int:
        """Get maximum routes allowed for user based on subscription.

        Args:
            user_id: Rubika user ID

        Returns:
            Maximum number of routes (0 if no active subscription)
        """
        sub = await self.get_active_subscription(user_id)

        if not sub:
            return 0

        return self.TIER_LIMITS.get(sub.tier, 0)

    async def create_subscription(
        self, user_id: int, tier: str, days: int = 30
    ) -> Subscription:
        """Create a new subscription for user.

        Deactivates any existing subscription before creating new one.

        Args:
            user_id: Rubika user ID
            tier: Subscription tier (basic, pro, enterprise)
            days: Duration in days

        Returns:
            Created Subscription instance
        """
        # Deactivate any existing subscriptions
        await self.deactivate_subscription(user_id)

        start = date.today()
        end = start + timedelta(days=days)

        logger.info(f"Creating {tier} subscription for user {user_id}")

        result = await self.db.fetchrow(
            "INSERT INTO subscriptions (user_id, tier, start_date, end_date, is_active) "
            "VALUES ($1, $2, $3, $4, true) RETURNING *",
            user_id,
            tier,
            start,
            end,
        )

        return Subscription(**result)

    async def extend_subscription(self, user_id: int, days: int = 30) -> Subscription:
        """Extend existing subscription by N days.

        Args:
            user_id: Rubika user ID
            days: Number of days to extend

        Returns:
            Updated Subscription instance
        """
        logger.info(f"Extending subscription for user {user_id} by {days} days")

        sub = await self.get_active_subscription(user_id)

        if not sub:
            raise ValueError(f"No active subscription for user {user_id}")

        new_end = sub.end_date + timedelta(days=days)

        result = await self.db.fetchrow(
            "UPDATE subscriptions SET end_date = $1 WHERE id = $2 RETURNING *",
            new_end,
            sub.id,
        )

        return Subscription(**result)

    async def deactivate_subscription(self, user_id: int) -> None:
        """Deactivate all subscriptions for user.

        Args:
            user_id: Rubika user ID
        """
        logger.info(f"Deactivating subscriptions for user {user_id}")

        await self.db.execute(
            "UPDATE subscriptions SET is_active = false WHERE user_id = $1", user_id
        )

    async def get_subscription_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """Get subscription by ID.

        Args:
            subscription_id: Subscription ID

        Returns:
            Subscription instance or None
        """
        result = await self.db.fetchrow(
            "SELECT * FROM subscriptions WHERE id = $1", subscription_id
        )

        return Subscription(**result) if result else None
