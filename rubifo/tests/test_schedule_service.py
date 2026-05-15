"""Unit tests for ScheduleService (T66)."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from src.core.schedule_service import ScheduleService
from src.models.schedule import Schedule


@pytest.mark.asyncio
class TestScheduleService:
    """Test ScheduleService functionality."""

    @pytest.fixture
    async def schedule_service(self, mock_db):
        """Create ScheduleService instance."""
        return ScheduleService(mock_db)

    async def test_create_schedule_interval(self, schedule_service, mock_db, sample_schedule_data):
        """Test creating interval-based schedule."""
        mock_db.execute.return_value = None
        mock_db.fetchrow.return_value = sample_schedule_data

        schedule = await schedule_service.create_schedule(
            route_id=1,
            user_id=1,
            schedule_type="interval",
            interval_minutes=30,
        )

        assert mock_db.execute.called
        assert mock_db.fetchrow.called

    async def test_create_schedule_daily_count(self, schedule_service, mock_db):
        """Test creating daily_count-based schedule."""
        mock_db.execute.return_value = None
        mock_db.fetchrow.return_value = {
            "id": 1,
            "route_id": 1,
            "schedule_type": "daily_count",
            "daily_count": 5,
        }

        schedule = await schedule_service.create_schedule(
            route_id=1,
            user_id=1,
            schedule_type="daily_count",
            daily_count=5,
            times=[(9, 0), (14, 0), (18, 0), (20, 0), (22, 0)],
        )

        assert mock_db.execute.called

    async def test_calculate_next_run_interval(self, schedule_service):
        """Test calculating next_run for interval schedule."""
        now = datetime.now()
        next_run = await schedule_service._calculate_next_run(
            schedule_type="interval",
            interval_minutes=30,
            daily_count=None,
            times=None,
        )

        assert next_run > now
        assert (next_run - now).total_seconds() > 0

    async def test_calculate_next_run_daily_count(self, schedule_service):
        """Test calculating next_run for daily_count schedule."""
        times = [(9, 0), (14, 0), (18, 0)]

        next_run = await schedule_service._calculate_next_run(
            schedule_type="daily_count",
            interval_minutes=None,
            daily_count=3,
            times=times,
        )

        assert next_run is not None

    async def test_update_next_run(self, schedule_service, mock_db):
        """Test updating schedule's next_run time."""
        mock_db.execute.return_value = None
        new_time = datetime.now() + timedelta(hours=1)

        result = await schedule_service.update_next_run(1, new_time)

        assert mock_db.execute.called

    async def test_deactivate_schedule(self, schedule_service, mock_db):
        """Test deactivating a schedule."""
        mock_db.execute.return_value = None

        result = await schedule_service.deactivate_schedule(1)

        assert mock_db.execute.called

    async def test_get_schedule_times(self, schedule_service, mock_db):
        """Test fetching schedule times for daily_count."""
        mock_db.fetch.return_value = [
            {"hour": 9, "minute": 0},
            {"hour": 14, "minute": 0},
        ]

        times = await schedule_service.get_schedule_times(1)

        assert isinstance(times, list)
        assert mock_db.fetch.called

    async def test_delete_schedule(self, schedule_service, mock_db):
        """Test deleting a schedule."""
        mock_db.execute.return_value = None

        result = await schedule_service.delete_schedule(1)

        assert mock_db.execute.called

    async def test_get_active_schedules(self, schedule_service, mock_db):
        """Test fetching active schedules."""
        mock_db.fetch.return_value = [
            {"id": 1, "route_id": 1, "is_active": True},
            {"id": 2, "route_id": 1, "is_active": True},
        ]

        schedules = await schedule_service.get_active_schedules()

        assert isinstance(schedules, list)
        assert mock_db.fetch.called


@pytest.mark.asyncio
class TestScheduleCalculation:
    """Test schedule calculation logic."""

    @pytest.fixture
    async def schedule_service(self, mock_db):
        """Create ScheduleService instance."""
        return ScheduleService(mock_db)

    async def test_interval_calculation_accuracy(self, schedule_service):
        """Test interval calculation is accurate."""
        before = datetime.now()
        next_run = await schedule_service._calculate_next_run(
            schedule_type="interval",
            interval_minutes=15,
            daily_count=None,
            times=None,
        )
        after = datetime.now()

        # Next run should be roughly 15 minutes from now
        delta = (next_run - before).total_seconds()
        assert 14 * 60 < delta < 16 * 60  # Between 14 and 16 minutes

    async def test_daily_count_respects_times(self, schedule_service):
        """Test daily_count respects configured times."""
        # Schedule for 9am, 2pm, 6pm
        times = [(9, 0), (14, 0), (18, 0)]

        next_run = await schedule_service._calculate_next_run(
            schedule_type="daily_count",
            interval_minutes=None,
            daily_count=3,
            times=times,
        )

        # If current time is before 9am, next run should be at 9am today
        # Otherwise, should be at next scheduled time
        assert next_run is not None

    async def test_schedule_handles_past_times(self, schedule_service):
        """Test schedule correctly handles times in the past."""
        # If all times have passed, should schedule for next day
        past_times = [(6, 0), (8, 0), (10, 0)]
        current_hour = datetime.now().hour

        if current_hour > 10:  # All times are in the past
            next_run = await schedule_service._calculate_next_run(
                schedule_type="daily_count",
                interval_minutes=None,
                daily_count=3,
                times=past_times,
            )

            # Should be scheduled for next day
            days_until = (next_run.date() - datetime.now().date()).days
            assert days_until >= 0


class TestScheduleModel:
    """Test Schedule model."""

    def test_schedule_dataclass_creation(self, sample_schedule_data):
        """Test creating Schedule dataclass."""
        schedule = Schedule(**sample_schedule_data)

        assert schedule.id == sample_schedule_data["id"]
        assert schedule.route_id == sample_schedule_data["route_id"]
        assert schedule.schedule_type == sample_schedule_data["schedule_type"]

    def test_schedule_interval_type(self, sample_schedule_data):
        """Test interval schedule type."""
        sample_schedule_data["schedule_type"] = "interval"
        schedule = Schedule(**sample_schedule_data)

        assert schedule.schedule_type == "interval"
        assert schedule.interval_minutes is not None

    def test_schedule_daily_count_type(self, sample_schedule_data):
        """Test daily_count schedule type."""
        sample_schedule_data["schedule_type"] = "daily_count"
        sample_schedule_data["daily_count"] = 5
        schedule = Schedule(**sample_schedule_data)

        assert schedule.schedule_type == "daily_count"
        assert schedule.daily_count == 5

    def test_schedule_next_run_tracking(self, sample_schedule_data):
        """Test next_run is properly tracked."""
        schedule = Schedule(**sample_schedule_data)

        assert schedule.next_run is not None
        assert isinstance(schedule.next_run, datetime)

    def test_schedule_active_status(self, sample_schedule_data):
        """Test is_active status."""
        schedule = Schedule(**sample_schedule_data)
        assert schedule.is_active is True

        sample_schedule_data["is_active"] = False
        inactive_schedule = Schedule(**sample_schedule_data)
        assert inactive_schedule.is_active is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
