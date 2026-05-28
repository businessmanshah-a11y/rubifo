from typing import Optional
from datetime import datetime, date, timedelta
from src.models.subscription import Subscription
from src.config import SUBSCRIPTION_TIERS
from src.logger import logger
from src.utils import now_tehran


class SubscriptionService:
    """Service for subscription management."""

    TIER_LIMITS = {
        tier: config["max_destinations"] for tier, config in SUBSCRIPTION_TIERS.items()
    }

    def __init__(self, db):
        self.db = db

    async def get_active_subscription(self, user_id: str) -> Optional[Subscription]:
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

        return Subscription(**dict(result)) if result else None

    async def check_destination_limit(self, user_id: str) -> int:
        """Get maximum destinations allowed for user based on subscription.

        Args:
            user_id: Rubika user ID

        Returns:
            Maximum number of destinations (0 if no active subscription or trial)
        """
        return await self.get_destination_limit(user_id)

    async def get_access_state(self, user_id: str) -> str:
        """Return the user's current commercial access state.

        States:
            paid: active subscription exists.
            trial: no paid subscription, active unexpired trial exists.
            expired: neither paid access nor active trial exists.
        """
        sub = await self.get_active_subscription(user_id)
        if sub:
            return "paid"

        user = await self.db.fetchrow(
            "SELECT is_trial_active, trial_end_at FROM users WHERE user_id = $1",
            user_id,
        )
        if not user:
            return "expired"

        trial_end = user.get("trial_end_at") if hasattr(user, "get") else user["trial_end_at"]
        is_trial_active = (
            user.get("is_trial_active") if hasattr(user, "get") else user["is_trial_active"]
        )
        if is_trial_active and trial_end and trial_end > now_tehran():
            return "trial"

        return "expired"

    async def is_paid(self, user_id: str) -> bool:
        """Return True when the user has a paid subscription."""
        return await self.get_access_state(user_id) == "paid"

    async def can_use_professional_plans(self, user_id: str) -> bool:
        """Only paid users can create professional plan kinds."""
        return await self.is_paid(user_id)

    async def get_destination_limit(self, user_id: str) -> int:
        """Return destination limit for paid/trial users, or 0 for expired users."""
        sub = await self.get_active_subscription(user_id)
        if sub:
            return self.TIER_LIMITS.get(sub.tier, 0)

        user = await self.db.fetchrow(
            "SELECT is_trial_active, trial_end_at FROM users WHERE user_id = $1",
            user_id,
        )
        if not user:
            return 0

        trial_end = user.get("trial_end_at") if hasattr(user, "get") else user["trial_end_at"]
        is_trial_active = (
            user.get("is_trial_active") if hasattr(user, "get") else user["is_trial_active"]
        )
        if is_trial_active and trial_end and trial_end > now_tehran():
            return 1
        return 0

    async def create_subscription(
        self, user_id: str, tier: str, days: int = 30
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

        return Subscription(**dict(result)) if result else Subscription(
            user_id=user_id, tier=tier, start_date=start, end_date=end, is_active=True
        )

    async def extend_subscription(self, user_id: str, days: int = 30) -> Subscription:
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

        return Subscription(**dict(result)) if result else Subscription(
            user_id=user_id, tier=sub.tier, start_date=sub.start_date, end_date=new_end, is_active=True
        )

    async def deactivate_subscription(self, user_id: str) -> None:
        """Deactivate all subscriptions for user.

        Args:
            user_id: Rubika user ID
        """
        logger.info(f"Deactivating subscriptions for user {user_id}")

        await self.db.execute(
            "UPDATE subscriptions SET is_active = false WHERE user_id = $1", user_id
        )

    async def get_subscription_status(self, user_id: str) -> dict:
        """Return full subscription status for display in bot messages.

        Returns dict with keys: status, tier, end_date, days_left, hours_left,
        destinations_used, destinations_limit.
        Status values: 'trial', 'active', 'expired'.
        """
        sub = await self.get_active_subscription(user_id)

        destinations_used = await self.db.fetchval(
            "SELECT COUNT(DISTINCT target_channel_id) FROM routes WHERE user_id = $1 AND is_active = true",
            user_id,
        ) or 0

        if sub:
            days_left = (sub.end_date - datetime.now().date()).days
            return {
                "status": "active",
                "tier": sub.tier,
                "end_date": sub.end_date,
                "days_left": max(0, days_left),
                "hours_left": 0,
                "destinations_used": destinations_used,
                "destinations_limit": self.TIER_LIMITS.get(sub.tier, 1),
            }

        user = await self.db.fetchrow(
            "SELECT is_trial_active, trial_end_at FROM users WHERE user_id = $1",
            user_id,
        )
        if user:
            trial_end = user.get("trial_end_at") if hasattr(user, "get") else user["trial_end_at"]
            is_trial_active = (
                user.get("is_trial_active") if hasattr(user, "get") else user["is_trial_active"]
            )
            if is_trial_active and trial_end and trial_end > now_tehran():
                hours_left = max(0.0, (trial_end - datetime.now()).total_seconds() / 3600)
                return {
                    "status": "trial",
                    "tier": None,
                    "end_date": trial_end,
                    "days_left": int(hours_left / 24),
                    "hours_left": hours_left,
                    "destinations_used": destinations_used,
                    "destinations_limit": 1,
                }

        return {
            "status": "expired",
            "tier": None,
            "end_date": None,
            "days_left": 0,
            "hours_left": 0,
            "destinations_used": 0,
            "destinations_limit": 0,
        }

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

        return Subscription(**dict(result)) if result else None
