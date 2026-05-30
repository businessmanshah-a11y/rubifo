from datetime import date, datetime, timezone, timedelta

TEHRAN_TZ = timezone(timedelta(hours=3, minutes=30))


def normalize_digits(value: str) -> str:
    """Convert Persian and Arabic-Indic digits to ASCII digits."""
    persian = "۰۱۲۳۴۵۶۷۸۹"
    arabic = "٠١٢٣٤٥٦٧٨٩"
    table = {ord(ch): str(i) for i, ch in enumerate(persian)}
    table.update({ord(ch): str(i) for i, ch in enumerate(arabic)})
    return value.translate(table)


def persian_digits(value: str) -> str:
    """Convert ASCII digits in display text to Persian digits."""
    table = {ord(str(i)): ch for i, ch in enumerate("۰۱۲۳۴۵۶۷۸۹")}
    return value.translate(table)


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


def _gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    g_days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    j_days_in_month = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]

    gy -= 1600
    gm -= 1
    gd -= 1

    g_day_no = 365 * gy + (gy + 3) // 4 - (gy + 99) // 100 + (gy + 399) // 400
    for i in range(gm):
        g_day_no += g_days_in_month[i]
    if gm > 1 and ((gy + 1600) % 4 == 0 and ((gy + 1600) % 100 != 0 or (gy + 1600) % 400 == 0)):
        g_day_no += 1
    g_day_no += gd

    j_day_no = g_day_no - 79
    j_np = j_day_no // 12053
    j_day_no %= 12053

    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)
    j_day_no %= 1461

    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365

    jm = 0
    while jm < 11 and j_day_no >= j_days_in_month[jm]:
        j_day_no -= j_days_in_month[jm]
        jm += 1

    return jy, jm + 1, j_day_no + 1


def _format_jalali(value: datetime, fmt: str) -> str:
    jy, jm, jd = _gregorian_to_jalali(value.year, value.month, value.day)
    replacements = {
        "%Y": f"{jy:04d}",
        "%m": f"{jm:02d}",
        "%d": f"{jd:02d}",
        "%H": f"{value.hour:02d}",
        "%M": f"{value.minute:02d}",
        "%S": f"{value.second:02d}",
    }
    rendered = fmt
    for token, replacement in replacements.items():
        rendered = rendered.replace(token, replacement)
    return persian_digits(rendered)


def to_jalali_date(value, fmt: str = "%Y/%m/%d") -> str:
    """Format a date or datetime with the Jalali calendar and Persian digits."""
    if value is None:
        return "—"
    try:
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, date):
            dt = datetime.combine(value, datetime.min.time())
        else:
            dt = datetime.fromisoformat(str(value))
        return _format_jalali(dt, fmt)
    except Exception:
        if hasattr(value, "strftime"):
            return persian_digits(value.strftime(fmt))
        return persian_digits(str(value))


def fmt_jalali_tehran(dt: datetime, fmt: str = "%Y/%m/%d %H:%M") -> str:
    """Format a naive UTC datetime as Jalali Tehran local time."""
    if dt is None:
        return "—"
    return to_jalali_date(to_tehran(dt), fmt)
