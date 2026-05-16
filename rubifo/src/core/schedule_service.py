from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from src.models.schedule import Schedule, ScheduleTime
from src.logger import logger
from src.utils import now_tehran


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
        if schedule_type not in ["interval", "daily_count"]:
            raise ValueError(f"Invalid schedule_type: {schedule_type}")

        # Calculate next_run
        next_run = await self._calculate_next_run(
            schedule_type, interval_minutes, daily_count, times
        )

        logger.info(f"Creating {schedule_type} schedule for route {route_id}")

        result = await self.db.fetchrow(
            """
            INSERT INTO schedules
            (user_id, route_id, schedule_type, interval_minutes, daily_count, next_run, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, true)
            RETURNING *
            """,
            user_id,
            route_id,
            schedule_type,
            interval_minutes,
            daily_count,
            next_run,
        )

        schedule = Schedule(**result)

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

        return Schedule(**result) if result else None

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

        return Schedule(**result) if result else None

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

        return [Schedule(**dict(row)) for row in results]

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

        return [ScheduleTime(**dict(row)) for row in results]

    async def update_next_run(self, schedule_id: int, next_run: datetime) -> None:
        """Update next_run time for a schedule.

        Args:
            schedule_id: Schedule ID
            next_run: New next run datetime
        """
        await self.db.execute(
            "UPDATE schedules SET next_run = $1 WHERE id = $2",
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
        now = now_tehran()

        if schedule_type == "interval":
            if not interval_minutes:
                raise ValueError("interval_minutes required for interval type")
            return now + timedelta(minutes=interval_minutes)

        elif schedule_type == "daily_count":
            if not times or len(times) == 0:
                # If no times specified, default to 1 hour from now
                return now + timedelta(hours=1)

            # Find the earliest time today after now
            for hour, minute in sorted(times):
                scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if scheduled_time > now:
                    return scheduled_time

            # If all times have passed today, use first time tomorrow
            first_hour, first_minute = times[0]
            tomorrow = now + timedelta(days=1)
            return tomorrow.replace(hour=first_hour, minute=first_minute, second=0, microsecond=0)

        else:
            raise ValueError(f"Unknown schedule_type: {schedule_type}")
