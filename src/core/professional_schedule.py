"""Professional schedule configuration, parsing, and slot generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from src.utils import normalize_digits


PlanKind = Literal[
    "interval",
    "daily_count",
    "publishing_program",
    "campaign",
    "smart_queue",
    "timing_pattern",
    "multi_stage",
    "content_mix",
]

PERSIAN_WEEKDAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
WEEKDAY_TO_INDEX = {name: i for i, name in enumerate(PERSIAN_WEEKDAYS)}
CONTENT_TYPE_LABELS = {
    "text": "متن",
    "photo": "عکس",
    "video": "ویدیو",
    "voice": "ویس",
    "music": "موسیقی",
    "file": "فایل",
    "gif": "گیف",
}
LABEL_TO_CONTENT_TYPE = {
    "متن": "text",
    "عکس": "photo",
    "تصویر": "photo",
    "ویدیو": "video",
    "فیلم": "video",
    "ویس": "voice",
    "صوت": "voice",
    "موسیقی": "music",
    "آهنگ": "music",
    "فایل": "file",
    "گیف": "gif",
}
TEHRAN_OFFSET = timedelta(hours=3, minutes=30)


def parse_hhmm(value: str) -> time:
    raw = normalize_digits(value.strip())
    if ":" not in raw:
        raw = f"{int(raw):02d}:00"
    hour_s, minute_s = raw.split(":", 1)
    hour, minute = int(hour_s), int(minute_s)
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError("time must be between 00:00 and 23:59")
    return time(hour, minute)


def format_hhmm(value: str) -> str:
    parsed = parse_hhmm(value)
    return f"{parsed.hour:02d}:{parsed.minute:02d}"


def parse_jalali_date(value: str) -> date:
    year_s, month_s, day_s = normalize_digits(value).replace("-", "/").split("/")
    jy, jm, jd = int(year_s), int(month_s), int(day_s)
    try:
        import jdatetime

        return jdatetime.date(jy, jm, jd).togregorian()
    except Exception:
        return jalali_to_gregorian(jy, jm, jd)


def jalali_to_gregorian(jy: int, jm: int, jd: int) -> date:
    """Convert a Jalali date to Gregorian date.

    Uses the standard arithmetic conversion so runtime does not depend on an
    optional calendar package. Dates are valid for modern product usage.
    """
    jy -= 979
    jm -= 1
    jd -= 1
    j_day_no = 365 * jy + jy // 33 * 8 + (jy % 33 + 3) // 4
    for i in range(jm):
        j_day_no += 31 if i < 6 else 30
    j_day_no += jd

    g_day_no = j_day_no + 79
    gy = 1600 + 400 * (g_day_no // 146097)
    g_day_no %= 146097

    leap = True
    if g_day_no >= 36525:
        g_day_no -= 1
        gy += 100 * (g_day_no // 36524)
        g_day_no %= 36524
        if g_day_no >= 365:
            g_day_no += 1
        else:
            leap = False

    gy += 4 * (g_day_no // 1461)
    g_day_no %= 1461

    if g_day_no >= 366:
        leap = False
        g_day_no -= 1
        gy += g_day_no // 365
        g_day_no %= 365

    month_days = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 0
    while gm < 12 and g_day_no >= month_days[gm]:
        g_day_no -= month_days[gm]
        gm += 1
    return date(gy, gm + 1, g_day_no + 1)


def tehran_now_utc_naive(now_utc: Optional[datetime] = None) -> datetime:
    return now_utc or datetime.utcnow()


def utc_to_tehran(dt: datetime) -> datetime:
    return dt + TEHRAN_OFFSET


def tehran_to_utc(dt: datetime) -> datetime:
    return dt - TEHRAN_OFFSET


def persian_weekday_for_gregorian(day: date) -> str:
    # Python Monday=0. Tehran/Persian week Saturday=0.
    return PERSIAN_WEEKDAYS[(day.weekday() + 2) % 7]


def expand_weekday_range(start: str, end: str) -> List[str]:
    start_i, end_i = WEEKDAY_TO_INDEX[start], WEEKDAY_TO_INDEX[end]
    if start_i <= end_i:
        return PERSIAN_WEEKDAYS[start_i : end_i + 1]
    return PERSIAN_WEEKDAYS[start_i:] + PERSIAN_WEEKDAYS[: end_i + 1]


class BasePlanConfig(BaseModel):
    start_time: str = "09:00"
    end_time: str = "23:00"
    loop_mode: bool = False
    posts_per_run: int = Field(default=1, ge=1, le=20)

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        return format_hhmm(value)

    @model_validator(mode="after")
    def validate_window(self):
        if parse_hhmm(self.start_time) >= parse_hhmm(self.end_time):
            raise ValueError("start_time must be before end_time")
        return self


class CampaignPlanConfig(BasePlanConfig):
    start_date: str
    end_date: str
    active_weekdays: List[str] = Field(default_factory=lambda: PERSIAN_WEEKDAYS[:5])
    daily_count: int = Field(ge=1, le=96)

    @field_validator("active_weekdays")
    @classmethod
    def validate_weekdays(cls, values: List[str]) -> List[str]:
        invalid = [v for v in values if v not in WEEKDAY_TO_INDEX]
        if invalid:
            raise ValueError(f"invalid weekdays: {invalid}")
        return values

    @model_validator(mode="after")
    def validate_dates(self):
        if parse_jalali_date(self.start_date) > parse_jalali_date(self.end_date):
            raise ValueError("start_date must be before end_date")
        return self


class SmartQueuePlanConfig(BasePlanConfig):
    daily_count: int = Field(ge=1, le=96)
    strategy: Literal["fifo"] = "fifo"
    loop_mode: bool = True


class TimingPatternPlanConfig(BasePlanConfig):
    pattern: Literal["store", "humanized", "low_risk", "launch"] = "humanized"
    daily_count: int = Field(ge=1, le=96)
    jitter_minutes: int = Field(default=0, ge=0, le=30)


class StageConfig(BaseModel):
    days: int = Field(ge=1, le=365)
    daily_count: int = Field(ge=1, le=96)
    start_time: str = "09:00"
    end_time: str = "23:00"

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        return format_hhmm(value)


class MultiStagePlanConfig(BasePlanConfig):
    start_date: str
    stages: List[StageConfig] = Field(min_length=1, max_length=12)
    loop_mode: bool = False


class ContentMixPlanConfig(BasePlanConfig):
    quotas: Dict[str, int]
    loop_mode: bool = True

    @field_validator("quotas")
    @classmethod
    def validate_quotas(cls, values: Dict[str, int]) -> Dict[str, int]:
        allowed = set(CONTENT_TYPE_LABELS)
        invalid = [key for key in values if key not in allowed]
        if invalid:
            raise ValueError(f"invalid content types: {invalid}")
        if any(count < 1 or count > 96 for count in values.values()):
            raise ValueError("quota counts must be between 1 and 96")
        return values

    @property
    def daily_count(self) -> int:
        return sum(self.quotas.values())


class PublishingProgramConfig(BaseModel):
    """User-facing publishing program schedule.

    This is the humane wrapper around the internal schedule model. It supports
    the v1 publishing-program goals: recurring daily activity and dated campaigns,
    each with fixed intervals, daily counts, or exact times.
    """

    program_mode: Literal["recurring", "dated"] = "recurring"
    cadence: Literal["interval", "daily_count", "exact_times"]
    start_time: str = "09:00"
    end_time: str = "23:59"
    interval_minutes: Optional[int] = Field(default=None, ge=1, le=10080)
    daily_count: Optional[int] = Field(default=None, ge=1, le=96)
    times: List[str] = Field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    posts_per_run: int = Field(default=1, ge=1, le=20)
    loop_mode: bool = False

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_window_times(cls, value: str) -> str:
        return format_hhmm(value)

    @field_validator("times")
    @classmethod
    def validate_exact_times(cls, values: List[str]) -> List[str]:
        return [format_hhmm(value) for value in values]

    @model_validator(mode="after")
    def validate_program(self):
        if self.cadence in ("interval", "daily_count"):
            if parse_hhmm(self.start_time) >= parse_hhmm(self.end_time):
                raise ValueError("start_time must be before end_time")
        if self.cadence == "interval" and not self.interval_minutes:
            raise ValueError("interval_minutes is required for interval cadence")
        if self.cadence == "daily_count" and not self.daily_count:
            raise ValueError("daily_count is required for daily_count cadence")
        if self.cadence == "exact_times" and not self.times:
            raise ValueError("times is required for exact_times cadence")
        if self.program_mode == "dated":
            if not self.start_date or not self.end_date:
                raise ValueError("start_date and end_date are required for dated programs")
            if parse_jalali_date(self.start_date) > parse_jalali_date(self.end_date):
                raise ValueError("start_date must be before end_date")
        return self


@dataclass
class GeneratedSlot:
    utc_time: datetime
    tehran_time: datetime
    metadata: Dict[str, Any]


@dataclass
class ParsedPlan:
    plan_kind: str
    config: Dict[str, Any]


class PlanSlotGenerator:
    def __init__(self, now_utc: Optional[datetime] = None):
        self.now_utc = tehran_now_utc_naive(now_utc)

    def next_slots(self, plan_kind: str, config: Dict[str, Any], count: int = 5) -> List[GeneratedSlot]:
        if plan_kind == "publishing_program":
            return self._publishing_program_slots(PublishingProgramConfig(**config), count)
        if plan_kind == "campaign":
            cfg = CampaignPlanConfig(**config)
            return self._daily_slots(cfg.daily_count, cfg.start_time, cfg.end_time, count, cfg)
        if plan_kind == "smart_queue":
            cfg = SmartQueuePlanConfig(**config)
            return self._daily_slots(cfg.daily_count, cfg.start_time, cfg.end_time, count)
        if plan_kind == "timing_pattern":
            cfg = TimingPatternPlanConfig(**config)
            return self._daily_slots(
                cfg.daily_count, cfg.start_time, cfg.end_time, count, jitter_minutes=cfg.jitter_minutes
            )
        if plan_kind == "multi_stage":
            cfg = MultiStagePlanConfig(**config)
            stage, stage_index = self._current_stage(cfg)
            return self._daily_slots(
                stage.daily_count,
                stage.start_time,
                stage.end_time,
                count,
                metadata={"stage_index": stage_index},
            )
        if plan_kind == "content_mix":
            cfg = ContentMixPlanConfig(**config)
            types: List[str] = []
            for content_type, quota in cfg.quotas.items():
                types.extend([content_type] * quota)
            slots = self._daily_slots(cfg.daily_count, cfg.start_time, cfg.end_time, count)
            for index, slot in enumerate(slots):
                slot.metadata["message_type"] = types[index % len(types)]
            return slots
        return []

    def next_run(self, plan_kind: str, config: Dict[str, Any]) -> Optional[datetime]:
        slots = self.next_slots(plan_kind, config, count=1)
        return slots[0].utc_time if slots else None

    def _daily_slots(
        self,
        daily_count: int,
        start_time: str,
        end_time: str,
        count: int,
        campaign: Optional[CampaignPlanConfig] = None,
        jitter_minutes: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[GeneratedSlot]:
        now_teh = utc_to_tehran(self.now_utc)
        day = now_teh.date()
        slots: List[GeneratedSlot] = []

        while len(slots) < count:
            if campaign:
                start_date = parse_jalali_date(campaign.start_date)
                end_date = parse_jalali_date(campaign.end_date)
                if day < start_date:
                    day = start_date
                if day > end_date:
                    break
                if persian_weekday_for_gregorian(day) not in campaign.active_weekdays:
                    day += timedelta(days=1)
                    continue

            for slot_time in self._times_for_day(daily_count, start_time, end_time, jitter_minutes):
                slot_teh = datetime.combine(day, slot_time)
                if slot_teh <= now_teh:
                    continue
                slot_meta = dict(metadata or {})
                slots.append(
                    GeneratedSlot(
                        utc_time=tehran_to_utc(slot_teh),
                        tehran_time=slot_teh,
                        metadata=slot_meta,
                    )
                )
                if len(slots) >= count:
                    return slots
            day += timedelta(days=1)
        return slots

    def _times_for_day(self, daily_count: int, start_time: str, end_time: str, jitter_minutes: int) -> List[time]:
        start = parse_hhmm(start_time)
        end = parse_hhmm(end_time)
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        span = end_minutes - start_minutes
        step = span / max(daily_count, 1)
        result = []
        for index in range(daily_count):
            minute_of_day = int(start_minutes + index * step)
            if jitter_minutes:
                offset = jitter_minutes + int(jitter_minutes * 1.5) * index
                minute_of_day += min(offset, max(0, int(step) - 1))
            minute_of_day = min(minute_of_day, end_minutes)
            result.append(time(minute_of_day // 60, minute_of_day % 60))
        return result

    def _publishing_program_slots(self, config: PublishingProgramConfig, count: int) -> List[GeneratedSlot]:
        now_teh = utc_to_tehran(self.now_utc)
        day = now_teh.date()
        slots: List[GeneratedSlot] = []

        while len(slots) < count:
            if config.program_mode == "dated":
                start_date = parse_jalali_date(config.start_date or "")
                end_date = parse_jalali_date(config.end_date or "")
                if day < start_date:
                    day = start_date
                if day > end_date:
                    break

            for slot_time in self._publishing_times_for_day(config):
                slot_teh = datetime.combine(day, slot_time)
                if slot_teh <= now_teh:
                    continue
                slots.append(
                    GeneratedSlot(
                        utc_time=tehran_to_utc(slot_teh),
                        tehran_time=slot_teh,
                        metadata={"program_mode": config.program_mode, "cadence": config.cadence},
                    )
                )
                if len(slots) >= count:
                    return slots
            day += timedelta(days=1)
        return slots

    def _publishing_times_for_day(self, config: PublishingProgramConfig) -> List[time]:
        if config.cadence == "exact_times":
            return sorted(parse_hhmm(value) for value in config.times)
        if config.cadence == "daily_count":
            return self._times_for_day(config.daily_count or 1, config.start_time, config.end_time, 0)

        start = parse_hhmm(config.start_time)
        end = parse_hhmm(config.end_time)
        current = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        step = config.interval_minutes or 60
        result: List[time] = []
        while current <= end_minutes:
            result.append(time(current // 60, current % 60))
            current += step
        return result

    def _current_stage(self, config: MultiStagePlanConfig) -> tuple[StageConfig, int]:
        start = parse_jalali_date(config.start_date)
        today = utc_to_tehran(self.now_utc).date()
        elapsed_days = max(0, (today - start).days)
        cursor = 0
        for index, stage in enumerate(config.stages):
            cursor += stage.days
            if elapsed_days < cursor:
                return stage, index
        return config.stages[-1], len(config.stages) - 1


class PersianQuickPlanParser:
    def parse(self, text: str) -> ParsedPlan:
        normalized = normalize_digits(text.strip())
        if match := re.search(
            r"از\s+(\d{4}/\d{1,2}/\d{1,2})\s+تا\s+(\d{4}/\d{1,2}/\d{1,2})\s+روزی\s+(\d+)\s+پست\s+(\S+)\s+تا\s+(\S+)",
            normalized,
        ):
            start_day, end_day, count, weekday_start, weekday_end = match.groups()
            return ParsedPlan(
                "campaign",
                {
                    "start_date": start_day,
                    "end_date": end_day,
                    "daily_count": int(count),
                    "active_weekdays": expand_weekday_range(weekday_start, weekday_end),
                    "start_time": "09:00",
                    "end_time": "23:00",
                    "loop_mode": False,
                },
            )

        if match := re.search(r"روزی\s+(.+)\s+بین\s+(\d{1,2}(?::\d{2})?)\s+تا\s+(\d{1,2}(?::\d{2})?)", normalized):
            body, start_time, end_time = match.groups()
            quotas: Dict[str, int] = {}
            for count, label in re.findall(r"(\d+)\s+(\S+)", body):
                content_type = LABEL_TO_CONTENT_TYPE.get(label)
                if content_type:
                    quotas[content_type] = int(count)
            if quotas:
                return ParsedPlan(
                    "content_mix",
                    {
                        "quotas": quotas,
                        "start_time": format_hhmm(start_time),
                        "end_time": format_hhmm(end_time),
                        "loop_mode": True,
                    },
                )

            count_match = re.search(r"(\d+)\s+پست", body)
            if count_match:
                return ParsedPlan(
                    "smart_queue",
                    {
                        "daily_count": int(count_match.group(1)),
                        "start_time": format_hhmm(start_time),
                        "end_time": format_hhmm(end_time),
                        "loop_mode": "چرخشی" in normalized,
                    },
                )

        if match := re.search(r"(\d+)\s+روز\s+اول\s+روزی\s+(\d+)\s+پست\s+بعد\s+(\d+)\s+روز\s+روزی\s+(\d+)\s+پست", normalized):
            first_days, first_count, second_days, second_count = match.groups()
            return ParsedPlan(
                "multi_stage",
                {
                    "start_date": "1403/03/01",
                    "loop_mode": False,
                    "stages": [
                        {"days": int(first_days), "daily_count": int(first_count), "start_time": "09:00", "end_time": "23:00"},
                        {"days": int(second_days), "daily_count": int(second_count), "start_time": "10:00", "end_time": "22:00"},
                    ],
                },
            )

        raise ValueError("فرمت دستور سریع شناخته نشد.")


def describe_plan(plan_kind: str, config: Dict[str, Any]) -> str:
    if plan_kind == "publishing_program":
        cfg = PublishingProgramConfig(**config)
        prefix = "کمپین تاریخ‌دار" if cfg.program_mode == "dated" else "انتشار منظم روزانه"
        if cfg.cadence == "exact_times":
            return f"{prefix}: ساعت‌های دقیق {'، '.join(cfg.times)}"
        if cfg.cadence == "daily_count":
            return f"{prefix}: روزی {cfg.daily_count} پست از {cfg.start_time} تا {cfg.end_time}"
        return f"{prefix}: از {cfg.start_time} تا {cfg.end_time} هر {cfg.interval_minutes} دقیقه"
    if plan_kind == "campaign":
        cfg = CampaignPlanConfig(**config)
        weekdays = "، ".join(cfg.active_weekdays)
        return f"کمپین حرفه‌ای: روزی {cfg.daily_count} پست، {weekdays}، از {cfg.start_time} تا {cfg.end_time}"
    if plan_kind == "smart_queue":
        cfg = SmartQueuePlanConfig(**config)
        loop = "چرخشی" if cfg.loop_mode else "یک‌بار"
        return f"صف هوشمند {loop}: روزی {cfg.daily_count} پست از {cfg.start_time} تا {cfg.end_time}"
    if plan_kind == "timing_pattern":
        cfg = TimingPatternPlanConfig(**config)
        return f"الگوی زمانی {cfg.pattern}: روزی {cfg.daily_count} پست از {cfg.start_time} تا {cfg.end_time}"
    if plan_kind == "multi_stage":
        cfg = MultiStagePlanConfig(**config)
        counts = "، ".join(f"{stage.days} روز روزی {stage.daily_count}" for stage in cfg.stages)
        return f"پلن چندمرحله‌ای: {counts}"
    if plan_kind == "content_mix":
        cfg = ContentMixPlanConfig(**config)
        parts = [f"{count} {CONTENT_TYPE_LABELS[key]}" for key, count in cfg.quotas.items()]
        return f"ترکیب محتوا: روزی {cfg.daily_count} پست ({'، '.join(parts)})"
    if plan_kind == "interval":
        return f"ساده بازه‌ای: هر {config.get('interval_minutes', '?')} دقیقه"
    if plan_kind == "daily_count":
        return f"ساده روزانه: {config.get('daily_count', '?')} پیام/روز"
    return "پلن ناشناخته"
