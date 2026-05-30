import json
from typing import Any, Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from src.models.schedule import Schedule, ScheduleTime
from src.logger import logger
from src.core.professional_schedule import PlanSlotGenerator, describe_plan
from src.utils import to_jalali_date


class ScheduleService:
    """Service for managing message scheduling and execution."""

    def __init__(self, db):
        self.db = db

    async def create_schedule(
        self,
        user_id: str,
        route_id: int,
        schedule_type: str,
        interval_minutes: Optional[int] = None,
        daily_count: Optional[int] = None,
        times: Optional[List[Tuple[int, int]]] = None,
        plan_kind: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        posts_per_run: int = 1,
        loop_mode: bool = False,
        ends_at: Optional[datetime] = None,
    ) -> Schedule:
        """Create a new schedule.

        Args:
            user_id: Rubika user ID
            route_id: Route ID to apply schedule to
            schedule_type: 'interval' or 'daily_count'
            interval_minutes: Minutes between messages (for interval type)
            daily_count: Number of messages to send per day (for daily_count type)
            times: List of (hour, minute) tuples for distribution (for daily_count type)

        Returns:
            Created Schedule instance
        """
        plan_kind = plan_kind or schedule_type
        config = config or {}
        if schedule_type not in [
            "interval",
            "daily_count",
            "publishing_program",
            "campaign",
            "smart_queue",
            "timing_pattern",
            "multi_stage",
            "content_mix",
        ]:
            raise ValueError(f"Invalid schedule_type: {schedule_type}")

        # Calculate next_run
        if plan_kind in ("interval", "daily_count"):
            next_run = await self._calculate_next_run(
                schedule_type, interval_minutes, daily_count, times
            )
        else:
            next_run = PlanSlotGenerator().next_run(plan_kind, config)
            if next_run is None:
                raise ValueError("No future run could be generated for this plan")

        logger.info(f"Creating {schedule_type} schedule for route {route_id}")

        result = await self.db.fetchrow(
            """
            INSERT INTO schedules
            (user_id, route_id, schedule_type, plan_kind, config, interval_minutes,
             daily_count, posts_per_run, loop_mode, next_run, ends_at, is_active)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10, $11, true)
            RETURNING *
            """,
            user_id,
            route_id,
            schedule_type,
            plan_kind,
            json.dumps(config),
            interval_minutes,
            daily_count,
            posts_per_run,
            loop_mode,
            next_run,
            ends_at,
        )

        schedule = Schedule(**self._row_dict(result))
        await self.db.execute("UPDATE schedules SET updated_at = updated_at WHERE id = $1", schedule.id)

        # If daily_count type, insert distribution times
        if schedule_type == "daily_count" and times:
            for hour, minute in times:
                await self.db.execute(
                    """
                    INSERT INTO schedule_times (schedule_id, hour, minute)
                    VALUES ($1, $2, $3)
                    """,
                    schedule.id,
                    hour,
                    minute,
                )
            logger.info(f"Added {len(times)} schedule times for schedule {schedule.id}")

        return schedule

    async def create_professional_schedule(
        self,
        user_id: str,
        route_id: int,
        plan_kind: str,
        config: Dict[str, Any],
    ) -> Schedule:
        """Create a professional plan backed by JSON config."""
        daily_count = config.get("daily_count")
        if plan_kind == "content_mix":
            daily_count = sum(config.get("quotas", {}).values())
        posts_per_run = int(config.get("posts_per_run", 1))
        loop_mode = bool(config.get("loop_mode", False))
        return await self.create_schedule(
            user_id=user_id,
            route_id=route_id,
            schedule_type=plan_kind,
            plan_kind=plan_kind,
            config=config,
            daily_count=daily_count,
            posts_per_run=posts_per_run,
            loop_mode=loop_mode,
        )

    async def create_publishing_schedule(
        self,
        user_id: str,
        route_id: int,
        config: Dict[str, Any],
        is_active: bool = True,
        paused_reason: Optional[str] = None,
        program_purpose: str = "real",
    ) -> Schedule:
        """Create the user-facing publishing-program schedule."""
        next_run = PlanSlotGenerator().next_run("publishing_program", config) if is_active else None
        row = await self.db.fetchrow(
            """
            INSERT INTO schedules
              (user_id, route_id, schedule_type, plan_kind, config, posts_per_run,
               loop_mode, next_run, is_active, paused_reason, program_purpose)
            VALUES ($1, $2, 'publishing_program', 'publishing_program', $3::jsonb,
                    $4, $5, $6, $7, $8, $9)
            RETURNING *
            """,
            user_id,
            route_id,
            json.dumps(config),
            int(config.get("posts_per_run", 1)),
            bool(config.get("loop_mode", False)),
            next_run,
            is_active,
            paused_reason,
            program_purpose,
        )
        return Schedule(**self._row_dict(row))

    async def update_publishing_schedule(
        self,
        schedule_id: int,
        config: Dict[str, Any],
        has_content: bool,
    ) -> Schedule:
        """Update timing for an existing publishing-program schedule."""
        next_run = PlanSlotGenerator().next_run("publishing_program", config) if has_content else None
        row = await self.db.fetchrow(
            """
            UPDATE schedules
            SET schedule_type = 'publishing_program',
                plan_kind = 'publishing_program',
                config = $2::jsonb,
                posts_per_run = $3,
                loop_mode = $4,
                next_run = $5,
                is_active = $6,
                paused_reason = $7,
                updated_at = NOW()
            WHERE id = $1
            RETURNING *
            """,
            schedule_id,
            json.dumps(config),
            int(config.get("posts_per_run", 1)),
            bool(config.get("loop_mode", False)),
            next_run,
            has_content,
            None if has_content else "در انتظار محتوا",
        )
        return Schedule(**self._row_dict(row))

    async def update_professional_schedule(
        self,
        schedule_id: int,
        plan_kind: str,
        config: Dict[str, Any],
    ) -> Schedule:
        """Update an existing schedule with a new professional plan config."""
        next_run = PlanSlotGenerator().next_run(plan_kind, config)
        if next_run is None:
            raise ValueError("No future run could be generated for this plan")
        daily_count = config.get("daily_count")
        if plan_kind == "content_mix":
            daily_count = sum(config.get("quotas", {}).values())
        result = await self.db.fetchrow(
            """
            UPDATE schedules
            SET schedule_type = $2, plan_kind = $2, config = $3::jsonb,
                daily_count = $4, posts_per_run = $5, loop_mode = $6,
                next_run = $7, paused_reason = NULL, is_active = true,
                updated_at = NOW()
            WHERE id = $1
            RETURNING *
            """,
            schedule_id,
            plan_kind,
            json.dumps(config),
            daily_count,
            int(config.get("posts_per_run", 1)),
            bool(config.get("loop_mode", False)),
            next_run,
        )
        return Schedule(**self._row_dict(result))

    async def get_schedule(self, schedule_id: int) -> Optional[Schedule]:
        """Get schedule by ID.

        Args:
            schedule_id: Schedule ID

        Returns:
            Schedule instance or None
        """
        result = await self.db.fetchrow(
            "SELECT * FROM schedules WHERE id = $1", schedule_id
        )

        return Schedule(**self._row_dict(result)) if result else None

    async def get_route_schedule(self, route_id: int) -> Optional[Schedule]:
        """Get active schedule for a route.

        Args:
            route_id: Route ID

        Returns:
            Schedule instance or None
        """
        result = await self.db.fetchrow(
            "SELECT * FROM schedules WHERE route_id = $1 AND is_active = true",
            route_id,
        )

        return Schedule(**self._row_dict(result)) if result else None

    async def get_user_schedules(self, user_id: int) -> List[Schedule]:
        """Get all schedules for a user.

        Args:
            user_id: Rubika user ID

        Returns:
            List of Schedule instances
        """
        results = await self.db.fetch(
            "SELECT * FROM schedules WHERE user_id = $1 ORDER BY created_at DESC",
            user_id,
        )

        return [Schedule(**self._row_dict(row)) for row in results]

    async def get_schedule_times(self, schedule_id: int) -> List[ScheduleTime]:
        """Get distribution times for a schedule.

        Args:
            schedule_id: Schedule ID

        Returns:
            List of ScheduleTime instances
        """
        results = await self.db.fetch(
            """
            SELECT * FROM schedule_times
            WHERE schedule_id = $1
            ORDER BY hour, minute
            """,
            schedule_id,
        )

        return [ScheduleTime(**self._time_row_dict(row)) for row in results]

    async def update_next_run(self, schedule_id: int, next_run: datetime) -> None:
        """Update next_run time for a schedule.

        Args:
            schedule_id: Schedule ID
            next_run: New next run datetime
        """
        await self.db.execute(
            "UPDATE schedules SET next_run = $1, last_run = NOW() WHERE id = $2",
            next_run,
            schedule_id,
        )

        logger.info(f"Schedule {schedule_id} next_run updated to {next_run}")

    async def deactivate_schedule(self, schedule_id: int) -> None:
        """Deactivate a schedule.

        Args:
            schedule_id: Schedule ID
        """
        await self.db.execute(
            "UPDATE schedules SET is_active = false WHERE id = $1", schedule_id
        )

        logger.info(f"Schedule {schedule_id} deactivated")

    async def activate_schedule(self, schedule_id: int) -> None:
        """Activate a schedule.

        Args:
            schedule_id: Schedule ID
        """
        await self.db.execute(
            "UPDATE schedules SET is_active = true WHERE id = $1", schedule_id
        )

        logger.info(f"Schedule {schedule_id} activated")

    async def pause_schedule(self, schedule_id: int, reason: str) -> None:
        """Pause a schedule and store a human-readable reason."""
        await self.db.execute(
            "UPDATE schedules SET is_active = false, paused_reason = $2 WHERE id = $1",
            schedule_id,
            reason,
        )
        logger.info(f"Schedule {schedule_id} paused: {reason}")

    async def mark_slot_done(self, schedule_id: int, run_at: datetime) -> None:
        """Mark the generated/persisted slot as done when present."""
        await self.db.execute(
            """
            UPDATE schedule_times
            SET status = 'done'
            WHERE schedule_id = $1 AND scheduled_at = $2
            """,
            schedule_id,
            run_at,
        )

    async def get_active_schedules(self) -> List[Schedule]:
        """Get all active schedules."""
        rows = await self.db.fetch(
            "SELECT * FROM schedules WHERE is_active = true ORDER BY next_run ASC"
        )
        return [Schedule(**self._row_dict(row)) for row in rows]

    async def delete_schedule(self, schedule_id: int) -> None:
        """Delete a schedule (cascades to schedule_times).

        Args:
            schedule_id: Schedule ID
        """
        # Delete schedule times first (or rely on CASCADE)
        await self.db.execute("DELETE FROM schedule_times WHERE schedule_id = $1", schedule_id)

        # Delete schedule
        await self.db.execute("DELETE FROM schedules WHERE id = $1", schedule_id)

        logger.info(f"Schedule {schedule_id} deleted")

    async def _calculate_next_run(
        self,
        schedule_type: str,
        interval_minutes: Optional[int],
        daily_count: Optional[int],
        times: Optional[List[Tuple[int, int]]],
    ) -> datetime:
        """Calculate next run time based on schedule type.

        Args:
            schedule_type: 'interval' or 'daily_count'
            interval_minutes: Interval for interval type
            daily_count: Daily count for daily_count type
            times: Distribution times for daily_count type

        Returns:
            Next run datetime
        """
        now_utc = datetime.now()
        # User-facing schedule math is Tehran/local naive time in the current codebase.
        now_teh = now_utc

        if schedule_type == "interval":
            if not interval_minutes:
                raise ValueError("interval_minutes required for interval type")
            return now_utc + timedelta(minutes=interval_minutes)

        elif schedule_type == "daily_count":
            if not times or len(times) == 0:
                return now_utc + timedelta(hours=1)

            # Times are in Tehran — find next slot, store as UTC
            for hour, minute in sorted(times):
                teh_slot = now_teh.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if teh_slot > now_teh:
                    return teh_slot

            # All slots passed today — use first slot tomorrow (Tehran → UTC)
            first_hour, first_minute = times[0]
            tomorrow_teh = now_teh + timedelta(days=1)
            teh_slot = tomorrow_teh.replace(hour=first_hour, minute=first_minute, second=0, microsecond=0)
            return teh_slot

        else:
            raise ValueError(f"Unknown schedule_type: {schedule_type}")

    async def calculate_next_for_schedule(self, schedule: Schedule) -> Optional[datetime]:
        """Calculate the next run for legacy and professional schedules."""
        plan_kind = schedule.plan_kind or schedule.schedule_type
        if plan_kind in ("interval", "daily_count"):
            times = None
            if plan_kind == "daily_count":
                raw_times = await self.get_schedule_times(schedule.id)
                times = [(t.hour, t.minute) for t in raw_times if t.hour is not None and t.minute is not None]
            return await self._calculate_next_run(
                schedule.schedule_type,
                schedule.interval_minutes,
                schedule.daily_count,
                times,
            )
        return PlanSlotGenerator().next_run(plan_kind, schedule.config or {})

    def preview_plan(self, plan_kind: str, config: Dict[str, Any], count: int = 5) -> str:
        """Return a concise Farsi preview for a professional plan."""
        slots = PlanSlotGenerator().next_slots(plan_kind, config, count=count)
        times = "، ".join(to_jalali_date(slot.tehran_time, "%m/%d %H:%M") for slot in slots) or "اجرای آینده ندارد"
        return f"{describe_plan(plan_kind, config)}\n۵ اجرای بعدی: {times}"

    @staticmethod
    def _row_dict(row) -> Dict[str, Any]:
        data = dict(row)
        config = data.get("config")
        if isinstance(config, str):
            data["config"] = json.loads(config)
        elif config is None:
            data["config"] = {}
        if data.get("plan_kind") is None:
            data["plan_kind"] = data.get("schedule_type")
        return data

    @staticmethod
    def _time_row_dict(row) -> Dict[str, Any]:
        data = dict(row)
        metadata = data.get("metadata")
        if isinstance(metadata, str):
            data["metadata"] = json.loads(metadata)
        return data
