"""Tests for Rubifo professional scheduling plans."""

from datetime import datetime

import pytest

from src.core.professional_schedule import (
    CampaignPlanConfig,
    ContentMixPlanConfig,
    MultiStagePlanConfig,
    PersianQuickPlanParser,
    PlanSlotGenerator,
    SmartQueuePlanConfig,
    TimingPatternPlanConfig,
    describe_plan,
)


def test_campaign_config_accepts_persian_weekdays_and_jalali_dates():
    config = CampaignPlanConfig(
        start_date="1403/03/01",
        end_date="1403/03/15",
        active_weekdays=["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه"],
        start_time="10:00",
        end_time="23:00",
        daily_count=6,
        loop_mode=False,
    )

    assert config.daily_count == 6
    assert config.active_weekdays[0] == "شنبه"
    assert "کمپین" in describe_plan("campaign", config.model_dump())


def test_timing_pattern_humanized_slots_are_stable_and_inside_window():
    config = TimingPatternPlanConfig(
        pattern="humanized",
        start_time="09:00",
        end_time="23:00",
        daily_count=5,
        jitter_minutes=12,
    )
    generator = PlanSlotGenerator(now_utc=datetime(2024, 5, 20, 4, 0))

    slots = generator.next_slots("timing_pattern", config.model_dump(), count=5)

    assert len(slots) == 5
    rendered = [slot.tehran_time.strftime("%H:%M") for slot in slots]
    assert rendered == ["09:12", "12:18", "15:24", "18:30", "21:36"]
    assert all(slot.utc_time < slot.tehran_time for slot in slots)


def test_multi_stage_moves_from_launch_to_maintenance_stage():
    config = MultiStagePlanConfig(
        stages=[
            {"days": 3, "daily_count": 10, "start_time": "09:00", "end_time": "23:00"},
            {"days": 7, "daily_count": 5, "start_time": "10:00", "end_time": "22:00"},
        ],
        start_date="1403/03/01",
        loop_mode=True,
    )
    generator = PlanSlotGenerator(now_utc=datetime(2024, 5, 25, 6, 0))

    slots = generator.next_slots("multi_stage", config.model_dump(), count=3)

    assert len(slots) == 3
    assert {slot.metadata["stage_index"] for slot in slots} == {1}


def test_content_mix_config_uses_existing_message_types():
    config = ContentMixPlanConfig(
        quotas={"video": 2, "photo": 3, "text": 1},
        start_time="09:00",
        end_time="22:00",
        loop_mode=True,
    )

    assert config.daily_count == 6
    assert "ویدیو" in describe_plan("content_mix", config.model_dump())


def test_persian_quick_parser_understands_campaign_template():
    parsed = PersianQuickPlanParser().parse(
        "از 1403/03/01 تا 1403/03/15 روزی 5 پست شنبه تا چهارشنبه"
    )

    assert parsed.plan_kind == "campaign"
    assert parsed.config["daily_count"] == 5
    assert parsed.config["active_weekdays"] == ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه"]


def test_persian_quick_parser_understands_content_mix_template():
    parsed = PersianQuickPlanParser().parse("روزی 2 ویدیو 3 عکس 1 متن بین 9 تا 22")

    assert parsed.plan_kind == "content_mix"
    assert parsed.config["quotas"] == {"video": 2, "photo": 3, "text": 1}
    assert parsed.config["start_time"] == "09:00"
    assert parsed.config["end_time"] == "22:00"


def test_smart_queue_config_defaults_to_fifo_with_loop():
    config = SmartQueuePlanConfig(
        start_time="10:00",
        end_time="23:00",
        daily_count=8,
        loop_mode=True,
    )

    assert config.strategy == "fifo"
    assert config.loop_mode is True
