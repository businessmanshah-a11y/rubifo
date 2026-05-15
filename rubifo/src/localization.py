"""Farsi localization messages for Rubifo."""

# Error messages
ERROR_MESSAGES = {
    "no_active_subscription": "❌ شما اشتراک فعالی ندارید.\n/buy برای خرید اشتراک بفرستید.",
    "route_limit_reached": "❌ شما حداکثر مسیرهای مجاز را ایجاد کرده‌اید.",
    "invalid_channel_id": "❌ شناسه کانال نامعتبر است.",
    "api_error": "❌ خطا در ارتباط با سرور. لطفا دوباره سعی کنید.",
    "payment_failed": "❌ پرداخت ناموفق. دوباره سعی کنید یا از پشتیبانی کمک بگیرید.",
    "route_not_found": "❌ مسیر یافت نشد.",
    "unauthorized": "❌ این مسیر/برنامه متعلق به شما نیست.",
    "invalid_input": "❌ ورودی نامعتبر است.",
    "timeout": "⏱️ مهلت انتظار تمام شد. لطفا دوباره سعی کنید.",
    "no_routes": "شما هیچ مسیری ندارید.\n/addroute برای اضافه کردن مسیر.",
    "no_schedules": "شما هیچ برنامه‌ریزی ندارید.\n/addplan برای اضافه کردن برنامه.",
    "no_logs": "هیچ فعالیتی برای نمایش وجود ندارد.",
}

# Success messages
SUCCESS_MESSAGES = {
    "route_created": "✅ مسیر ایجاد شد!",
    "route_removed": "✅ مسیر حذف شد.",
    "schedule_created": "✅ برنامه‌ریزی ایجاد شد!",
    "schedule_removed": "✅ برنامه‌ریزی حذف شد.",
    "payment_confirmed": "✅ پرداخت تأیید شد!",
    "subscription_active": "✅ اشتراک فعال است.",
}

# Help text
HELP_TEXT = """📚 دستورات Rubifo:

👤 **کاربری:**
/start - شروع و ثبت‌نام
/buy - خرید اشتراک
/renew - تمدید اشتراک

🗺️ **مسیرها:**
/addroute - ایجاد مسیر جدید
/listroutes - نمایش مسیرها
/removeroute [شناسه] - حذف مسیر
/updatesource [شناسه] - بروز‌رسانی صف
/sync [شناسه] - هماهنگ‌سازی صف

📅 **برنامه‌ریزی:**
/addplan - ایجاد برنامه
/listplans - نمایش برنامه‌ها
/editplan [شناسه] - ویرایش برنامه
/removeplan [شناسه] - حذف برنامه
/toggleplan [شناسه] - فعال/غیرفعال کردن

📊 **اطلاعات:**
/calendar - تقویم فعالیت‌ها
/logs - گزارش‌های اخیر
/help - این پیام"""

# Welcome message
WELCOME_TEXT = """🎉 **سلام! خوش آمدید به Rubifo**

Rubifo یک ربات هوشمند برای فوروارد خودکار پست‌ها در روبیکا است.

📌 **تریال شما:** 48 ساعت رایگان
💳 **بعد از تریال:** /buy برای خریدآپشن‌های تعدادی

🚀 **شروع سریع:**
1️⃣  /addroute - کانالی را انتخاب کنید
2️⃣  /addplan - برنامه‌ی فوروارد را تنظیم کنید
3️⃣  تمام پست‌ها خودکار منتقل می‌شوند!

📚 برای کمک: /help"""

# Pagination
PAGINATION_FORMAT = "[◀️ قبلی] [{page}/{total}] [بعدی ▶️]"
EMPTY_STATE = "هیچ موردی برای نمایش وجود ندارد."

# Confirmation
CONFIRM_DELETE = "🗑️ آیا مطمئنید؟\nبرای تأیید \"بله\" را بفرستید."
CONFIRMED = "✅ تأیید شد."
CANCELLED = "❌ لغو شد."

# Format helpers
def format_subscription_info(tier: str, end_date) -> str:
    """Format subscription information."""
    tier_names = {"basic": "📦 پایه", "pro": "⭐ حرفه‌ای", "enterprise": "👑 ویژه"}
    tier_name = tier_names.get(tier, tier)
    return f"{tier_name}\nتا تاریخ: {end_date}"


def format_route_info(route_id: int, source: int, target: int, is_active: bool, pending_count: int) -> str:
    """Format route information."""
    status = "✅ فعال" if is_active else "⛔ غیرفعال"
    return f"#{route_id}: {source} ← → {target}\n{status} | {pending_count} پست درانتظار"


def format_schedule_info(schedule_id: int, schedule_type: str, next_run, is_active: bool, params: dict = None) -> str:
    """Format schedule information."""
    status = "✅ فعال" if is_active else "⛔ غیرفعال"
    next_time = next_run.strftime("%H:%M") if next_run else "---"

    if schedule_type == "interval":
        type_info = f"⏱️ بازه‌ای ({params.get('interval_minutes', '?')} دقیقه)"
    else:
        type_info = f"📊 روزانه ({params.get('daily_count', '?')} پیام)"

    return f"#{schedule_id}: {type_info}\n{status} | بعدی: {next_time}"


def format_error_with_suggestion(error_code: str, suggestion: str = "") -> str:
    """Format error with helpful suggestion."""
    error_msg = ERROR_MESSAGES.get(error_code, "خطایی رخ داد.")
    if suggestion:
        return f"{error_msg}\n\n💡 {suggestion}"
    return error_msg
