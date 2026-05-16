from typing import Tuple, List, Dict, Any
from src.core.subscription_service import SubscriptionService
from src.logger import logger


class RouteService:
    """Service for route management and validation."""

    def __init__(self, db):
        self.db = db
        self.subscription_service = SubscriptionService(db)

    async def can_create_route(self, user_id: str) -> Tuple[bool, str]:
        """Check if user can create a new route based on subscription.

        Args:
            user_id: Rubika user ID

        Returns:
            Tuple of (can_create, error_message_if_no)
        """
        # Get active subscription
        subscription = await self.subscription_service.get_active_subscription(user_id)

        if not subscription:
            from src.database import fetchrow
            user = await fetchrow(
                "SELECT is_trial_active FROM users WHERE user_id = $1", user_id
            )
            if not user or not user["is_trial_active"]:
                return False, "⚠️ تریال یا اشتراک فعالی ندارید.\n💳 /buy برای خرید اشتراک"
            limit = 1
        else:
            # Get route limit for tier
            limit = self.subscription_service.TIER_LIMITS.get(subscription.tier, 0)

        # Count existing active routes
        result = await self.db.fetchrow(
            "SELECT COUNT(*) as count FROM routes WHERE user_id = $1 AND is_active = true",
            user_id,
        )

        current_count = result["count"] if result else 0

        if current_count >= limit:
            if subscription:
                tier_names = {"basic": "پایه", "pro": "حرفه‌ای", "enterprise": "ویژه"}
                tier_name = tier_names.get(subscription.tier, subscription.tier)
                msg = f"شما حداکثر {limit} مسیر برای پلان {tier_name} دارید."
            else:
                msg = f"در دوره تریال فقط {limit} مسیر مجاز است.\n💳 /buy برای اشتراک بیشتر"
            return False, msg

        return True, ""

    async def create_route(
        self, user_id: str, source_id: int, target_channel_id: str
    ) -> int:
        """Create a new route for user.

        Args:
            user_id: Rubika user ID
            source_id: Source ID (FK to sources table)
            target_channel_id: Target channel @username or numeric ID

        Returns:
            Created route ID
        """
        result = await self.db.fetchrow(
            "INSERT INTO routes (user_id, source_id, target_channel_id, is_active) "
            "VALUES ($1, $2, $3, true) RETURNING id",
            user_id,
            source_id,
            target_channel_id,
        )

        logger.info(f"Route created for user {user_id}: source {source_id} → {target_channel_id}")
        return result["id"]

    async def get_user_routes(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all routes for a user.

        Args:
            user_id: Rubika user ID

        Returns:
            List of route dictionaries
        """
        results = await self.db.fetch(
            "SELECT * FROM routes WHERE user_id = $1 ORDER BY created_at DESC",
            user_id,
        )

        return [dict(row) for row in results]

    async def get_route(self, route_id: int) -> Dict[str, Any]:
        """Get specific route by ID.

        Args:
            route_id: Route ID

        Returns:
            Route dictionary or None
        """
        result = await self.db.fetchrow("SELECT * FROM routes WHERE id = $1", route_id)
        return dict(result) if result else None

    async def deactivate_route(self, route_id: int) -> None:
        """Deactivate a route.

        Args:
            route_id: Route ID
        """
        await self.db.execute(
            "UPDATE routes SET is_active = false WHERE id = $1", route_id
        )

        logger.info(f"Route {route_id} deactivated")

    async def delete_route(self, route_id: int) -> None:
        """Delete a route (removes from queue too due to CASCADE).

        Args:
            route_id: Route ID
        """
        await self.db.execute("DELETE FROM routes WHERE id = $1", route_id)
        logger.info(f"Route {route_id} deleted")

    async def get_route_queue_count(self, route_id: int, status: str = "pending") -> int:
        """Get count of messages in queue for a route.

        Args:
            route_id: Route ID
            status: Filter by status (default: pending)

        Returns:
            Count of messages
        """
        result = await self.db.fetchrow(
            "SELECT COUNT(*) as count FROM post_queue WHERE route_id = $1 AND status = $2",
            route_id,
            status,
        )

        return result["count"] if result else 0
