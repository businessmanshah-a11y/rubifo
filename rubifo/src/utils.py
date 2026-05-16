from datetime import datetime, timezone, timedelta

TEHRAN_TZ = timezone(timedelta(hours=3, minutes=30))


def now_tehran() -> datetime:
    """Current datetime in Iran timezone (UTC+3:30), timezone-naive for DB storage."""
    return datetime.now(TEHRAN_TZ).replace(tzinfo=None)


def to_tehran(dt: datetime) -> datetime:
    """Convert a naive UTC datetime to Iran timezone (for display)."""
    if dt is None:
        return dt
    return (dt.replace(tzinfo=timezone.utc) + timedelta(hours=3, minutes=30)).replace(tzinfo=None)


def fmt_tehran(dt: datetime, fmt: str = "%Y-%m-%d %H:%M") -> str:
    """Format a naive UTC datetime as Iran local time string."""
    if dt is None:
        return "—"
    return to_tehran(dt).strftime(fmt)
