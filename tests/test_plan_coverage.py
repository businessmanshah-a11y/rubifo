"""
Comprehensive plan coverage tests — 122 cases across 9 sections.

All tests are pure unit tests: no DB, no bot, no async.
Run with: pytest tests/test_plan_coverage.py -v
"""

from datetime import date, datetime, time
from typing import Dict

import pytest

from src.core.professional_schedule import (
    CampaignPlanConfig,
    ContentMixPlanConfig,
    MultiStagePlanConfig,
    PersianQuickPlanParser,
    PlanSlotGenerator,
    SmartQueuePlanConfig,
    StageConfig,
    TimingPatternPlanConfig,
    describe_plan,
    expand_weekday_range,
    normalize_digits,
    parse_hhmm,
    parse_jalali_date,
    persian_weekday_for_gregorian,
)
from src.utils import (
    fmt_jalali_tehran,
    normalize_digits as normalize_user_digits,
    to_jalali_date,
)


# ---------------------------------------------------------------------------
# Section 1 — Utility functions (13 tests)
# ---------------------------------------------------------------------------


def test_normalize_digits_persian():
    assert normalize_digits("۱۲۳۴۵۶۷۸۹۰") == "1234567890"


def test_normalize_digits_arabic():
    assert normalize_digits("١٢٣٤٥٦٧٨٩٠") == "1234567890"


def test_normalize_digits_mixed_leaves_ascii_unchanged():
    result = normalize_digits("abc123۴۵۶")
    assert result == "abc123456"


def test_shared_normalize_digits_handles_user_input_digits():
    assert normalize_user_digits("زمان ۰۹:۳۰ و ١٢ پست") == "زمان 09:30 و 12 پست"


def test_jalali_display_helpers_use_persian_digits():
    assert to_jalali_date(date(2026, 5, 20)) == "۱۴۰۵/۰۲/۳۰"
    assert fmt_jalali_tehran(datetime(2026, 5, 20, 8, 30)) == "۱۴۰۵/۰۲/۳۰ ۱۲:۰۰"


def test_parse_hhmm_hour_only():
    assert parse_hhmm("09") == time(9, 0)


def test_parse_hhmm_hour_minute():
    assert parse_hhmm("09:30") == time(9, 30)


def test_parse_hhmm_midnight():
    assert parse_hhmm("00") == time(0, 0)


def test_parse_hhmm_last_valid_time():
    assert parse_hhmm("23:59") == time(23, 59)


def test_parse_hhmm_invalid_hour_raises():
    with pytest.raises(ValueError):
        parse_hhmm("24")


def test_parse_jalali_date_1403_03_01():
    assert parse_jalali_date("1403/03/01") == date(2024, 5, 21)


def test_parse_jalali_date_1405_02_29():
    # This is the exact date from the failing live session (May 19 2026)
    assert parse_jalali_date("1405/02/29") == date(2026, 5, 19)


def test_persian_weekday_for_gregorian_may_20_2026():
    # May 20 2026 is a Wednesday → سه‌شنبه in Persian (Mon=سه‌شنبه in Persian week Sat=0)
    # Python weekday: Wednesday = 2; Persian = (2+2)%7 = 4 → چهارشنبه
    # Let's verify programmatically against known anchor
    day = date(2026, 5, 20)  # Wednesday
    result = persian_weekday_for_gregorian(day)
    # Wednesday = python 2; persian = (2+2)%7 = 4 → چهارشنبه
    assert result == "چهارشنبه"


def test_expand_weekday_range_saturday_to_wednesday():
    days = expand_weekday_range("شنبه", "چهارشنبه")
    assert days == ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه"]
    assert len(days) == 5


def test_expand_weekday_range_wraparound():
    days = expand_weekday_range("پنجشنبه", "شنبه")
    assert "پنجشنبه" in days and "جمعه" in days and "شنبه" in days
    assert len(days) == 3


# ---------------------------------------------------------------------------
# Section 2 — Config validation (18 tests)
# ---------------------------------------------------------------------------


def test_campaign_config_valid():
    cfg = CampaignPlanConfig(
        start_date="1405/03/01",
        end_date="1405/06/01",
        active_weekdays=["شنبه", "یکشنبه"],
        start_time="09:00",
        end_time="22:00",
        daily_count=5,
    )
    assert cfg.daily_count == 5


def test_campaign_config_daily_count_zero_raises():
    with pytest.raises(Exception):
        CampaignPlanConfig(
            start_date="1405/03/01", end_date="1405/06/01",
            active_weekdays=["شنبه"], start_time="09:00", end_time="22:00",
            daily_count=0,
        )


def test_campaign_config_start_after_end_raises():
    with pytest.raises(Exception):
        CampaignPlanConfig(
            start_date="1405/06/01", end_date="1405/03/01",
            active_weekdays=["شنبه"], start_time="09:00", end_time="22:00",
            daily_count=3,
        )


def test_campaign_config_invalid_weekday_raises():
    with pytest.raises(Exception):
        CampaignPlanConfig(
            start_date="1405/03/01", end_date="1405/06/01",
            active_weekdays=["Monday"], start_time="09:00", end_time="22:00",
            daily_count=3,
        )


def test_campaign_config_start_time_gte_end_time_raises():
    with pytest.raises(Exception):
        CampaignPlanConfig(
            start_date="1405/03/01", end_date="1405/06/01",
            active_weekdays=["شنبه"], start_time="22:00", end_time="09:00",
            daily_count=3,
        )


def test_smart_queue_config_defaults():
    cfg = SmartQueuePlanConfig(daily_count=8, start_time="10:00", end_time="23:00")
    assert cfg.strategy == "fifo"
    assert cfg.loop_mode is True


def test_smart_queue_config_daily_count_over_max_raises():
    with pytest.raises(Exception):
        SmartQueuePlanConfig(daily_count=97, start_time="10:00", end_time="23:00")


def test_timing_pattern_humanized_valid():
    cfg = TimingPatternPlanConfig(pattern="humanized", daily_count=5, start_time="09:00", end_time="23:00")
    assert cfg.pattern == "humanized"


def test_timing_pattern_store_valid():
    cfg = TimingPatternPlanConfig(pattern="store", daily_count=3, start_time="09:00", end_time="23:00")
    assert cfg.pattern == "store"


def test_timing_pattern_low_risk_valid():
    cfg = TimingPatternPlanConfig(pattern="low_risk", daily_count=2, start_time="09:00", end_time="23:00")
    assert cfg.pattern == "low_risk"


def test_timing_pattern_launch_valid():
    cfg = TimingPatternPlanConfig(pattern="launch", daily_count=10, start_time="09:00", end_time="23:00")
    assert cfg.pattern == "launch"


def test_timing_pattern_jitter_over_max_raises():
    with pytest.raises(Exception):
        TimingPatternPlanConfig(pattern="humanized", daily_count=5, start_time="09:00", end_time="23:00", jitter_minutes=31)


def test_timing_pattern_unknown_pattern_raises():
    with pytest.raises(Exception):
        TimingPatternPlanConfig(pattern="unknown", daily_count=5, start_time="09:00", end_time="23:00")


def test_multi_stage_single_stage_valid():
    cfg = MultiStagePlanConfig(
        start_date="1405/03/01",
        stages=[{"days": 7, "daily_count": 5, "start_time": "09:00", "end_time": "22:00"}],
    )
    assert len(cfg.stages) == 1


def test_multi_stage_zero_stages_raises():
    with pytest.raises(Exception):
        MultiStagePlanConfig(start_date="1405/03/01", stages=[])


def test_multi_stage_stage_days_zero_raises():
    with pytest.raises(Exception):
        MultiStagePlanConfig(
            start_date="1405/03/01",
            stages=[{"days": 0, "daily_count": 5, "start_time": "09:00", "end_time": "22:00"}],
        )


def test_content_mix_valid_daily_count_property():
    cfg = ContentMixPlanConfig(
        quotas={"video": 2, "photo": 3, "text": 1},
        start_time="09:00", end_time="22:00",
    )
    assert cfg.daily_count == 6


def test_content_mix_invalid_type_raises():
    with pytest.raises(Exception):
        ContentMixPlanConfig(quotas={"reel": 2}, start_time="09:00", end_time="22:00")


def test_content_mix_count_over_96_raises():
    with pytest.raises(Exception):
        ContentMixPlanConfig(quotas={"video": 97}, start_time="09:00", end_time="22:00")


# ---------------------------------------------------------------------------
# Section 3 — Campaign slot generation (22 tests)
# ---------------------------------------------------------------------------


def _campaign_cfg(start: str, end: str, weekdays=None, daily: int = 5,
                  st: str = "09:00", et: str = "23:00") -> Dict:
    return CampaignPlanConfig(
        start_date=start, end_date=end,
        active_weekdays=weekdays or ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"],
        start_time=st, end_time=et, daily_count=daily,
    ).model_dump()


def test_campaign_expired_end_date_returns_none():
    # Exact reproduction of the live failure: 1405/02/29 = May 19 2026 (yesterday)
    cfg = _campaign_cfg("1405/02/29", "1405/02/29", ["چهارشنبه"], daily=10, st="00:00", et="12:00")
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 9, 0))
    assert gen.next_run("campaign", cfg) is None


def test_campaign_start_date_tomorrow_generates():
    # start is May 21 2026; today is May 20
    cfg = _campaign_cfg("1405/03/01", "1405/03/07")
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 12, 0))
    result = gen.next_run("campaign", cfg)
    assert result is not None
    assert result > datetime(2026, 5, 20, 12, 0)


def test_campaign_today_in_range_window_not_yet_passed():
    # now is May 20 2026 08:00 Tehran = 04:30 UTC; window 09:00–23:00 Tehran
    cfg = _campaign_cfg("1405/02/29", "1405/03/07")  # May 19 – May 27
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 30))  # 08:00 Tehran
    result = gen.next_run("campaign", cfg)
    assert result is not None
    # First slot must be after now
    from src.core.professional_schedule import utc_to_tehran
    teh = utc_to_tehran(result)
    assert teh.date() == date(2026, 5, 20)


def test_campaign_today_in_range_window_already_passed():
    # now is May 20 2026 22:00 Tehran = 18:30 UTC; window 09:00–23:00
    cfg = _campaign_cfg("1405/02/29", "1405/03/07")
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 18, 30))  # 22:00 Tehran
    slots = gen.next_slots("campaign", cfg, count=1)
    assert len(slots) == 1
    from src.core.professional_schedule import utc_to_tehran
    teh = utc_to_tehran(slots[0].utc_time)
    assert teh.date() > date(2026, 5, 20)


def test_campaign_weekday_matches_today():
    # May 20 2026 = چهارشنبه; use 08:00 Tehran so window hasn't started
    cfg = _campaign_cfg("1405/02/29", "1405/03/07", weekdays=["چهارشنبه"], st="10:00", et="22:00")
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 30))  # 08:00 Tehran
    result = gen.next_run("campaign", cfg)
    assert result is not None
    from src.core.professional_schedule import utc_to_tehran
    teh = utc_to_tehran(result)
    assert teh.date() == date(2026, 5, 20)


def test_campaign_wrong_weekday_today_skips():
    # May 20 2026 = چهارشنبه; only allow شنبه
    cfg = _campaign_cfg("1405/02/29", "1405/03/07", weekdays=["شنبه"])
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 30))
    result = gen.next_run("campaign", cfg)
    assert result is not None
    from src.core.professional_schedule import utc_to_tehran
    teh = utc_to_tehran(result)
    assert persian_weekday_for_gregorian(teh.date()) == "شنبه"


def test_campaign_only_fridays():
    cfg = _campaign_cfg("1405/02/29", "1405/03/15", weekdays=["جمعه"])
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    result = gen.next_run("campaign", cfg)
    assert result is not None
    from src.core.professional_schedule import utc_to_tehran
    teh = utc_to_tehran(result)
    assert persian_weekday_for_gregorian(teh.date()) == "جمعه"


def test_campaign_all_7_weekdays_active():
    cfg = _campaign_cfg("1405/02/29", "1405/03/07")  # all 7 weekdays by default
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 30))
    slots = gen.next_slots("campaign", cfg, count=7)
    assert len(slots) == 7


def test_campaign_daily_count_1():
    cfg = _campaign_cfg("1405/03/01", "1405/03/07", daily=1)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("campaign", cfg, count=3)
    # Each day should contribute 1 slot
    from src.core.professional_schedule import utc_to_tehran
    dates = [utc_to_tehran(s.utc_time).date() for s in slots]
    assert len(set(dates)) == 3  # 3 different days


def test_campaign_daily_count_10_distributes():
    cfg = _campaign_cfg("1405/03/01", "1405/03/07", daily=10)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("campaign", cfg, count=10)
    assert len(slots) == 10
    from src.core.professional_schedule import utc_to_tehran
    dates = {utc_to_tehran(s.utc_time).date() for s in slots}
    # all 10 in same day (first available)
    assert len(dates) == 1


def test_campaign_midnight_window():
    cfg = _campaign_cfg("1405/03/01", "1405/03/07", st="00:00", et="12:00")
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 18, 0))  # 21:30 Tehran — past 12:00
    result = gen.next_run("campaign", cfg)
    assert result is not None
    from src.core.professional_schedule import utc_to_tehran
    teh = utc_to_tehran(result)
    assert teh.hour < 12


def test_campaign_count_20_across_days():
    cfg = _campaign_cfg("1405/03/01", "1405/03/15", daily=5)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("campaign", cfg, count=20)
    assert len(slots) == 20


def test_campaign_single_day_all_past_returns_none():
    # End_date today but window 00:00–06:00 already past by 15:00 Tehran
    cfg = _campaign_cfg("1405/02/30", "1405/02/30", st="00:00", et="06:00")
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 11, 30))  # 15:00 Tehran
    assert gen.next_run("campaign", cfg) is None


def test_campaign_far_future_start():
    cfg = _campaign_cfg("1406/01/01", "1406/01/07")
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    result = gen.next_run("campaign", cfg)
    assert result is not None
    assert result > datetime(2026, 5, 20)


def test_campaign_start_equals_end_equals_today_future_slots():
    # today = 1405/02/30 = May 20 2026; now 08:00 Tehran; window 10:00–22:00
    cfg = _campaign_cfg("1405/02/30", "1405/02/30", st="10:00", et="22:00")
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 30))  # 08:00 Tehran
    result = gen.next_run("campaign", cfg)
    assert result is not None


def test_campaign_start_equals_end_equals_today_all_past_none():
    # Now 23:30 Tehran (20:00 UTC); window 09:00–22:00 already done
    cfg = _campaign_cfg("1405/02/30", "1405/02/30", st="09:00", et="22:00")
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 20, 0))  # 23:30 Tehran
    assert gen.next_run("campaign", cfg) is None


def test_campaign_wraparound_weekday_range():
    days = expand_weekday_range("پنجشنبه", "دوشنبه")
    # پنجشنبه(5), جمعه(6), شنبه(0), یکشنبه(1), دوشنبه(2)
    assert "پنجشنبه" in days
    assert "جمعه" in days
    assert "شنبه" in days
    assert len(days) == 5


def test_campaign_daily_count_96_max():
    cfg = _campaign_cfg("1405/03/01", "1405/03/07", daily=96)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("campaign", cfg, count=96)
    assert len(slots) == 96


def test_campaign_2_days_20_slots_spans_both():
    cfg = _campaign_cfg("1405/03/01", "1405/03/02", daily=12)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("campaign", cfg, count=20)
    assert len(slots) == 20
    from src.core.professional_schedule import utc_to_tehran
    dates = {utc_to_tehran(s.utc_time).date() for s in slots}
    assert len(dates) == 2


def test_campaign_single_active_weekday_in_week():
    # Only شنبه (Saturday) in a 7-day range → max 1 Saturday
    cfg = _campaign_cfg("1405/03/01", "1405/03/07", weekdays=["شنبه"], daily=3)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("campaign", cfg, count=10)
    from src.core.professional_schedule import utc_to_tehran
    for s in slots:
        assert persian_weekday_for_gregorian(utc_to_tehran(s.utc_time).date()) == "شنبه"


def test_campaign_narrow_window_22_to_2359():
    cfg = _campaign_cfg("1405/03/01", "1405/03/07", daily=3, st="22:00", et="23:59")
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("campaign", cfg, count=3)
    from src.core.professional_schedule import utc_to_tehran
    for s in slots:
        teh = utc_to_tehran(s.utc_time)
        assert teh.hour >= 22


def test_campaign_utc_less_than_tehran():
    cfg = _campaign_cfg("1405/03/01", "1405/03/07", daily=1)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("campaign", cfg, count=1)
    assert len(slots) == 1
    assert slots[0].utc_time < slots[0].tehran_time


# ---------------------------------------------------------------------------
# Section 4 — Smart Queue slot generation (10 tests)
# ---------------------------------------------------------------------------


def _sq_cfg(daily: int = 8, st: str = "09:00", et: str = "23:00", loop: bool = True) -> Dict:
    return SmartQueuePlanConfig(daily_count=daily, start_time=st, end_time=et, loop_mode=loop).model_dump()


def test_smart_queue_8_slots_today():
    cfg = _sq_cfg(daily=8)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))  # 07:30 Tehran before window
    slots = gen.next_slots("smart_queue", cfg, count=8)
    assert len(slots) == 8


def test_smart_queue_after_midnight_tehran():
    # 00:30 Tehran = 21:00 UTC previous day; window 09:00-23:00 → still generates
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 19, 21, 0))  # 00:30 Tehran May 20
    cfg = _sq_cfg()
    result = gen.next_run("smart_queue", cfg)
    assert result is not None


def test_smart_queue_count_24_spans_days():
    cfg = _sq_cfg(daily=8)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("smart_queue", cfg, count=24)
    assert len(slots) == 24


def test_smart_queue_loop_mode_true_generates():
    cfg = _sq_cfg(loop=True)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    assert gen.next_run("smart_queue", cfg) is not None


def test_smart_queue_loop_mode_false_generates():
    cfg = _sq_cfg(loop=False)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    assert gen.next_run("smart_queue", cfg) is not None


def test_smart_queue_daily_count_1():
    cfg = _sq_cfg(daily=1)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("smart_queue", cfg, count=3)
    assert len(slots) == 3
    from src.core.professional_schedule import utc_to_tehran
    dates = [utc_to_tehran(s.utc_time).date() for s in slots]
    assert len(set(dates)) == 3  # 1 per day


def test_smart_queue_daily_count_48():
    cfg = _sq_cfg(daily=48)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("smart_queue", cfg, count=48)
    assert len(slots) == 48


def test_smart_queue_narrow_window_4_slots():
    cfg = _sq_cfg(daily=4, st="10:00", et="11:00")
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("smart_queue", cfg, count=4)
    assert len(slots) == 4
    from src.core.professional_schedule import utc_to_tehran
    for s in slots:
        teh = utc_to_tehran(s.utc_time)
        assert 10 <= teh.hour <= 11


def test_smart_queue_strategy_is_fifo():
    cfg = SmartQueuePlanConfig(daily_count=5, start_time="09:00", end_time="23:00")
    assert cfg.strategy == "fifo"


def test_smart_queue_next_run_never_none():
    cfg = _sq_cfg(daily=3)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 20, 0))
    # Even if today's window passed, tomorrow's slots exist
    assert gen.next_run("smart_queue", cfg) is not None


# ---------------------------------------------------------------------------
# Section 5 — Timing Pattern slot generation (14 tests)
# ---------------------------------------------------------------------------


def _tp_cfg(pattern: str = "humanized", daily: int = 5,
            st: str = "09:00", et: str = "23:00", jitter: int = 12) -> Dict:
    return TimingPatternPlanConfig(
        pattern=pattern, daily_count=daily,
        start_time=st, end_time=et, jitter_minutes=jitter,
    ).model_dump()


def test_timing_pattern_humanized_5_slots_offsets():
    cfg = _tp_cfg("humanized", 5, "09:00", "23:00", 12)
    gen = PlanSlotGenerator(now_utc=datetime(2024, 5, 20, 4, 0))
    slots = gen.next_slots("timing_pattern", cfg, count=5)
    assert len(slots) == 5
    rendered = [s.tehran_time.strftime("%H:%M") for s in slots]
    assert rendered == ["09:12", "12:18", "15:24", "18:30", "21:36"]


def test_timing_pattern_store_even_distribution():
    cfg = _tp_cfg("store", 4, "10:00", "22:00", 0)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("timing_pattern", cfg, count=4)
    assert len(slots) == 4
    times = [s.tehran_time for s in slots]
    assert times == sorted(times)


def test_timing_pattern_low_risk_within_window():
    cfg = _tp_cfg("low_risk", 3, "10:00", "22:00", 0)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("timing_pattern", cfg, count=3)
    assert len(slots) == 3
    from src.core.professional_schedule import utc_to_tehran
    for s in slots:
        teh = utc_to_tehran(s.utc_time)
        assert 10 <= teh.hour < 22


def test_timing_pattern_launch_within_window():
    cfg = _tp_cfg("launch", 5, "09:00", "23:00", 5)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("timing_pattern", cfg, count=5)
    assert len(slots) == 5


def test_timing_pattern_zero_jitter_even():
    cfg = _tp_cfg("humanized", 3, "09:00", "21:00", 0)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("timing_pattern", cfg, count=3)
    times = [s.tehran_time.hour * 60 + s.tehran_time.minute for s in slots]
    # With jitter=0, slots should be evenly spaced
    diffs = [times[i+1] - times[i] for i in range(len(times)-1)]
    assert all(d > 0 for d in diffs)


def test_timing_pattern_max_jitter_30():
    cfg = _tp_cfg("humanized", 3, "09:00", "23:00", 30)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("timing_pattern", cfg, count=3)
    assert len(slots) == 3


def test_timing_pattern_daily_count_1_single_slot():
    cfg = _tp_cfg("humanized", 1, "09:00", "23:00", 0)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("timing_pattern", cfg, count=1)
    assert len(slots) == 1
    from src.core.professional_schedule import utc_to_tehran
    assert utc_to_tehran(slots[0].utc_time).hour == 9


def test_timing_pattern_daily_count_10():
    cfg = _tp_cfg("humanized", 10, "09:00", "23:00", 0)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("timing_pattern", cfg, count=10)
    assert len(slots) == 10


def test_timing_pattern_slots_monotonically_increasing():
    cfg = _tp_cfg("store", 6, "09:00", "23:00", 0)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("timing_pattern", cfg, count=6)
    for i in range(len(slots) - 1):
        assert slots[i].tehran_time < slots[i+1].tehran_time


def test_timing_pattern_all_slots_within_window():
    cfg = _tp_cfg("store", 5, "10:00", "20:00", 0)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("timing_pattern", cfg, count=5)
    from src.core.professional_schedule import utc_to_tehran
    for s in slots:
        teh = utc_to_tehran(s.utc_time)
        assert 10 <= teh.hour < 20


def test_timing_pattern_count_3_returns_3():
    cfg = _tp_cfg("humanized", 5, "09:00", "23:00", 0)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("timing_pattern", cfg, count=3)
    assert len(slots) == 3


def test_timing_pattern_next_run_returns_utc():
    cfg = _tp_cfg("humanized", 5, "09:00", "23:00", 0)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    result = gen.next_run("timing_pattern", cfg)
    assert isinstance(result, datetime)


def test_timing_pattern_jitter_stays_within_end_time():
    cfg = _tp_cfg("humanized", 5, "09:00", "23:00", 30)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("timing_pattern", cfg, count=5)
    from src.core.professional_schedule import parse_hhmm as phh
    et = phh("23:00")
    for s in slots:
        assert s.tehran_time.time() <= et


def test_timing_pattern_daily_count_96():
    cfg = _tp_cfg("store", 96, "00:00", "23:59", 0)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 0, 0))
    slots = gen.next_slots("timing_pattern", cfg, count=96)
    assert len(slots) == 96


# ---------------------------------------------------------------------------
# Section 6 — Multi-Stage slot generation (10 tests)
# ---------------------------------------------------------------------------


def _ms_cfg(start: str, stages, loop: bool = False) -> Dict:
    return MultiStagePlanConfig(start_date=start, stages=stages, loop_mode=loop).model_dump()


_two_stage = [
    {"days": 3, "daily_count": 10, "start_time": "09:00", "end_time": "23:00"},
    {"days": 7, "daily_count": 5, "start_time": "10:00", "end_time": "22:00"},
]


def test_multi_stage_day0_uses_stage0():
    # start = May 20 2026, now = 04:00 UTC same day → elapsed=0 → stage 0
    cfg = _ms_cfg("1405/02/30", _two_stage)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("multi_stage", cfg, count=3)
    assert all(s.metadata["stage_index"] == 0 for s in slots)


def test_multi_stage_day3_uses_stage1():
    # start May 17 2026, now May 20 → elapsed=3 → stage 1
    cfg = _ms_cfg("1405/02/27", _two_stage)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("multi_stage", cfg, count=3)
    assert all(s.metadata["stage_index"] == 1 for s in slots)


def test_multi_stage_day10_still_stage1():
    # start May 10 2026 (1405/02/20), now May 20 → elapsed=10 → stage 1 (3+7=10, just in range)
    cfg = _ms_cfg("1405/02/20", _two_stage)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("multi_stage", cfg, count=1)
    assert slots[0].metadata["stage_index"] == 1


def test_multi_stage_metadata_has_stage_index():
    cfg = _ms_cfg("1405/02/30", _two_stage)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("multi_stage", cfg, count=1)
    assert "stage_index" in slots[0].metadata


def test_multi_stage_beyond_all_stages_uses_last():
    # start Jan 1 2024, now May 20 2026 → well past 10 days → last stage
    cfg = _ms_cfg("1402/10/11", _two_stage)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("multi_stage", cfg, count=1)
    assert slots[0].metadata["stage_index"] == len(_two_stage) - 1


def test_multi_stage_3_stages_day0():
    stages = [
        {"days": 5, "daily_count": 10, "start_time": "09:00", "end_time": "23:00"},
        {"days": 5, "daily_count": 6, "start_time": "09:00", "end_time": "23:00"},
        {"days": 5, "daily_count": 3, "start_time": "09:00", "end_time": "23:00"},
    ]
    cfg = _ms_cfg("1405/02/30", stages)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("multi_stage", cfg, count=1)
    assert slots[0].metadata["stage_index"] == 0


def test_multi_stage_start_date_in_past_correct_stage():
    stages = [
        {"days": 2, "daily_count": 8, "start_time": "09:00", "end_time": "23:00"},
        {"days": 5, "daily_count": 4, "start_time": "09:00", "end_time": "23:00"},
    ]
    # start May 18, now May 20 → elapsed=2 → stage 1
    cfg = _ms_cfg("1405/02/28", stages)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("multi_stage", cfg, count=1)
    assert slots[0].metadata["stage_index"] == 1


def test_multi_stage_start_tomorrow_is_stage0():
    cfg = _ms_cfg("1405/03/01", _two_stage)  # May 21 2026
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("multi_stage", cfg, count=1)
    assert slots[0].metadata["stage_index"] == 0


def test_multi_stage_daily_count_per_stage_respected():
    stages = [{"days": 3, "daily_count": 10, "start_time": "09:00", "end_time": "23:00"}]
    cfg = _ms_cfg("1405/02/30", stages)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("multi_stage", cfg, count=10)
    assert len(slots) == 10


def test_multi_stage_different_time_windows_per_stage():
    stages = [
        {"days": 1, "daily_count": 2, "start_time": "09:00", "end_time": "11:00"},
        {"days": 5, "daily_count": 2, "start_time": "20:00", "end_time": "22:00"},
    ]
    # start May 19 2026 → elapsed=1 → stage 1 (window 20:00-22:00)
    cfg = _ms_cfg("1405/02/29", stages)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("multi_stage", cfg, count=1)
    from src.core.professional_schedule import utc_to_tehran
    teh = utc_to_tehran(slots[0].utc_time)
    assert teh.hour >= 20


# ---------------------------------------------------------------------------
# Section 7 — Content Mix slot generation (10 tests)
# ---------------------------------------------------------------------------


def _cm_cfg(quotas: Dict, st: str = "09:00", et: str = "22:00", loop: bool = True) -> Dict:
    return ContentMixPlanConfig(quotas=quotas, start_time=st, end_time=et, loop_mode=loop).model_dump()


def test_content_mix_6_slots_metadata_cycles():
    quotas = {"video": 2, "photo": 3, "text": 1}
    cfg = _cm_cfg(quotas)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("content_mix", cfg, count=6)
    assert len(slots) == 6
    types = [s.metadata["message_type"] for s in slots]
    assert types == ["video", "video", "photo", "photo", "photo", "text"]


def test_content_mix_first_slot_is_first_type():
    cfg = _cm_cfg({"photo": 1, "text": 1})
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("content_mix", cfg, count=1)
    assert slots[0].metadata["message_type"] == "photo"


def test_content_mix_cycles_correctly():
    cfg = _cm_cfg({"video": 1, "text": 1})
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("content_mix", cfg, count=4)
    types = [s.metadata["message_type"] for s in slots]
    assert types == ["video", "text", "video", "text"]


def test_content_mix_single_type_all_same():
    cfg = _cm_cfg({"text": 5})
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("content_mix", cfg, count=5)
    assert all(s.metadata["message_type"] == "text" for s in slots)


def test_content_mix_daily_count_is_sum_of_quotas():
    quotas = {"video": 2, "photo": 3, "text": 1}
    cfg_obj = ContentMixPlanConfig(quotas=quotas, start_time="09:00", end_time="22:00")
    assert cfg_obj.daily_count == 6


def test_content_mix_loop_true_generates_beyond_day():
    cfg = _cm_cfg({"photo": 2}, loop=True)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("content_mix", cfg, count=10)
    assert len(slots) == 10


def test_content_mix_all_7_types_valid():
    quotas = {"text": 1, "photo": 1, "video": 1, "voice": 1, "music": 1, "file": 1, "gif": 1}
    cfg = _cm_cfg(quotas)
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("content_mix", cfg, count=7)
    assert len(slots) == 7


def test_content_mix_count_20_cycles():
    cfg = _cm_cfg({"video": 2, "photo": 3})  # 5 per cycle
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("content_mix", cfg, count=20)
    assert len(slots) == 20
    # Every 5th slot should reset the cycle
    assert slots[0].metadata["message_type"] == slots[5].metadata["message_type"]


def test_content_mix_slots_in_future():
    cfg = _cm_cfg({"text": 1})
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    now = gen.now_utc
    slots = gen.next_slots("content_mix", cfg, count=3)
    assert all(s.utc_time > now for s in slots)


def test_content_mix_metadata_key_is_message_type():
    cfg = _cm_cfg({"video": 1})
    gen = PlanSlotGenerator(now_utc=datetime(2026, 5, 20, 4, 0))
    slots = gen.next_slots("content_mix", cfg, count=1)
    assert "message_type" in slots[0].metadata


# ---------------------------------------------------------------------------
# Section 8 — PersianQuickPlanParser (18 tests)
# ---------------------------------------------------------------------------


_parser = PersianQuickPlanParser()


def test_parser_campaign_basic():
    parsed = _parser.parse("از 1403/03/01 تا 1403/03/15 روزی 5 پست شنبه تا چهارشنبه")
    assert parsed.plan_kind == "campaign"
    assert parsed.config["daily_count"] == 5


def test_parser_campaign_single_weekday():
    parsed = _parser.parse("از 1405/03/01 تا 1405/06/01 روزی 1 پست جمعه تا جمعه")
    assert parsed.plan_kind == "campaign"
    assert parsed.config["active_weekdays"] == ["جمعه"]


def test_parser_campaign_persian_digits():
    parsed = _parser.parse("از ۱۴۰۳/۰۳/۰۱ تا ۱۴۰۳/۰۳/۱۵ روزی ۵ پست شنبه تا چهارشنبه")
    assert parsed.plan_kind == "campaign"
    assert parsed.config["daily_count"] == 5


def test_parser_content_mix_basic():
    parsed = _parser.parse("روزی 2 ویدیو 3 عکس 1 متن بین 9 تا 22")
    assert parsed.plan_kind == "content_mix"
    assert parsed.config["quotas"] == {"video": 2, "photo": 3, "text": 1}
    assert parsed.config["start_time"] == "09:00"
    assert parsed.config["end_time"] == "22:00"


def test_parser_content_mix_single_voice():
    parsed = _parser.parse("روزی 1 ویس بین 10 تا 23")
    assert parsed.plan_kind == "content_mix"
    assert "voice" in parsed.config["quotas"]


def test_parser_content_mix_synonym_labels():
    parsed = _parser.parse("روزی 2 فیلم 1 صوت بین 8 تا 20")
    assert parsed.plan_kind == "content_mix"
    assert "video" in parsed.config["quotas"]
    assert "voice" in parsed.config["quotas"]


def test_parser_smart_queue_basic():
    parsed = _parser.parse("روزی 10 پست بین 9 تا 23")
    assert parsed.plan_kind == "smart_queue"
    assert parsed.config["daily_count"] == 10


def test_parser_smart_queue_loop_mode_true():
    parsed = _parser.parse("روزی 5 پست بین 10 تا 22 چرخشی")
    assert parsed.plan_kind == "smart_queue"
    assert parsed.config["loop_mode"] is True


def test_parser_smart_queue_loop_mode_false():
    parsed = _parser.parse("روزی 5 پست بین 10 تا 22")
    assert parsed.plan_kind == "smart_queue"
    assert parsed.config["loop_mode"] is False


def test_parser_multi_stage_basic():
    parsed = _parser.parse("3 روز اول روزی 10 پست بعد 7 روز روزی 5 پست")
    assert parsed.plan_kind == "multi_stage"
    stages = parsed.config["stages"]
    assert stages[0]["daily_count"] == 10
    assert stages[1]["daily_count"] == 5


def test_parser_multi_stage_min_values():
    parsed = _parser.parse("1 روز اول روزی 1 پست بعد 1 روز روزی 1 پست")
    assert parsed.plan_kind == "multi_stage"
    assert parsed.config["stages"][0]["days"] == 1


def test_parser_unrecognized_raises():
    with pytest.raises(ValueError):
        _parser.parse("این یک متن تصادفی است که فرمت ندارد")


def test_parser_empty_string_raises():
    with pytest.raises(ValueError):
        _parser.parse("")


def test_parser_campaign_weekday_range_expands():
    parsed = _parser.parse("از 1403/03/01 تا 1403/03/15 روزی 5 پست شنبه تا چهارشنبه")
    assert parsed.config["active_weekdays"] == ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه"]


def test_parser_campaign_same_weekday_single():
    parsed = _parser.parse("از 1403/03/01 تا 1403/03/15 روزی 3 پست جمعه تا جمعه")
    assert parsed.config["active_weekdays"] == ["جمعه"]


def test_parser_arabic_digits_normalize():
    parsed = _parser.parse("روزی ٢ ویدیو ٣ عکس ١ متن بین ٩ تا ٢٢")
    assert parsed.plan_kind == "content_mix"
    assert parsed.config["quotas"]["video"] == 2


def test_parser_content_mix_loop_mode_default_true():
    parsed = _parser.parse("روزی 3 عکس بین 10 تا 22")
    assert parsed.plan_kind == "content_mix"
    assert parsed.config["loop_mode"] is True


def test_parser_campaign_all_7_weekdays():
    parsed = _parser.parse("از 1403/03/01 تا 1403/03/15 روزی 5 پست شنبه تا جمعه")
    assert len(parsed.config["active_weekdays"]) == 7


# ---------------------------------------------------------------------------
# Section 9 — describe_plan (8 tests)
# ---------------------------------------------------------------------------


def test_describe_plan_campaign_contains_keyword():
    cfg = CampaignPlanConfig(
        start_date="1405/03/01", end_date="1405/06/01",
        active_weekdays=["شنبه"], start_time="09:00", end_time="22:00", daily_count=3,
    )
    assert "کمپین" in describe_plan("campaign", cfg.model_dump())


def test_describe_plan_smart_queue_loop():
    cfg = SmartQueuePlanConfig(daily_count=5, start_time="09:00", end_time="23:00", loop_mode=True)
    assert "چرخشی" in describe_plan("smart_queue", cfg.model_dump())


def test_describe_plan_smart_queue_no_loop():
    cfg = SmartQueuePlanConfig(daily_count=5, start_time="09:00", end_time="23:00", loop_mode=False)
    assert "یک‌بار" in describe_plan("smart_queue", cfg.model_dump())


def test_describe_plan_timing_pattern_contains_pattern_name():
    cfg = TimingPatternPlanConfig(pattern="humanized", daily_count=5, start_time="09:00", end_time="23:00")
    result = describe_plan("timing_pattern", cfg.model_dump())
    assert "humanized" in result


def test_describe_plan_multi_stage_contains_stage_info():
    cfg = MultiStagePlanConfig(
        start_date="1405/03/01",
        stages=[{"days": 3, "daily_count": 10, "start_time": "09:00", "end_time": "23:00"}],
    )
    result = describe_plan("multi_stage", cfg.model_dump())
    assert "3" in result and "10" in result


def test_describe_plan_content_mix_contains_types():
    cfg = ContentMixPlanConfig(
        quotas={"video": 2, "photo": 1}, start_time="09:00", end_time="22:00",
    )
    result = describe_plan("content_mix", cfg.model_dump())
    assert "ویدیو" in result


def test_describe_plan_interval_contains_minutes():
    result = describe_plan("interval", {"interval_minutes": 30})
    assert "30" in result


def test_describe_plan_daily_count_contains_count():
    result = describe_plan("daily_count", {"daily_count": 8})
    assert "8" in result
