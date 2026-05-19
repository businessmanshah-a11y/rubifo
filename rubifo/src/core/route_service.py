from typing import Tuple, List, Dict, Any, Optional
from src.core.subscription_service import SubscriptionService
from src.logger import logger
from src.utils import now_tehran


def _row_get(row: Any, key: str, default: Any = None) -> Any:
    """Read a value from asyncpg records or dict-like test doubles."""
    if not row:
        return default
    if hasattr(row, "get"):
        value = row.get(key)
    elif key in row:
        value = row[key]
    else:
        value = default
    return default if value is None else value


class RouteService:
    """Service for route management and validation."""

    def __init__(self, db):
        self.db = db
        self.subscription_service = SubscriptionService(db)

    async def can_create_route(
        self, user_id: str, target_channel_id: str
    ) -> Tuple[bool, Optional[str]]:
        """Check if user can create a route to the target destination.

        Args:
            user_id: Rubika user ID
            target_channel_id: Normalized destination channel id

        Returns:
            Tuple of (can_create, error_message_if_no)
        """
        subscription = await self.subscription_service.get_active_subscription(user_id)

        if subscription:
            limit = self.subscription_service.TIER_LIMITS.get(subscription.tier, 0)
            access_state = "paid"
        else:
            access_state = "expired"
            try:
                user = await self.db.fetchrow(
                    "SELECT is_trial_active, trial_end_at FROM users WHERE user_id = $1",
                    user_id,
                )
            except Exception:
                user = None
            if user:
                trial_end = user.get("trial_end_at") if hasattr(user, "get") else user["trial_end_at"]
                is_trial_active = (
                    user.get("is_trial_active") if hasattr(user, "get") else user["is_trial_active"]
                )
                if is_trial_active and trial_end and trial_end > now_tehran():
                    access_state = "trial"
            if access_state != "trial":
                return False, (
                    "⚠️ تریال یا اشتراک فعالی ندارید.\n"
                    "💳 /buy برای خرید اشتراک و فعال‌سازی کانال‌های مقصد"
                )
            limit = 1

        existing_destination = await self.db.fetchrow(
            """
            SELECT EXISTS(
                SELECT 1 FROM routes
                WHERE user_id = $1 AND target_channel_id = $2 AND is_active = true
            ) AS exists
            """,
            user_id,
            target_channel_id,
        )
        destination_exists = bool(_row_get(existing_destination, "exists", False))
        if destination_exists:
            return True, None

        # Count existing active destinations; multiple routes to the same
        # destination should only consume one subscription slot.
        result = await self.db.fetchrow(
            """
            SELECT COUNT(DISTINCT target_channel_id) as count
            FROM routes
            WHERE user_id = $1 AND is_active = true
            """,
            user_id,
        )

        current_count = _row_get(result, "count", 0)

        if current_count >= limit:
            if subscription:
                tier_names = {
                    "basic": "شروع حرفه‌ای",
                    "pro": "رشد",
                    "enterprise": "مقیاس",
                }
                tier_name = tier_names.get(subscription.tier, subscription.tier)
                if subscription.tier == "basic":
                    msg = (
                        "پلن شروع حرفه‌ای فقط 1 کانال مقصد فعال دارد.\n"
                        "برای کانال‌های مقصد بیشتر پلن رشد یا مقیاس را بخرید. 💳 /buy"
                    )
                else:
                    msg = f"شما حداکثر {limit} کانال مقصد برای پلن {tier_name} دارید."
            else:
                msg = (
                    "در تریال فقط یک کانال مقصد دارید؛ برای کانال‌های مقصد بیشتر پلن رشد یا مقیاس را بخرید.\n"
                    "💳 /buy"
                )
            return False, msg

        return True, None

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
