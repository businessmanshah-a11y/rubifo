import re
from typing import List, Optional, Tuple

from src.core.subscription_service import SubscriptionService
from src.models.destination import DestinationChannel


class DestinationService:
    """Manage channels registered independently from internal source routes."""

    _CHANNEL_RE = re.compile(r"^@[A-Za-z0-9_]{3,}$")

    def __init__(self, db):
        self.db = db
        self.subscriptions = SubscriptionService(db)

    @classmethod
    def normalize_channel_input(cls, raw: str) -> str:
        value = raw.strip().rstrip("/")
        for prefix in ("https://rubika.ir/", "http://rubika.ir/", "rubika.ir/"):
            if value.lower().startswith(prefix):
                value = "@" + value[len(prefix):].split("/", 1)[0]
                break
        if not cls._CHANNEL_RE.match(value):
            raise ValueError("آدرس کانال باید مانند @my_channel یا لینک روبیکا باشد.")
        return value

    async def record_verification(
        self,
        user_id: str,
        channel_id: str,
        title: Optional[str],
        status: str,
        error: Optional[str] = None,
    ) -> DestinationChannel:
        row = await self.db.fetchrow(
            """
            INSERT INTO destination_channels
              (user_id, channel_id, title, verification_status, verification_error,
               verified_at, is_active)
            VALUES ($1, $2, $3, $4, $5,
                    CASE WHEN $4 IN ('verified', 'cleanup_failed') THEN NOW() END, true)
            ON CONFLICT (user_id, channel_id) WHERE is_active = true
            DO UPDATE SET title = EXCLUDED.title,
                          verification_status = EXCLUDED.verification_status,
                          verification_error = EXCLUDED.verification_error,
                          verified_at = EXCLUDED.verified_at,
                          updated_at = NOW()
            RETURNING *
            """,
            user_id,
            channel_id,
            title,
            status,
            error,
        )
        return DestinationChannel(**dict(row))

    async def get(self, destination_id: int, user_id: Optional[str] = None) -> Optional[DestinationChannel]:
        query = "SELECT * FROM destination_channels WHERE id = $1 AND is_active = true"
        args = [destination_id]
        if user_id is not None:
            query += " AND user_id = $2"
            args.append(user_id)
        row = await self.db.fetchrow(query, *args)
        return DestinationChannel(**dict(row)) if row else None

    async def list_verified(self, user_id: str) -> List[DestinationChannel]:
        rows = await self.db.fetch(
            """
            SELECT * FROM destination_channels
            WHERE user_id = $1 AND is_active = true
              AND verification_status IN ('verified', 'cleanup_failed')
            ORDER BY created_at
            """,
            user_id,
        )
        return [DestinationChannel(**dict(row)) for row in rows]

    async def can_register(self, user_id: str, channel_id: str) -> Tuple[bool, Optional[str]]:
        existing = await self.db.fetchrow(
            """
            SELECT id FROM destination_channels
            WHERE user_id = $1 AND channel_id = $2 AND is_active = true
            """,
            user_id,
            channel_id,
        )
        if existing:
            return True, None
        limit = await self.subscriptions.get_destination_limit(user_id)
        used = await self.db.fetchval(
            "SELECT COUNT(*) FROM destination_channels WHERE user_id = $1 AND is_active = true",
            user_id,
        ) or 0
        if used >= limit:
            return False, (
                "ظرفیت کانال مقصد شما پر است.\n"
                "می‌توانید با کانال ثبت‌شده ادامه دهید، کانالی را جایگزین کنید یا اشتراک را ارتقا دهید."
            )
        return True, None

    async def deactivate(self, user_id: str, destination_id: int) -> None:
        await self.db.execute(
            "UPDATE destination_channels SET is_active = false, updated_at = NOW() "
            "WHERE id = $1 AND user_id = $2",
            destination_id,
            user_id,
        )

    async def count_active_programs(self, user_id: str, destination_id: int) -> int:
        return await self.db.fetchval(
            """
            SELECT COUNT(*) FROM schedules sch
            JOIN routes r ON r.id = sch.route_id
            WHERE r.user_id = $1 AND r.destination_id = $2 AND sch.is_active = true
            """,
            user_id,
            destination_id,
        ) or 0

    async def replace(self, user_id: str, destination_id: int) -> None:
        await self.db.execute(
            """
            UPDATE schedules
            SET is_active = false, paused_reason = 'کانال مقصد جایگزین شد',
                next_run = NULL, updated_at = NOW()
            WHERE route_id IN (
                SELECT id FROM routes
                WHERE user_id = $1 AND destination_id = $2 AND is_active = true
            ) AND is_active = true
            """,
            user_id,
            destination_id,
        )
        await self.db.execute(
            """
            UPDATE destination_channels
            SET is_active = false, updated_at = NOW()
            WHERE id = $1 AND user_id = $2
            """,
            destination_id,
            user_id,
        )

    async def remove(self, user_id: str, destination_id: int) -> None:
        await self.db.execute(
            """
            UPDATE schedules
            SET is_active = false, paused_reason = 'کانال مقصد حذف شد',
                next_run = NULL, updated_at = NOW()
            WHERE route_id IN (
                SELECT id FROM routes
                WHERE user_id = $1 AND destination_id = $2 AND is_active = true
            ) AND is_active = true
            """,
            user_id,
            destination_id,
        )
        await self.deactivate(user_id, destination_id)
