"""Tests for the user-facing publishing-program domain."""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.core.destination_service import DestinationService
from src.core.publishing_program_service import PublishingProgramService
from src.core.professional_schedule import PlanSlotGenerator, PublishingProgramConfig
from src.models.destination import DestinationChannel


def test_destination_input_normalization_accepts_username_and_rubika_link():
    assert DestinationService.normalize_channel_input("@foroushgah") == "@foroushgah"
    assert DestinationService.normalize_channel_input("https://rubika.ir/foroushgah") == "@foroushgah"


def test_destination_input_normalization_rejects_non_channel_text():
    with pytest.raises(ValueError):
        DestinationService.normalize_channel_input("foroushgah")


@pytest.mark.asyncio
async def test_record_verified_channel_upserts_a_persistent_destination(mock_db):
    mock_db.fetchrow.return_value = {
        "id": 3,
        "user_id": "u1",
        "channel_id": "@shop",
        "title": "Shop",
        "verification_status": "verified",
        "verification_error": None,
        "verified_at": datetime.now(),
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    destination = await DestinationService(mock_db).record_verification(
        "u1", "@shop", "Shop", "verified"
    )

    assert isinstance(destination, DestinationChannel)
    assert destination.channel_id == "@shop"
    assert "destination_channels" in mock_db.fetchrow.await_args.args[0]


@pytest.mark.asyncio
async def test_replacing_destination_pauses_programs_before_releasing_capacity(mock_db):
    await DestinationService(mock_db).replace("u1", 3)

    first_sql = mock_db.execute.await_args_list[0].args[0]
    second_sql = mock_db.execute.await_args_list[1].args[0]
    assert "UPDATE schedules" in first_sql
    assert "کانال مقصد جایگزین شد" in first_sql
    assert "UPDATE destination_channels" in second_sql


@pytest.mark.asyncio
async def test_removing_destination_pauses_dependent_programs(mock_db):
    await DestinationService(mock_db).remove("u1", 3)

    first_sql = mock_db.execute.await_args_list[0].args[0]
    assert "UPDATE schedules" in first_sql
    assert "کانال مقصد حذف شد" in first_sql


@pytest.mark.asyncio
async def test_program_commit_reuses_route_and_pauses_empty_content(mock_db):
    destination = DestinationChannel(id=7, user_id="u1", channel_id="@shop", verification_status="verified")
    source = SimpleNamespace(id=4, name="آموزشی")

    with patch(
        "src.core.publishing_program_service.PublishingProgramService.can_create_real_program",
        new_callable=AsyncMock,
        return_value=(True, None),
    ):
        with patch(
        "src.core.publishing_program_service.RouteService.get_or_create_internal_route",
        new_callable=AsyncMock,
        return_value=11,
        ) as route:
            with patch(
                "src.core.publishing_program_service.SourceService.count_posts",
                new_callable=AsyncMock,
                return_value=0,
            ):
                with patch(
                    "src.core.publishing_program_service.ScheduleService.create_publishing_schedule",
                    new_callable=AsyncMock,
                    return_value=SimpleNamespace(id=14, is_active=False),
                ) as schedule:
                    result = await PublishingProgramService(mock_db).commit_real_program(
                        "u1",
                        destination,
                        source,
                        {"program_mode": "recurring", "cadence": "exact_times", "times": ["09:00"]},
                    )

    route.assert_awaited_once_with("u1", source.id, destination.id, destination.channel_id, "real")
    assert schedule.await_args.kwargs["is_active"] is False
    assert schedule.await_args.kwargs["paused_reason"] == "در انتظار محتوا"
    assert result["waiting_for_content"] is True


def test_publishing_program_config_rejects_2400_and_accepts_exact_times():
    with pytest.raises(ValueError):
        PublishingProgramConfig(
            program_mode="recurring",
            cadence="exact_times",
            times=["24:00"],
        )

    config = PublishingProgramConfig(
        program_mode="dated",
        cadence="exact_times",
        times=["09:00", "23:59"],
        start_date="1405/03/04",
        end_date="1405/03/05",
    )
    assert config.times == ["09:00", "23:59"]


def test_publishing_program_generator_handles_dated_exact_times():
    config = PublishingProgramConfig(
        program_mode="dated",
        cadence="exact_times",
        times=["09:00", "20:00"],
        start_date="1405/03/04",
        end_date="1405/03/05",
    )

    slots = PlanSlotGenerator(now_utc=datetime(2026, 5, 24, 20, 0)).next_slots(
        "publishing_program", config.model_dump(), count=2
    )

    assert len(slots) == 2
    assert slots[0].tehran_time.date() <= slots[1].tehran_time.date()


@pytest.mark.asyncio
async def test_trial_can_create_only_one_real_recurring_program(mock_db):
    with patch(
        "src.core.publishing_program_service.SubscriptionService.get_access_state",
        new_callable=AsyncMock,
        return_value="trial",
    ):
        mock_db.fetchval.return_value = 1
        allowed, reason = await PublishingProgramService(mock_db).can_create_real_program(
            "u1", {"program_mode": "recurring", "cadence": "interval", "interval_minutes": 60}
        )

    assert allowed is False
    assert "یک برنامه واقعی روزانه" in reason


@pytest.mark.asyncio
async def test_expired_user_cannot_start_tutorial(mock_db):
    with patch(
        "src.core.publishing_program_service.SubscriptionService.get_access_state",
        new_callable=AsyncMock,
        return_value="expired",
    ):
        allowed, reason = await PublishingProgramService(mock_db).can_create_tutorial("u1")

    assert allowed is False
    assert "تریال" in reason


@pytest.mark.asyncio
async def test_adding_first_content_activates_waiting_program(mock_db):
    waiting_row = {
        "id": 20,
        "user_id": "u1",
        "route_id": 4,
        "schedule_type": "publishing_program",
        "plan_kind": "publishing_program",
        "config": {"program_mode": "recurring", "cadence": "exact_times", "times": ["09:00"]},
        "next_run": None,
        "is_active": False,
        "paused_reason": "در انتظار محتوا",
    }
    mock_db.fetch.return_value = [waiting_row]
    with patch(
        "src.core.publishing_program_service.ScheduleService.calculate_next_for_schedule",
        new_callable=AsyncMock,
        return_value=datetime.now() + timedelta(hours=1),
    ):
        activated = await PublishingProgramService(mock_db).activate_waiting_programs(5)

    assert activated == 1
    assert "is_active = true" in mock_db.execute.await_args.args[0]
