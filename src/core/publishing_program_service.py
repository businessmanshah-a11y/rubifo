import json
from typing import Any, Dict, List, Optional, Tuple

from src.core.route_service import RouteService
from src.core.schedule_service import ScheduleService
from src.core.source_service import SourceService
from src.core.subscription_service import SubscriptionService
from src.core.destination_service import DestinationService
from src.models.destination import DestinationChannel
from src.models.publishing_draft import PublishingDraft
from src.models.schedule import Schedule


class PublishingProgramService:
    """Orchestrate user-facing publishing programs over internal routes."""

    def __init__(self, db):
        self.db = db

    async def save_draft(
        self,
        user_id: str,
        flow_kind: str,
        step: str,
        destination_id: Optional[int] = None,
        source_id: Optional[int] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> PublishingDraft:
        row = await self.db.fetchrow(
            """
            INSERT INTO publishing_drafts
              (user_id, flow_kind, step, destination_id, source_id, payload, is_active)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, true)
            ON CONFLICT (user_id) WHERE is_active = true
            DO UPDATE SET flow_kind = EXCLUDED.flow_kind, step = EXCLUDED.step,
                          destination_id = EXCLUDED.destination_id,
                          source_id = EXCLUDED.source_id, payload = EXCLUDED.payload,
                          updated_at = NOW()
            RETURNING *
            """,
            user_id,
            flow_kind,
            step,
            destination_id,
            source_id,
            json.dumps(payload or {}),
        )
        data = dict(row)
        if isinstance(data.get("payload"), str):
            data["payload"] = json.loads(data["payload"])
        return PublishingDraft(**data)

    async def get_draft(self, user_id: str) -> Optional[PublishingDraft]:
        row = await self.db.fetchrow(
            "SELECT * FROM publishing_drafts WHERE user_id = $1 AND is_active = true",
            user_id,
        )
        if not row:
            return None
        data = dict(row)
        if isinstance(data.get("payload"), str):
            data["payload"] = json.loads(data["payload"])
        return PublishingDraft(**data)

    async def clear_draft(self, user_id: str) -> None:
        await self.db.execute(
            "UPDATE publishing_drafts SET is_active = false, updated_at = NOW() "
            "WHERE user_id = $1 AND is_active = true",
            user_id,
        )

    async def can_create_real_program(self, user_id: str, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        access = await SubscriptionService(self.db).get_access_state(user_id)
        if access == "expired":
            return False, "برای ساخت برنامه انتشار، اشتراک یا تریال فعال لازم است."
        if access == "trial":
            if config.get("program_mode") != "recurring":
                return False, "کمپین تاریخ‌دار در تریال قفل است؛ برای ادامه اشتراک را ارتقا دهید."
            count = await self.db.fetchval(
                """
                SELECT COUNT(*) FROM schedules
                WHERE user_id = $1 AND program_purpose = 'real'
                  AND schedule_type = 'publishing_program'
                """,
                user_id,
            ) or 0
            if count >= 1:
                return False, "در تریال فقط یک برنامه واقعی روزانه قابل ساخت است."
        return True, None

    async def can_create_tutorial(self, user_id: str) -> Tuple[bool, Optional[str]]:
        if await SubscriptionService(self.db).get_access_state(user_id) == "expired":
            return False, "برای اجرای آزمایش، تریال یا اشتراک فعال لازم است."
        return True, None

    async def commit_real_program(
        self,
        user_id: str,
        destination: DestinationChannel,
        source,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        allowed, reason = await self.can_create_real_program(user_id, config)
        if not allowed:
            raise ValueError(reason)
        route_id = await RouteService(self.db).get_or_create_internal_route(
            user_id, source.id, destination.id, destination.channel_id, "real"
        )
        has_content = await SourceService(self.db).count_posts(source.id) > 0
        schedule = await ScheduleService(self.db).create_publishing_schedule(
            user_id=user_id,
            route_id=route_id,
            config=config,
            is_active=has_content,
            paused_reason=None if has_content else "در انتظار محتوا",
            program_purpose="real",
        )
        await self.clear_draft(user_id)
        return {"schedule": schedule, "route_id": route_id, "waiting_for_content": not has_content}

    async def update_real_program(
        self,
        user_id: str,
        schedule_id: int,
        source_id: int,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        access = await SubscriptionService(self.db).get_access_state(user_id)
        if access == "expired":
            raise ValueError("برای ویرایش برنامه انتشار، اشتراک یا تریال فعال لازم است.")
        if access == "trial" and config.get("program_mode") != "recurring":
            raise ValueError("کمپین تاریخ‌دار در تریال قفل است؛ برای ادامه اشتراک را ارتقا دهید.")
        has_content = await SourceService(self.db).count_posts(source_id) > 0
        schedule = await ScheduleService(self.db).update_publishing_schedule(
            schedule_id, config, has_content
        )
        await self.clear_draft(user_id)
        return {"schedule": schedule, "waiting_for_content": not has_content}

    async def get_program_components(self, user_id: str, schedule_id: int):
        row = await self.db.fetchrow(
            """
            SELECT r.destination_id, r.source_id
            FROM schedules sch
            JOIN routes r ON r.id = sch.route_id
            WHERE sch.id = $1 AND sch.user_id = $2
              AND sch.program_purpose = 'real'
            """,
            schedule_id,
            user_id,
        )
        if not row:
            return None
        destination = await DestinationService(self.db).get(row["destination_id"], user_id)
        source = await SourceService(self.db).get_source(row["source_id"])
        if not destination or not source:
            return None
        return destination, source

    async def commit_tutorial(
        self, user_id: str, destination: DestinationChannel, source, interval_minutes: int
    ) -> Dict[str, Any]:
        allowed, reason = await self.can_create_tutorial(user_id)
        if not allowed:
            raise ValueError(reason)
        if interval_minutes not in (1, 5, 10):
            raise ValueError("فاصله آزمایش باید ۱، ۵ یا ۱۰ دقیقه باشد.")
        route_id = await RouteService(self.db).get_or_create_internal_route(
            user_id, source.id, destination.id, destination.channel_id, "tutorial_test"
        )
        schedule = await ScheduleService(self.db).create_schedule(
            user_id=user_id,
            route_id=route_id,
            schedule_type="interval",
            interval_minutes=interval_minutes,
            program_purpose="tutorial_test",
        )
        await self.clear_draft(user_id)
        return {"schedule": schedule, "route_id": route_id}

    async def cleanup_tutorial(self, user_id: str) -> None:
        await self.db.execute(
            """
            WITH deleted_routes AS (
                DELETE FROM routes
                WHERE user_id = $1 AND program_purpose = 'tutorial_test'
                RETURNING source_id
            )
            DELETE FROM sources
            WHERE user_id = (SELECT id FROM users WHERE user_id = $1)
              AND program_purpose = 'tutorial_test'
            """,
            user_id,
        )

    async def source_has_active_program(self, source_id: int) -> bool:
        value = await self.db.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM schedules sch
                JOIN routes r ON r.id = sch.route_id
                WHERE r.source_id = $1 AND sch.is_active = true
            )
            """,
            source_id,
        )
        return bool(value)

    async def activate_waiting_programs(self, source_id: int) -> int:
        rows = await self.db.fetch(
            """
            SELECT sch.* FROM schedules sch
            JOIN routes r ON r.id = sch.route_id
            WHERE r.source_id = $1 AND sch.is_active = false
              AND sch.paused_reason = 'در انتظار محتوا'
            """,
            source_id,
        )
        schedules = ScheduleService(self.db)
        activated = 0
        for row in rows:
            schedule = Schedule(**ScheduleService._row_dict(row))
            next_run = await schedules.calculate_next_for_schedule(schedule)
            if next_run:
                await self.db.execute(
                    """
                    UPDATE schedules
                    SET is_active = true, paused_reason = NULL, next_run = $2, updated_at = NOW()
                    WHERE id = $1
                    """,
                    schedule.id,
                    next_run,
                )
                activated += 1
        return activated

    async def list_programs(self, user_id: str) -> List[Dict[str, Any]]:
        rows = await self.db.fetch(
            """
            SELECT sch.*, src.id AS source_id, src.name AS source_name, dc.channel_id
            FROM schedules sch
            JOIN routes r ON r.id = sch.route_id
            JOIN sources src ON src.id = r.source_id
            LEFT JOIN destination_channels dc ON dc.id = r.destination_id
            WHERE sch.user_id = $1
            ORDER BY sch.created_at DESC
            """,
            user_id,
        )
        return [dict(row) for row in rows]
