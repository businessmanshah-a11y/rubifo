from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import asyncio
from src.logger import logger
from src.config import SUBSCRIPTION_TIERS, WEB_BASE_URL
from src.utils import fmt_jalali_tehran, normalize_digits, to_jalali_date
from src.integrations.zarinpal import create_zarinpal_gateway
from src.core.professional_schedule import (
    CampaignPlanConfig,
    ContentMixPlanConfig,
    MultiStagePlanConfig,
    PersianQuickPlanParser,
    SmartQueuePlanConfig,
    TimingPatternPlanConfig,
    describe_plan,
    expand_weekday_range,
    format_hhmm,
)

# In-memory storage for pending payments (authority -> {tier, amount, user_id})
pending_payments: Dict[str, Dict[str, Any]] = {}

# In-memory conversation states (user_id -> conversation_data)
conversation_states: Dict[str, Dict[str, Any]] = {}


def _make_inline_keypad(buttons: List[Tuple[str, str]], cols: int = 2):
    """Build a Keypad from (label, button_id) pairs, grouping into rows of `cols`."""
    from rubpy.bot.models import Keypad, KeypadRow, Button
    from rubpy.bot.enums import ButtonTypeEnum

    rows = []
    for i in range(0, len(buttons), cols):
        row_buttons = [
            Button(id=btn_id, type=ButtonTypeEnum.SIMPLE, button_text=label)
            for label, btn_id in buttons[i:i + cols]
        ]
        rows.append(KeypadRow(buttons=row_buttons))
    return Keypad(rows=rows)


def _format_price(amount: int) -> str:
    """Format toman prices for Farsi bot messages."""
    return f"{amount:,}"


def _tier_name(tier: str) -> str:
    return SUBSCRIPTION_TIERS.get(tier, {}).get("display_name_fa", tier)


def _tier_price(tier: str) -> int:
    return SUBSCRIPTION_TIERS.get(tier, {}).get("price_monthly", 0)


def _checkout_url(tier: Optional[str] = None) -> str:
    base = (WEB_BASE_URL or "https://rubifo.datayar.ir").rstrip("/")
    if "localhost" in base or "127.0.0.1" in base:
        base = "https://rubifo.datayar.ir"
    if tier:
        return f"{base}/checkout?tier={tier}"
    return f"{base}/checkout"


def _subscription_action_keypad(state: str):
    if state == "active":
        return _make_inline_keypad(
            [
                ("🔄 تمدید اشتراک", "/renew"),
                ("⬆️ ارتقا / تغییر پلن", "/buy"),
            ],
            cols=1,
        )
    return _make_inline_keypad(
        [
            ("📦 شروع حرفه‌ای", "/buy_basic"),
            ("⭐ رشد", "/buy_pro"),
            ("👑 مقیاس", "/buy_enterprise"),
        ],
        cols=1,
    )


def _plan_type_menu() -> str:
    return (
        "📅 نوع برنامه را انتخاب کنید:\n\n"
        "1️⃣ بازه‌ای — هر N دقیقه یک پیام\n"
        "2️⃣ روزانه ساده — فقط تعداد پست در روز\n\n"
        "3️⃣ کمپین حرفه‌ای — تاریخ، روزهای هفته، بازه ارسال\n"
        "4️⃣ صف هوشمند — ادامه خودکار و حالت چرخشی\n"
        "5️⃣ الگوی زمانی — انسانی/فروشگاهی/کم‌ریسک/لانچ\n"
        "6️⃣ چندمرحله‌ای — شدت ارسال متغیر در زمان\n"
        "7️⃣ ترکیب محتوا — سهمیه متن/عکس/ویدیو/فایل\n"
        "8️⃣ دستور سریع فارسی\n\n"
        "در تریال گزینه‌های 3 تا 8 قابل مشاهده‌اند اما بعد از خرید فعال می‌شوند.\n"
        "عدد 1 تا 8 را وارد کنید:"
    )


def _professional_plan_locked_message() -> str:
    return (
        "🔒 این پلن حرفه‌ای در تریال قفل است.\n\n"
        "در تریال می‌توانید هر N دقیقه یا N پست در روز بسازید؛ "
        "پلن‌های حرفه‌ای بعد از خرید فعال می‌شوند.\n\n"
        "Rubifo کار تکراری ادمین بارگذاری را حذف می‌کند. برای آزاد شدن همه امکانات، /buy را بفرستید."
    )


def _auto_daily_times(daily_count: int) -> List[Tuple[int, int]]:
    """Distribute simple daily plans between 09:00 and 23:00."""
    start_minutes = 9 * 60
    end_minutes = 23 * 60
    span = end_minutes - start_minutes
    times = []
    for index in range(daily_count):
        total_minutes = int(start_minutes + (span * index / daily_count))
        times.append((total_minutes // 60, total_minutes % 60))
    return times


async def _db_uid(pool, user_id) -> Optional[int]:
    """Return integer DB PK (users.id) for a Rubika user_id GUID."""
    row = await pool.fetchrow("SELECT id FROM users WHERE user_id = $1", user_id)
    return row["id"] if row else None


# ─────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────

async def handle_start(client, user_id: int, username: Optional[str] = None) -> None:
    logger.info(f"/start for user {user_id}")
    try:
        from src.database import pool
        from src.core.user_service import UserService

        user = await UserService(pool).get_or_create_user(user_id, username)

        if not user.phone_number or not user.password_hash or not user.onboarding_completed_at:
            conversation_states[user_id] = {"command": "web_onboarding_phone"}
            await client.send_message(
                user_id,
                "👋 خوش آمدید به Rubifo!\n\n"
                "برای اینکه بعداً خرید اشتراک در وب‌سایت به همین حساب روبیکا وصل شود، "
                "لطفاً شماره تماس خود را وارد کنید.\n\n"
                "فرمت شماره: 09123456789"
            )
            return

        subscription_status = None
        try:
            from src.core.subscription_service import SubscriptionService
            subscription_status = await SubscriptionService(pool).get_subscription_status(user_id)
        except Exception as e:
            logger.warning(f"Could not load subscription status for /start user {user_id}: {e}")

        def _sub_line(u, status=None) -> str:
            if status:
                if status.get("status") == "active":
                    return (
                        f"✅ پلن {_tier_name(status.get('tier'))} — "
                        f"{status.get('days_left', 0)} روز باقیمانده"
                    )
                if status.get("status") == "trial":
                    return f"⏳ تریال: {status.get('hours_left', 0):.0f} ساعت باقیمانده"
                if status.get("status") == "expired":
                    return "⚠️ تریال تمام شده — /buy برای اشتراک"

            if u.is_trial_active:
                hours_left = max(0, (u.trial_end_at - datetime.now()).total_seconds() / 3600)
                return f"⏳ تریال: {hours_left:.0f} ساعت باقیمانده"
            return "⚠️ تریال تمام شده — /buy برای اشتراک"

        msg = (
            "👋 خوش آمدید به Rubifo!\n\n"
            "Rubifo کمک می‌کند پست‌های کانالتان به‌صورت خودکار و طبق زمان‌بندی منتشر شوند.\n\n"
            "برای شروع، یک «برنامه انتشار» می‌سازید:\n"
            "1️⃣ کانال مقصد را معرفی می‌کنید و Rubifo را در آن کانال ادمین می‌کنید.\n"
            "2️⃣ پست‌های هم‌موضوع را داخل یک «دسته محتوا» می‌فرستید؛ مثل آموزشی، معرفی محصول یا رضایت مشتری.\n"
            "3️⃣ مشخص می‌کنید این دسته چه زمانی در کانال منتشر شود.\n\n"
            "اگر اولین‌بار است، می‌توانید قبل از برنامه واقعی یک آزمایش سه‌پستی انجام دهید.\n"
            f"{_sub_line(user, subscription_status)}\n\n"
            "برای شروع دکمه «➕ ایجاد برنامه جدید انتشار محتوا» را بزنید:"
        )
        keypad = _make_inline_keypad([("➕ ایجاد برنامه جدید انتشار محتوا", "➕ ساخت برنامه جدید")], cols=1)
        await client.send_message(user_id, msg, with_keypad=True, inline_keypad=keypad)
    except Exception as e:
        logger.error(f"/start error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


# ─────────────────────────────────────────────
# SOURCE MANAGEMENT
# ─────────────────────────────────────────────

async def handle_addsource(client, user_id: int) -> None:
    """Start creating a new source — ask for name."""
    logger.info(f"/addsource for user {user_id}")
    conversation_states[user_id] = {"command": "source_naming"}
    await client.send_message(
        user_id,
        "✏️ سورس جدید\n\n"
        "یک نام برای این سورس وارد کنید:\n"
        "(مثال: تبلیغات محصول الف، محتوای هفتگی)"
    )


async def handle_source_name_input(client, user_id: int, name: str) -> None:
    """Create source with given name and enter collecting mode."""
    name = name.strip()
    if not name or len(name) > 100:
        await client.send_message(user_id, "❌ نام باید بین ۱ تا ۱۰۰ کاراکتر باشد.")
        return

    try:
        from src.database import pool
        from src.core.source_service import SourceService
        db_id = await _db_uid(pool, user_id)
        if not db_id:
            await client.send_message(user_id, "ابتدا /start را بفرستید.")
            return
        source = await SourceService(pool).create_source(db_id, name)

        conversation_states[user_id] = {
            "command": "collecting_source",
            "source_id": source.id,
            "source_name": name,
            "post_count": 0,
        }
        await client.send_message(
            user_id,
            f"✅ سورس «{name}» ساخته شد!\n\n"
            f"📨 حالا پست‌هایی که می‌خواهید ذخیره شوند را ارسال کنید.\n"
            f"(عکس، ویدیو، ویس، موزیک، فایل، متن — همه قبول است)\n\n"
            f"نکته: اگر پست را به‌صورت فوروارد و با برچسب فرستنده بفرستید، "
            f"ممکن است همان برچسب در انتشار هم دیده شود. برای ارسال بدون برچسب، "
            f"در روبیکا گزینه پنهان کردن نام/فرستنده را بزنید یا محتوا را مستقیم و بدون فوروارد بفرستید.\n\n"
            f"وقتی تمام شد /savesource بفرستید."
        )
    except Exception as e:
        logger.error(f"source_name_input error: {e}")
        if user_id in conversation_states:
            del conversation_states[user_id]
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_source_collecting_message(client, user_id: int, message: Dict[str, Any]) -> None:
    """Store an incoming message as a source post during collecting mode.

    Media files are immediately re-uploaded via the bot's own upload endpoint so the stored
    file_id remains valid for future bot-to-channel sends.
    """
    state = conversation_states.get(user_id, {})
    source_id = state.get("source_id")
    if not source_id:
        return

    try:
        from src.database import pool
        from src.core.source_service import SourceService, _detect_message_type

        msg_type, text, file_id, caption, raw = _detect_message_type(message)

        # Re-upload media immediately so the file_id is bot-owned and never expires
        if file_id and msg_type != "text":
            try:
                file_id = await client.reupload_media(file_id, msg_type)
            except Exception as e:
                logger.warning(f"reupload_media failed for user {user_id}: {e} — media not stored")
                await client.send_message(
                    user_id,
                    "❌ آپلود فایل کامل نشد و این پست ذخیره نشد.\n"
                    "لطفاً همین پست را دوباره ارسال کنید تا فایل با شناسه معتبر بات ذخیره شود."
                )
                return

        post = await SourceService(pool).add_post(
            source_id, msg_type, text, file_id, caption, raw
        )

        state["post_count"] = state.get("post_count", 0) + 1
        count = state["post_count"]

        await client.send_message(
            user_id,
            f"✅ پست {count} ذخیره شد ({post.display_type})\n"
            f"ادامه دهید یا /savesource برای پایان."
        )
    except Exception as e:
        logger.error(f"collecting message error for user {user_id}: {e}")
        await client.send_message(user_id, "❌ خطا در ذخیره پست. دوباره ارسال کنید.")


async def handle_savesource(client, user_id: int) -> None:
    """Finish collecting and show source summary with connected flow."""
    state = conversation_states.pop(user_id, {})
    source_id = state.get("source_id")
    source_name = state.get("source_name", "")
    post_count = state.get("post_count", 0)

    if not source_id:
        await client.send_message(user_id, "❌ هیچ سورس فعالی برای ذخیره وجود ندارد.")
        return

    if post_count == 0:
        await client.send_message(
            user_id,
            f"✅ سورس «{source_name}» ساخته شد اما هنوز خالی است.\n\n"
            f"پست اضافه کنید:\n/addpost {source_id}",
            with_keypad=True,
        )
        return

    try:
        from src.database import pool
        from src.core.route_service import RouteService
        routes = await RouteService(pool).get_user_routes(user_id)

        if not routes:
            conversation_states[user_id] = {
                "command": "after_savesource",
                "source_id": source_id,
            }
            await client.send_message(
                user_id,
                f"✅ سورس «{source_name}» با {post_count} پست ذخیره شد!\n\n"
                f"➕ الان مسیر می‌سازیم تا ارسال شروع شود؟\n"
                f"«بله» یا /addroute",
                with_keypad=True,
            )
        else:
            await client.send_message(
                user_id,
                f"✅ سورس «{source_name}» با {post_count} پست ذخیره شد!\n\n"
                f"📦 /mysources — مشاهده همه سورس‌ها\n"
                f"➕ /addroute — اتصال به کانال جدید",
                with_keypad=True,
            )
    except Exception as e:
        logger.error(f"handle_savesource error: {e}")
        await client.send_message(
            user_id,
            f"✅ سورس «{source_name}» با {post_count} پست ذخیره شد!",
            with_keypad=True,
        )


async def handle_mysources(client, user_id: int) -> None:
    """List all content categories for user with inline action buttons."""
    logger.info(f"/mysources for user {user_id}")
    try:
        from src.database import pool
        from src.core.source_service import SourceService
        from src.core.route_service import RouteService
        db_id = await _db_uid(pool, user_id)
        ss = SourceService(pool)
        sources = await ss.get_user_sources(db_id) if db_id else []

        if not sources:
            await client.send_message(
                user_id,
                "📁 هنوز دسته محتوایی ندارید.\n\n"
                "برای ساخت دسته جدید، از «➕ ساخت برنامه جدید» شروع کنید "
                "یا هنگام ساخت برنامه، گزینه «ساخت دسته محتوای جدید» را بزنید.",
                with_keypad=True,
            )
            return

        msg = "📁 دسته‌های محتوای شما:\n\n"
        inline_buttons: List[Tuple[str, str]] = []

        for s in sources:
            count = await ss.count_posts(s.id)
            # Find connected routes for this source
            routes = await pool.fetch(
                "SELECT target_channel_id FROM routes WHERE source_id = $1 AND is_active = true",
                s.id,
            )
            connected = ", ".join(r["target_channel_id"] for r in routes) if routes else "—"
            msg += f"#{s.id} — {s.name}\n   📝 {count} پست | کانال‌ها: {connected}\n\n"
            inline_buttons.append((f"📝 #{s.id} پست‌ها", f"viewsource_{s.id}"))
            inline_buttons.append((f"➕ #{s.id} افزودن", f"addpost_{s.id}"))

        inline_buttons.append(("➕ ساخت برنامه جدید", "new_program"))
        keypad = _make_inline_keypad(inline_buttons, cols=2)
        await client.send_message(user_id, msg, inline_keypad=keypad)
    except Exception as e:
        logger.error(f"/mysources error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_viewsource(client, user_id: int, source_id: int) -> None:
    """Show posts in a source."""
    try:
        from src.database import pool
        from src.core.source_service import SourceService
        db_id = await _db_uid(pool, user_id)
        ss = SourceService(pool)
        source = await ss.get_source(source_id)

        if not source or source.user_id != db_id:
            await client.send_message(user_id, "❌ سورس یافت نشد.")
            return

        posts = await ss.get_posts(source_id)
        if not posts:
            await client.send_message(
                user_id,
                f"📦 سورس «{source.name}» خالی است.\n"
                f"/addpost {source_id} برای افزودن پست."
            )
            return

        msg = f"📦 سورس «{source.name}» — {len(posts)} پست:\n\n"
        for p in posts[:20]:
            valid = "" if p.file_id_valid else " ⚠️منقضی"
            msg += f"#{p.id} {p.display_type}{valid} — {p.short_preview[:35]}\n"

        if len(posts) > 20:
            msg += f"\n... و {len(posts) - 20} پست دیگر"

        msg += f"\n\n/removepost [شناسه‌پست] برای حذف"
        await client.send_message(user_id, msg)
    except Exception as e:
        logger.error(f"/viewsource error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_addpost(client, user_id: int, source_id: int) -> None:
    """Enter collecting mode for an existing source."""
    try:
        from src.database import pool
        from src.core.source_service import SourceService
        db_id = await _db_uid(pool, user_id)
        source = await SourceService(pool).get_source(source_id)

        if not source or source.user_id != db_id:
            await client.send_message(user_id, "❌ سورس یافت نشد.")
            return

        conversation_states[user_id] = {
            "command": "collecting_source",
            "source_id": source.id,
            "source_name": source.name,
            "post_count": 0,
        }
        await client.send_message(
            user_id,
            f"📨 افزودن پست به سورس «{source.name}»\n\n"
            f"پست‌های جدید را ارسال کنید.\n"
            f"برای پایان /savesource بفرستید."
        )
    except Exception as e:
        logger.error(f"/addpost error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_removepost(client, user_id: int, post_id: int) -> None:
    """Remove a single post from a source."""
    try:
        from src.database import pool
        from src.core.source_service import SourceService
        db_id = await _db_uid(pool, user_id)
        ss = SourceService(pool)
        post = await ss.get_post(post_id)

        if not post:
            await client.send_message(user_id, "❌ پست یافت نشد.")
            return

        source = await ss.get_source(post.source_id)
        if not source or source.user_id != db_id:
            await client.send_message(user_id, "❌ دسترسی مجاز نیست.")
            return

        await ss.remove_post(post_id)
        await client.send_message(user_id, f"✅ پست #{post_id} حذف شد.")
    except Exception as e:
        logger.error(f"/removepost error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_deletesource(client, user_id: int, source_id: int) -> None:
    """Ask confirmation before deleting a source."""
    try:
        from src.database import pool
        from src.core.source_service import SourceService
        db_id = await _db_uid(pool, user_id)
        source = await SourceService(pool).get_source(source_id)

        if not source or source.user_id != db_id:
            await client.send_message(user_id, "❌ سورس یافت نشد.")
            return

        conversation_states[user_id] = {
            "command": "deletesource",
            "source_id": source_id,
            "source_name": source.name,
        }
        await client.send_message(
            user_id,
            f"🗑️ حذف سورس «{source.name}»؟\n\n"
            f"تمام پست‌های این سورس و مسیرهای مرتبط حذف می‌شوند.\n\n"
            f"برای تأیید «بله» بفرستید."
        )
    except Exception as e:
        logger.error(f"/deletesource error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_deletesource_confirmation(client, user_id: int, text: str) -> None:
    state = conversation_states.pop(user_id, {})
    source_id = state.get("source_id")
    source_name = state.get("source_name", "")

    if text.strip().lower() not in ("بله", "yes", "y"):
        await client.send_message(user_id, "❌ حذف لغو شد.")
        return

    try:
        from src.database import pool
        from src.core.source_service import SourceService
        await SourceService(pool).delete_source(source_id)
        await client.send_message(
            user_id,
            f"✅ سورس «{source_name}» حذف شد.",
            with_keypad=True,
        )
    except Exception as e:
        logger.error(f"deletesource_confirmation error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


# ─────────────────────────────────────────────
# ROUTE MANAGEMENT (source-based)
# ─────────────────────────────────────────────

async def handle_addroute(client, user_id: int) -> None:
    """Start route creation — user picks a source, then a target channel."""
    logger.info(f"/addroute for user {user_id}")
    try:
        from src.database import pool
        from src.core.source_service import SourceService
        from src.core.user_service import UserService

        user = await UserService(pool).get_user(user_id)
        if not user:
            await client.send_message(user_id, "ابتدا /start را بفرستید.")
            return

        db_id = await _db_uid(pool, user_id)
        sources = await SourceService(pool).get_user_sources(db_id) if db_id else []
        if not sources:
            await client.send_message(
                user_id,
                "📦 ابتدا باید یک سورس بسازید.\n✏️ /addsource",
                with_keypad=True,
            )
            return

        source_map = {}
        msg = "➕ مسیر جدید\n\nکدام سورس را می‌خواهید به کانال وصل کنید؟\n\n"
        for i, s in enumerate(sources, 1):
            post_count = await SourceService(pool).count_posts(s.id)
            msg += f"{i}️⃣ #{s.id} — {s.name} ({post_count} پست)\n"
            source_map[str(i)] = s.id

        msg += "\nشماره سورس را وارد کنید:"
        await client.send_message(user_id, msg)

        conversation_states[user_id] = {
            "command": "addroute",
            "step": 1,
            "source_map": source_map,
        }
    except Exception as e:
        logger.error(f"/addroute error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_addroute_conversation(client, user_id: int, text: str) -> None:
    """Handle multi-step addroute conversation."""
    state = conversation_states.get(user_id, {})
    step = state.get("step", 1)

    try:
        from src.database import pool
        from src.core.route_service import RouteService
        from src.core.source_service import SourceService

        if step == 1:
            source_map = state.get("source_map", {})
            source_id = source_map.get(text.strip())
            if not source_id:
                await client.send_message(user_id, "❌ شماره نامعتبر. دوباره وارد کنید.")
                return

            source = await SourceService(pool).get_source(source_id)
            state["source_id"] = source_id
            state["source_name"] = source.name if source else str(source_id)

            # If a destination was pre-selected (from /my_destinations inline button), skip step 2
            preset_target = state.get("preset_target")
            if preset_target:
                state["step"] = 2
                # Immediately process as if user typed the target
                await handle_addroute_conversation(client, user_id, preset_target)
                return

            state["step"] = 2
            await client.send_message(
                user_id,
                f"✅ سورس «{state['source_name']}» انتخاب شد.\n\n"
                f"آیدی کانال مقصد را وارد کنید:\n"
                f"(ربات @Rubifo باید ادمین آن کانال باشد)\n\n"
                f"فرمت:\n"
                f"• @channel_username\n"
                f"• https://rubika.ir/channel_username"
            )

        elif step == 2:
            target = text.strip()
            if not target:
                await client.send_message(user_id, "❌ آیدی کانال نامعتبر است.")
                return

            # Normalize channel input
            if "rubika.ir/" in target:
                target = "@" + target.rstrip("/").split("rubika.ir/")[-1].strip()
            elif not target.startswith("@"):
                target = "@" + target.lstrip("@")

            can_create, error_msg = await RouteService(pool).can_create_route(user_id, target)
            if not can_create:
                await client.send_message(user_id, error_msg)
                return

            source_id = state["source_id"]
            source_name = state["source_name"]

            route_id = await RouteService(pool).create_route(user_id, source_id, target)
            conversation_states[user_id] = {
                "command": "after_addroute",
                "route_id": route_id,
            }

            await client.send_message(
                user_id,
                f"✅ مسیر #{route_id} ساخته شد!\n\n"
                f"📦 {source_name} → {target}\n\n"
                f"⚠️ مطمئن شوید ربات @Rubifo ادمین {target} است.\n\n"
                f"📅 الان زمان‌بندی ارسال تنظیم کنیم؟\n"
                f"«بله» یا /addplan",
                with_keypad=True,
            )

    except Exception as e:
        logger.error(f"addroute conversation error: {e}")
        conversation_states.pop(user_id, None)
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_listroutes(client, user_id: int) -> None:
    logger.info(f"/listroutes for user {user_id}")
    try:
        from src.database import pool
        from src.core.route_service import RouteService
        from src.core.source_service import SourceService

        routes = await RouteService(pool).get_user_routes(user_id)
        if not routes:
            await client.send_message(
                user_id,
                "شما هیچ مسیری ندارید.\n➕ /addroute برای ایجاد مسیر.",
                with_keypad=True,
            )
            return

        msg = "📋 مسیرهای شما\n\n"
        rs = RouteService(pool)
        ss = SourceService(pool)

        for route in routes:
            route_id = route["id"]
            source_id = route.get("source_id")
            target = route.get("target_channel_id", "؟")
            active_icon = "✅" if route["is_active"] else "⛔"

            source_name = "؟"
            if source_id:
                src = await ss.get_source(source_id)
                source_name = src.name if src else str(source_id)

            pending = await rs.get_route_queue_count(route_id, "pending")
            sent = await rs.get_route_queue_count(route_id, "sent")

            sched = await pool.fetchrow(
                "SELECT * FROM schedules WHERE route_id = $1 AND is_active = true LIMIT 1",
                route_id,
            )

            msg += f"{active_icon} #{route_id} — {source_name} → {target}\n"
            msg += f"   📤 {sent} ارسال | {pending} در صف\n"

            if sched:
                if sched["schedule_type"] == "interval":
                    msg += f"   ⏰ هر {sched['interval_minutes']} دقیقه\n"
                else:
                    msg += f"   ⏰ {sched['daily_count']} پیام/روز\n"
            else:
                msg += f"   ⚠️ بدون برنامه — /addplan\n"

            msg += "\n"

        msg += "/removeroute [شناسه] — حذف مسیر"
        await client.send_message(user_id, msg, with_keypad=True)
    except Exception as e:
        logger.error(f"/listroutes error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_removeroute(client, user_id: int, route_id: int) -> None:
    try:
        from src.database import pool
        from src.core.route_service import RouteService
        route = await RouteService(pool).get_route(route_id)

        if not route:
            await client.send_message(user_id, "❌ مسیر یافت نشد.")
            return
        if route["user_id"] != user_id:
            await client.send_message(user_id, "❌ این مسیر متعلق به شما نیست.")
            return

        conversation_states[user_id] = {"command": "removeroute", "route_id": route_id}
        await client.send_message(
            user_id,
            f"🗑️ حذف مسیر #{route_id}؟\n"
            f"مقصد: {route.get('target_channel_id', '?')}\n\n"
            f"برای تأیید «بله» بفرستید."
        )
    except Exception as e:
        logger.error(f"/removeroute error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_removeroute_confirmation(client, user_id: int, text: str) -> None:
    state = conversation_states.pop(user_id, {})
    route_id = state.get("route_id")

    if text.strip().lower() not in ("بله", "yes", "y"):
        await client.send_message(user_id, "❌ حذف لغو شد.")
        return

    try:
        from src.database import pool
        from src.core.route_service import RouteService
        await pool.execute("UPDATE post_queue SET status='removed' WHERE route_id=$1", route_id)
        await RouteService(pool).deactivate_route(route_id)
        await client.send_message(user_id, f"✅ مسیر #{route_id} حذف شد.", with_keypad=True)
    except Exception as e:
        logger.error(f"removeroute_confirmation error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


# ─────────────────────────────────────────────
# CONVERSATION ROUTER
# ─────────────────────────────────────────────

async def handle_conversation_response(client, user_id: int, text: str) -> None:
    """Route text responses for active multi-step conversations."""
    state = conversation_states.get(user_id, {})
    command = state.get("command")

    _yes = {"بله", "yes", "y", "آره", "اره", "ok", "اوکی"}

    if command == "source_naming":
        del conversation_states[user_id]
        await handle_source_name_input(client, user_id, text)
    elif command == "after_savesource":
        del conversation_states[user_id]
        if text.strip().lower() in _yes:
            await handle_addroute(client, user_id)
        else:
            await client.send_message(
                user_id, "باشه! هر وقت آماده شدید /addroute بفرستید.", with_keypad=True
            )
    elif command == "after_addroute":
        route_id = state.get("route_id")
        del conversation_states[user_id]
        if text.strip().lower() in _yes:
            await _start_addplan_for_route(client, user_id, route_id)
        else:
            await client.send_message(
                user_id, "باشه! هر وقت آماده شدید /addplan بفرستید.", with_keypad=True
            )
    elif command == "addroute":
        await handle_addroute_conversation(client, user_id, text)
    elif command == "deletesource":
        await handle_deletesource_confirmation(client, user_id, text)
    elif command == "removeroute":
        await handle_removeroute_confirmation(client, user_id, text)
    elif command == "removeplan":
        await handle_removeplan_confirmation(client, user_id, text)
    elif command == "addplan_route_select":
        await handle_addplan_route_selection(client, user_id, text)
    elif command == "addplan_type_select":
        await handle_addplan_type_selection(client, user_id, text)
    elif command == "addplan_interval":
        await handle_addplan_interval_input(client, user_id, text)
    elif command == "addplan_daily_count":
        await handle_addplan_daily_count_input(client, user_id, text)
    elif command == "addplan_professional_input":
        await handle_addplan_professional_input(client, user_id, text)
    elif command == "addplan_confirm":
        await handle_addplan_confirm(client, user_id, text)
    elif command == "web_onboarding_phone":
        await handle_web_onboarding_phone(client, user_id, text)
    elif command == "web_onboarding_password":
        await handle_web_onboarding_password(client, user_id, text)


async def handle_web_onboarding_phone(client, user_id: int, text: str) -> None:
    """Collect and validate the website login phone number."""
    try:
        from src.core.user_service import UserService

        phone_number = UserService.normalize_phone(text)
    except ValueError:
        conversation_states[user_id] = {"command": "web_onboarding_phone"}
        await client.send_message(
            user_id,
            "❌ شماره تماس معتبر نیست.\n"
            "لطفاً شماره موبایل را با فرمت 09xxxxxxxxx وارد کنید."
        )
        return

    conversation_states[user_id] = {
        "command": "web_onboarding_password",
        "phone_number": phone_number,
    }
    await client.send_message(
        user_id,
        "✅ شماره تماس ثبت شد.\n\n"
        "حالا یک رمز عبور ثابت برای ورود به وب‌سایت انتخاب کنید.\n"
        "رمز باید حداقل ۶ کاراکتر باشد."
    )


async def handle_web_onboarding_password(client, user_id: int, text: str) -> None:
    """Store website login credentials and finish onboarding."""
    password = (text or "").strip()
    if len(password) < 6:
        await client.send_message(
            user_id,
            "❌ رمز عبور کوتاه است. لطفاً رمزی با حداقل ۶ کاراکتر وارد کنید."
        )
        return

    state = conversation_states.get(user_id, {})
    phone_number = state.get("phone_number")
    if not phone_number:
        conversation_states[user_id] = {"command": "web_onboarding_phone"}
        await client.send_message(user_id, "لطفاً ابتدا شماره تماس را وارد کنید.")
        return

    try:
        from src.database import pool
        from src.core.user_service import UserService

        await UserService(pool).set_web_credentials(user_id, phone_number, password)
        conversation_states.pop(user_id, None)
        await client.send_message(
            user_id,
            "✅ شماره تماس و رمز ورود وب‌سایت ثبت شد.\n\n"
            "از این به بعد برای خرید یا تمدید اشتراک، /buy را بفرستید."
        )
    except Exception as e:
        logger.error(f"web onboarding password error for user {user_id}: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


# ─────────────────────────────────────────────
# DESTINATION CHANNELS
# ─────────────────────────────────────────────

async def handle_my_destinations(client, user_id: int) -> None:
    """Show verified destination channels in publishing-program language."""
    logger.info(f"/my_destinations for user {user_id}")
    try:
        from src.database import pool
        from src.core.destination_service import DestinationService
        from src.core.subscription_service import SubscriptionService

        destinations = await DestinationService(pool).list_verified(user_id)
        dest_limit = await SubscriptionService(pool).get_destination_limit(user_id)
        dest_used = len(destinations)

        if not destinations:
            await client.send_message(
                user_id,
                "📍 هیچ کانال مقصدی ندارید.\n\n"
                "برای افزودن کانال، از «➕ ساخت برنامه جدید» شروع کنید. "
                "در همان مسیر، Rubifo مرحله‌به‌مرحله به شما می‌گوید چطور ربات را ادمین کنید.",
                with_keypad=True,
            )
            return

        msg = f"📍 کانال‌های مقصد شما ({dest_used}/{dest_limit})\n\n"
        inline_buttons: List[Tuple[str, str]] = []

        for dest in destinations:
            ch = dest.channel_id
            stats = await pool.fetchrow(
                """
                SELECT
                  COUNT(s.id) FILTER (WHERE s.program_purpose = 'real') AS program_count,
                  COUNT(s.id) FILTER (
                    WHERE s.program_purpose = 'real' AND s.is_active = true
                  ) AS active_program_count,
                  COUNT(s.id) FILTER (
                    WHERE s.program_purpose = 'real' AND s.paused_reason = 'در انتظار محتوا'
                  ) AS waiting_program_count
                FROM routes r
                LEFT JOIN schedules s ON s.route_id = r.id
                WHERE r.user_id = $1 AND r.destination_id = $2 AND r.is_active = true
                """,
                user_id,
                dest.id,
            )
            msg += (
                f"📍 {ch}\n"
                f"   ✅ دسترسی انتشار تایید شده\n"
                f"   📅 {stats['program_count'] or 0} برنامه انتشار | "
                f"{stats['active_program_count'] or 0} فعال | "
                f"{stats['waiting_program_count'] or 0} در انتظار محتوا\n\n"
            )
            inline_buttons.extend([
                (f"📅 برنامه‌ها ({ch})", f"dst_plans_{ch}"),
                (f"📊 تقویم ({ch})", f"dst_cal_{ch}"),
                (f"➕ برنامه جدید ({ch})", "new_program"),
            ])

        if dest_used < dest_limit:
            msg += f"➕ می‌توانید {dest_limit - dest_used} کانال دیگر اضافه کنید؛ از «➕ ساخت برنامه جدید» شروع کنید."

        keypad = _make_inline_keypad(inline_buttons, cols=2)
        await client.send_message(user_id, msg, inline_keypad=keypad)
    except Exception as e:
        logger.error(f"/my_destinations error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_destination_routes(client, user_id: int, target_channel_id: str) -> None:
    """List routes going to a specific destination channel."""
    try:
        from src.database import pool
        from src.core.route_service import RouteService
        from src.core.source_service import SourceService

        routes = await pool.fetch(
            "SELECT * FROM routes WHERE user_id = $1 AND target_channel_id = $2 AND is_active = true ORDER BY id",
            user_id, target_channel_id,
        )
        if not routes:
            await client.send_message(
                user_id,
                f"📋 هیچ مسیری برای {target_channel_id} وجود ندارد.\n"
                f"➕ /addroute برای ساخت مسیر جدید.",
                with_keypad=True,
            )
            return

        msg = f"📋 مسیرهای {target_channel_id}:\n\n"
        rs = RouteService(pool)
        ss = SourceService(pool)
        for r in routes:
            src = await ss.get_source(r["source_id"])
            src_name = src.name if src else str(r["source_id"])
            pending = await rs.get_route_queue_count(r["id"], "pending")
            sent = await rs.get_route_queue_count(r["id"], "sent")
            msg += f"#{r['id']} — {src_name}\n   📤 {sent} ارسال | {pending} در صف\n   /removeplan — /listplans\n\n"

        await client.send_message(user_id, msg, with_keypad=True)
    except Exception as e:
        logger.error(f"handle_destination_routes error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_destination_plans(client, user_id: int, target_channel_id: str) -> None:
    """List publishing programs for a destination channel."""
    try:
        from src.database import pool
        from src.core.professional_schedule import describe_plan

        plans = await pool.fetch(
            """
            SELECT s.*, src.name AS source_name
            FROM schedules s
            JOIN routes r ON s.route_id = r.id
            LEFT JOIN sources src ON r.source_id = src.id
            WHERE r.user_id = $1 AND r.target_channel_id = $2
              AND r.is_active = true AND s.program_purpose = 'real'
            ORDER BY s.created_at DESC
            """,
            user_id, target_channel_id,
        )

        if not plans:
            await client.send_message(
                user_id,
                f"📅 هنوز برنامه انتشاری برای {target_channel_id} ندارید.\n"
                "برای ساخت، «➕ ساخت برنامه جدید» را بزنید.",
                with_keypad=True,
            )
            return

        msg = f"📅 برنامه‌های {target_channel_id}:\n\n"
        for p in plans:
            active_icon = "✅" if p["is_active"] else "⏳"
            pk = p.get("plan_kind") or p["schedule_type"]
            import json
            cfg = p["config"] if isinstance(p["config"], dict) else json.loads(p["config"] or "{}")
            type_info = describe_plan(pk, cfg)
            next_run = fmt_jalali_tehran(p["next_run"], "%m/%d %H:%M") if p["next_run"] else "—"
            paused = f"\n   وضعیت: {p['paused_reason']}" if p.get("paused_reason") else ""
            msg += (
                f"{active_icon} {p['source_name'] or 'دسته محتوا'}\n"
                f"   {type_info}\n"
                f"   اجرای بعدی: {next_run}{paused}\n\n"
            )

        msg += "برای ساخت برنامه تازه، «➕ ساخت برنامه جدید» را بزنید."
        await client.send_message(user_id, msg, with_keypad=True)
    except Exception as e:
        logger.error(f"handle_destination_plans error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_addroute_for_channel(client, user_id: int, target_channel_id: str) -> None:
    """Start addroute flow pre-filled with a specific destination channel."""
    logger.info(f"/addroute for {target_channel_id} by user {user_id}")
    try:
        from src.database import pool
        from src.core.source_service import SourceService

        db_id = await _db_uid(pool, user_id)
        sources = await SourceService(pool).get_user_sources(db_id) if db_id else []
        if not sources:
            await client.send_message(
                user_id,
                "📦 ابتدا باید یک سورس بسازید.\n✏️ /addsource",
                with_keypad=True,
            )
            return

        source_map = {}
        msg = f"➕ مسیر جدید به {target_channel_id}\n\nکدام سورس را می‌خواهید وصل کنید؟\n\n"
        for i, s in enumerate(sources, 1):
            post_count = await SourceService(pool).count_posts(s.id)
            msg += f"{i}️⃣ #{s.id} — {s.name} ({post_count} پست)\n"
            source_map[str(i)] = s.id

        msg += "\nشماره سورس را وارد کنید:"
        await client.send_message(user_id, msg)

        conversation_states[user_id] = {
            "command": "addroute",
            "step": 1,
            "source_map": source_map,
            "preset_target": target_channel_id,
        }
    except Exception as e:
        logger.error(f"handle_addroute_for_channel error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_calendar_display(client, user_id: int, target_channel_id: str) -> None:
    """Show scheduled publishing calendar for a destination channel (7 days)."""
    logger.info(f"/calendar display for {target_channel_id} by user {user_id}")
    try:
        from src.database import pool
        import json

        routes = await pool.fetch(
            "SELECT id FROM routes WHERE user_id = $1 AND target_channel_id = $2 AND is_active = true",
            user_id, target_channel_id,
        )
        if not routes:
            await client.send_message(
                user_id,
                f"📊 هنوز برنامه انتشاری برای {target_channel_id} ساخته نشده.\n"
                "برای شروع، «➕ ساخت برنامه جدید» را بزنید.",
                with_keypad=True,
            )
            return

        route_ids = [r["id"] for r in routes]
        plans = await pool.fetch(
            """
            SELECT s.id, s.route_id, s.schedule_type, s.plan_kind, s.config,
                   s.interval_minutes, s.daily_count, s.next_run, s.is_active,
                   s.paused_reason, s.program_purpose,
                   src.name AS source_name
            FROM schedules s
            JOIN routes r ON s.route_id = r.id
            LEFT JOIN sources src ON r.source_id = src.id
            WHERE s.route_id = ANY($1) AND s.program_purpose = 'real'
            ORDER BY s.next_run NULLS LAST
            """,
            route_ids,
        )

        pending_posts = await pool.fetchval(
            """
            SELECT COUNT(*) FROM post_queue pq
            WHERE pq.route_id = ANY($1) AND pq.status = 'pending'
            """,
            route_ids,
        )

        if not plans:
            await client.send_message(
                user_id,
                f"📊 تقویم {target_channel_id}\n\n"
                f"هیچ برنامه انتشاری ثبت نشده.\n"
                f"⏳ {pending_posts or 0} پست در صف\n\n"
                f"برای ساخت، «➕ ساخت برنامه جدید» را بزنید.",
                with_keypad=True,
            )
            return

        now = datetime.now()
        week_end = now + timedelta(days=7)

        msg = f"📊 تقویم {target_channel_id}\n⏳ {pending_posts or 0} پست در صف\n\n"

        # Group scheduled runs by day
        day_slots: Dict[str, List[str]] = {}
        for p in plans:
            if not p["is_active"]:
                continue
            next_run = p["next_run"]
            if not next_run or next_run > week_end:
                continue
            day_key = fmt_jalali_tehran(next_run, "%Y/%m/%d")
            time_str = fmt_jalali_tehran(next_run, "%H:%M")
            src = p["source_name"] or "دسته محتوا"
            pk = p["plan_kind"] or p["schedule_type"]
            cfg = p["config"] if isinstance(p["config"], dict) else json.loads(p["config"] or "{}")
            type_info = describe_plan(pk, cfg) if pk == "publishing_program" else pk
            slot = f"  {time_str} — {src} ({type_info})"
            day_slots.setdefault(day_key, []).append(slot)

        if day_slots:
            for day, slots in sorted(day_slots.items()):
                msg += f"📅 {day}:\n" + "\n".join(slots) + "\n\n"
        else:
            msg += "هیچ ارسالی در ۷ روز آینده برنامه‌ریزی نشده.\n\n"

        # Show all active schedules summary
        msg += "برنامه‌های انتشار:\n"
        for p in plans:
            src = p["source_name"] or "دسته محتوا"
            pk = p["plan_kind"] or p["schedule_type"]
            cfg = p["config"] if isinstance(p["config"], dict) else json.loads(p["config"] or "{}")
            type_info = describe_plan(pk, cfg) if pk == "publishing_program" else pk
            state = "فعال" if p["is_active"] else (p["paused_reason"] or "غیرفعال")
            msg += f"• {src}: {type_info} — {state}\n"

        inline_buttons = [
            (f"📅 برنامه‌ها ({target_channel_id})", f"dst_plans_{target_channel_id}"),
            ("➕ ساخت برنامه جدید", "new_program"),
        ]
        keypad = _make_inline_keypad(inline_buttons, cols=2)
        await client.send_message(user_id, msg, inline_keypad=keypad)
    except Exception as e:
        logger.error(f"handle_calendar_display error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


# ─────────────────────────────────────────────
# PAYMENT
# ─────────────────────────────────────────────

async def handle_subscription_status(client, user_id: int) -> None:
    """Show subscription status, days left, channel usage, and renew/upgrade options."""
    logger.info(f"/subscription_status for user {user_id}")
    try:
        from src.database import pool
        from src.core.subscription_service import SubscriptionService

        status = await SubscriptionService(pool).get_subscription_status(user_id)
        state = status["status"]

        if state == "trial":
            hours_left = status["hours_left"]
            dest_used = status["destinations_used"]
            dest_limit = status["destinations_limit"]
            msg = (
                "💳 وضعیت اشتراک شما\n\n"
                f"⏳ تریال: {hours_left:.0f} ساعت باقیمانده\n\n"
                f"کانال‌های مقصد: {dest_used}/{dest_limit}\n\n"
                "برای ادامه فعالیت بعد از تریال یکی از پلن‌های زیر را انتخاب کنید:\n"
                f"📦 شروع حرفه‌ای — {_format_price(_tier_price('basic'))} تومان/ماه (1 کانال)\n"
                f"⭐ رشد — {_format_price(_tier_price('pro'))} تومان/ماه (3 کانال)\n"
                f"👑 مقیاس — {_format_price(_tier_price('enterprise'))} تومان/ماه (10 کانال)"
            )
        elif state == "active":
            tier = status["tier"]
            tier_fa = _tier_name(tier)
            days_left = status["days_left"]
            dest_used = status["destinations_used"]
            dest_limit = status["destinations_limit"]
            end_date = to_jalali_date(status["end_date"])

            slots_remaining = dest_limit - dest_used
            slots_msg = (
                f"✅ {slots_remaining} کانال دیگر می‌توانی اضافه کنی"
                if slots_remaining > 0
                else "⛔ به حد کانال مقصد رسیدید"
            )

            msg = (
                f"💳 وضعیت اشتراک\n\n"
                f"✅ پلن {tier_fa}\n"
                f"تاریخ پایان: {end_date}\n"
                f"⏳ {days_left} روز باقیمانده\n\n"
                f"کانال‌های مقصد: {dest_used}/{dest_limit}\n"
                f"{slots_msg}\n\n"
                "برای تمدید یا تغییر پلن از دکمه‌های زیر استفاده کنید."
            )
        else:  # expired
            msg = (
                "⚠️ اشتراک منقضی‌شده\n\n"
                "تریال و اشتراک فعالی ندارید.\n"
                "تمام پلن‌ها غیرفعال شده‌اند.\n\n"
                "برای فعال‌سازی دوباره یکی از پلن‌های زیر را انتخاب کنید:\n"
                f"📦 شروع حرفه‌ای — {_format_price(_tier_price('basic'))} تومان/ماه (1 کانال)\n"
                f"⭐ رشد — {_format_price(_tier_price('pro'))} تومان/ماه (3 کانال)\n"
                f"👑 مقیاس — {_format_price(_tier_price('enterprise'))} تومان/ماه (10 کانال)"
            )

        await client.send_message(
            user_id,
            msg,
            with_keypad=True,
            inline_keypad=_subscription_action_keypad(state),
        )
    except Exception as e:
        logger.error(f"/subscription_status error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_buy(client, user_id: int) -> None:
    logger.info(f"/buy for user {user_id}")
    try:
        from src.database import pool
        from src.core.subscription_service import SubscriptionService
        active_sub = await SubscriptionService(pool).get_active_subscription(user_id)
        if active_sub:
            tier_fa = _tier_name(active_sub.tier)
            await client.send_message(
                user_id,
                f"شما اشتراک {tier_fa} دارید.\n"
                f"تاریخ پایان: {to_jalali_date(active_sub.end_date)}\n\n"
                "برای تمدید یا تغییر پلن از دکمه‌های زیر استفاده کنید.",
                inline_keypad=_subscription_action_keypad("active"),
            )
            return

        await client.send_message(
            user_id,
            "💳 اشتراک‌های Rubifo\n\n"
            "خرید و تمدید اشتراک از وب‌سایت انجام می‌شود تا پرداخت، رسید و فعال‌سازی "
            "روی همین حساب روبیکا ثبت شود.\n\n"
            f"لینک خرید:\n{_checkout_url()}\n\n"
            f"📦 شروع حرفه‌ای: {_format_price(_tier_price('basic'))} تومان/ماه\n"
            f"⭐ رشد: {_format_price(_tier_price('pro'))} تومان/ماه\n"
            f"👑 مقیاس: {_format_price(_tier_price('enterprise'))} تومان/ماه"
        )
    except Exception as e:
        logger.error(f"/buy error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_buy_tier(client, user_id: int, tier: str) -> None:
    logger.info(f"/buy_{tier} for user {user_id}")
    if tier not in SUBSCRIPTION_TIERS:
        await client.send_message(user_id, "سطح اشتراک نامعتبر است.")
        return
    amount = SUBSCRIPTION_TIERS[tier]["price_monthly"]
    tier_fa = _tier_name(tier)
    await client.send_message(
        user_id,
        f"برای خرید پلن {tier_fa} ({_format_price(amount)} تومان)، وارد وب‌سایت شوید:\n"
        f"{_checkout_url(tier)}"
    )


async def verify_payment_polling(client, subscription_service, authority: str, amount: int) -> None:
    MAX_ATTEMPTS = 30
    for attempt in range(MAX_ATTEMPTS):
        try:
            if authority not in pending_payments:
                break
            data = pending_payments[authority]
            user_id, tier = data["user_id"], data["tier"]
            gateway = create_zarinpal_gateway(sandbox=True)
            success, ref_id = await gateway.verify_payment(authority, amount)
            if success:
                from src.database import pool
                from src.core.transaction_service import TransactionService
                sub = await subscription_service.create_subscription(user_id, tier, days=30)
                await TransactionService(pool).insert_transaction(user_id, amount, tier, "completed", ref_id)
                del pending_payments[authority]
                await client.send_message(
                    user_id,
                    f"✅ پرداخت تأیید شد!\n\n"
                    f"اشتراک {_tier_name(tier)} فعال شد.\n"
                    "همه امکانات Rubifo برای شما باز است؛ محدودیت فقط تعداد کانال مقصد پلن شماست.\n"
                    f"تاریخ پایان: {to_jalali_date(sub.end_date)}"
                )
                return
            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"payment polling error {authority}: {e}")
            await asyncio.sleep(10)

    if authority in pending_payments:
        uid = pending_payments.pop(authority)["user_id"]
        await client.send_message(uid, "⏱ مهلت پرداخت تمام شد. /buy را دوباره بفرستید.")


async def handle_buy_basic(client, user_id: int) -> None:
    await handle_buy_tier(client, user_id, "basic")


async def handle_buy_pro(client, user_id: int) -> None:
    await handle_buy_tier(client, user_id, "pro")


async def handle_buy_enterprise(client, user_id: int) -> None:
    await handle_buy_tier(client, user_id, "enterprise")


async def handle_renew(client, user_id: int) -> None:
    logger.info(f"/renew for user {user_id}")
    try:
        from src.database import pool
        from src.core.subscription_service import SubscriptionService
        sub = await SubscriptionService(pool).get_active_subscription(user_id)
        if not sub:
            await client.send_message(user_id, "اشتراک فعالی ندارید.\n/buy برای خرید.")
            return

        tier = sub.tier
        amount = SUBSCRIPTION_TIERS.get(tier, {}).get("price_monthly", 0)
        tier_fa = _tier_name(tier)
        await client.send_message(
            user_id,
            f"تمدید پلن {tier_fa} ({_format_price(amount)} تومان) از وب‌سایت انجام می‌شود:\n"
            f"{_checkout_url(tier)}"
        )
    except Exception as e:
        logger.error(f"/renew error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def verify_renewal_payment_polling(client, subscription_service, authority: str, amount: int) -> None:
    MAX_ATTEMPTS = 30
    for attempt in range(MAX_ATTEMPTS):
        try:
            if authority not in pending_payments:
                break
            data = pending_payments[authority]
            user_id, tier = data["user_id"], data["tier"]
            gateway = create_zarinpal_gateway(sandbox=True)
            success, ref_id = await gateway.verify_payment(authority, amount)
            if success:
                from src.database import pool
                from src.core.transaction_service import TransactionService
                sub = await subscription_service.extend_subscription(user_id, days=30)
                await TransactionService(pool).insert_transaction(user_id, amount, tier, "completed", ref_id)
                del pending_payments[authority]
                await client.send_message(
                    user_id,
                    f"✅ تمدید پلن {_tier_name(tier)} انجام شد!\n"
                    f"تاریخ پایان جدید: {to_jalali_date(sub.end_date)}"
                )
                return
            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"renewal polling error {authority}: {e}")
            await asyncio.sleep(10)

    if authority in pending_payments:
        uid = pending_payments.pop(authority)["user_id"]
        await client.send_message(uid, "⏱ مهلت پرداخت تمام شد. /renew را دوباره بفرستید.")


# ─────────────────────────────────────────────
# HELP & LOGS
# ─────────────────────────────────────────────

async def handle_help(client, user_id: int) -> None:
    logger.info(f"/help for user {user_id}")
    msg = (
        "📖 راهنمای Rubifo\n\n"
        "Rubifo پست‌های کانالتان را طبق برنامه‌ای که می‌سازید خودکار منتشر می‌کند "
        "و برای حذف ادمین بارگذاری از کارهای تکراری و آپلود دستی ساخته شده است.\n\n"
        "مفهوم‌ها:\n"
        "📍 کانال مقصد: کانالی که Rubifo در آن پست منتشر می‌کند. باید Rubifo را در آن ادمین کنید.\n"
        "📁 دسته محتوا: پست‌های هم‌موضوع؛ مثل آموزشی، معرفی محصول یا رضایت مشتری.\n"
        "📅 برنامه انتشار: مشخص می‌کند کدام دسته محتوا در کدام کانال و چه زمانی منتشر شود.\n\n"
        "برای شروع، دکمه «➕ ساخت برنامه جدید» را بزنید. "
        "در مسیر ساخت برنامه می‌توانید برنامه آزمایشی سه‌پستی یا برنامه واقعی بسازید.\n\n"
        "دکمه‌های اصلی و دستورهای ساده:\n"
        "➕ ساخت برنامه جدید — شروع ساخت برنامه انتشار\n"
        "📅 برنامه‌های انتشار — دیدن و مدیریت برنامه‌ها\n"
        "📊 تقویم انتشار — دیدن ارسال‌های آینده هر کانال\n"
        "📁 دسته‌های محتوا — مدیریت پست‌های ذخیره‌شده\n"
        "📍 کانال‌های من — بررسی کانال‌های تاییدشده\n"
        "💳 اشتراک — وضعیت تریال یا خرید"
    )
    await client.send_message(user_id, msg, with_keypad=True)


async def handle_logs(client, user_id: int) -> None:
    logger.info(f"/logs for user {user_id}")
    try:
        from src.database import pool

        stats = await pool.fetchrow(
            """
            SELECT
                COUNT(*) FILTER (WHERE pq.status = 'sent') AS total_sent,
                COUNT(*) FILTER (WHERE pq.status = 'failed') AS total_failed,
                COUNT(*) FILTER (WHERE pq.status = 'pending') AS total_pending,
                COUNT(*) FILTER (
                    WHERE pq.status = 'sent' AND pq.created_at >= CURRENT_DATE
                ) AS today_sent,
                COUNT(*) FILTER (
                    WHERE pq.status = 'failed' AND pq.created_at >= CURRENT_DATE
                ) AS today_failed
            FROM post_queue pq
            JOIN routes r ON pq.route_id = r.id
            WHERE r.user_id = $1
            """,
            user_id,
        )

        logs = await pool.fetch(
            """
            SELECT pq.id, pq.status, pq.created_at, pq.last_error,
                   r.target_channel_id, s.name as source_name
            FROM post_queue pq
            JOIN routes r ON pq.route_id = r.id
            LEFT JOIN sources s ON r.source_id = s.id
            WHERE r.user_id = $1
            ORDER BY pq.created_at DESC
            LIMIT 15
            """,
            user_id,
        )

        if not stats or stats["total_sent"] == 0 and stats["total_failed"] == 0 and stats["total_pending"] == 0:
            await client.send_message(
                user_id,
                "📊 هنوز فعالیتی ثبت نشده.\n\n"
                "برای شروع ارسال، دکمه «➕ ساخت برنامه جدید» را بزنید.\n"
                "در همان فرایند، کانال مقصد را تایید می‌کنید، دسته محتوا می‌سازید "
                "و برنامه انتشار را فعال می‌کنید.",
                with_keypad=True,
            )
            return

        msg = (
            "📊 گزارش فعالیت\n\n"
            f"امروز: ✅ {stats['today_sent']} ارسال | ❌ {stats['today_failed']} خطا\n"
            f"کل: ✅ {stats['total_sent']} ارسال | ❌ {stats['total_failed']} خطا | ⏳ {stats['total_pending']} در صف\n"
        )

        if logs:
            msg += "\nآخرین رویدادها:\n"
            for log in logs:
                emoji = "✅" if log["status"] == "sent" else ("⏳" if log["status"] == "pending" else "❌")
                t = fmt_jalali_tehran(log["created_at"], "%m/%d %H:%M")
                src = log["source_name"] or "؟"
                tgt = (log["target_channel_id"] or "؟")[:20]
                msg += f"{emoji} {t} | {src} → {tgt}\n"
                if log["status"] == "failed" and log["last_error"]:
                    err = log["last_error"][:60]
                    msg += f"   ❗ {err}\n"

        await client.send_message(user_id, msg, with_keypad=True)
    except Exception as e:
        logger.error(f"/logs error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


# ─────────────────────────────────────────────
# SCHEDULE / PLAN
# ─────────────────────────────────────────────

async def _start_addplan_for_route(client, user_id: int, route_id: int) -> None:
    """Skip route selection and go directly to plan type selection."""
    conversation_states[user_id] = {
        "command": "addplan_type_select",
        "route_id": route_id,
    }
    await client.send_message(user_id, _plan_type_menu())


async def handle_addplan(client, user_id: int) -> None:
    logger.info(f"/addplan for user {user_id}")
    try:
        from src.database import pool
        from src.core.route_service import RouteService
        from src.core.source_service import SourceService
        from src.core.subscription_service import SubscriptionService
        access_state = await SubscriptionService(pool).get_access_state(user_id)
        if access_state == "expired":
            await client.send_message(
                user_id,
                "⚠️ تریال یا اشتراک فعالی ندارید.\n"
                "برای ساخت برنامه و ادامه انتشار، /buy را بفرستید."
            )
            return
        routes = await RouteService(pool).get_user_routes(user_id)
        active = [r for r in routes if r["is_active"]]
        if not active:
            await client.send_message(user_id, "ابتدا یک مسیر بسازید.\n➕ /addroute")
            return

        route_map: Dict[str, int] = {}
        msg = "📅 برای کدام مسیر برنامه‌ریزی می‌کنید؟\n\n"
        from src.core.source_service import SourceService
        for i, r in enumerate(active, 1):
            source_name = "؟"
            if r.get("source_id"):
                src = await SourceService(pool).get_source(r["source_id"])
                source_name = src.name if src else "؟"
            target = r.get("target_channel_id", "؟")
            msg += f"{i}️⃣  {source_name} → {target}\n"
            route_map[str(i)] = r["id"]

        msg += "\nشماره را وارد کنید:"
        await client.send_message(user_id, msg)
        conversation_states[user_id] = {
            "command": "addplan_route_select",
            "route_map": route_map,
        }
    except Exception as e:
        logger.error(f"/addplan error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_addplan_route_selection(client, user_id: int, text: str) -> None:
    state = conversation_states.get(user_id, {})
    route_map = state.get("route_map", {})
    route_id = route_map.get(normalize_digits(text.strip()))
    if not route_id:
        await client.send_message(user_id, "❌ شماره نامعتبر. دوباره وارد کنید.")
        return

    state["route_id"] = route_id
    state["command"] = "addplan_type_select"
    await client.send_message(user_id, _plan_type_menu())


async def handle_addplan_type_selection(client, user_id: int, text: str) -> None:
    state = conversation_states.get(user_id, {})
    choice = normalize_digits(text.strip())
    if choice in {"3", "4", "5", "6", "7", "8"}:
        from src.database import pool
        from src.core.subscription_service import SubscriptionService
        if not await SubscriptionService(pool).can_use_professional_plans(user_id):
            await client.send_message(user_id, _professional_plan_locked_message())
            return

    if choice == "1":
        state["command"] = "addplan_interval"
        await client.send_message(user_id, "⏱️ هر چند دقیقه یک پیام؟ (مثال: 60)")
    elif choice == "2":
        state["command"] = "addplan_daily_count"
        state["sub_step"] = 1
        await client.send_message(user_id, "📊 چند پیام در روز؟ (مثال: 3)")
    elif choice == "3":
        state["command"] = "addplan_professional_input"
        state["plan_kind"] = "campaign"
        await client.send_message(
            user_id,
            "🚀 کمپین حرفه‌ای را وارد کنید:\n"
            "فرمت: 1403/03/01 تا 1403/03/15 | 6 | شنبه تا چهارشنبه | 10 تا 23"
        )
    elif choice == "4":
        state["command"] = "addplan_professional_input"
        state["plan_kind"] = "smart_queue"
        await client.send_message(
            user_id,
            "🔁 صف هوشمند را وارد کنید:\n"
            "فرمت: 8 | 10 تا 23 | چرخشی\n"
            "برای حالت یک‌بار به جای چرخشی بنویسید: یک‌بار"
        )
    elif choice == "5":
        state["command"] = "addplan_professional_input"
        state["plan_kind"] = "timing_pattern"
        await client.send_message(
            user_id,
            "🧠 الگوی زمانی را وارد کنید:\n"
            "فرمت: humanized | 5 | 09 تا 23 | 12\n"
            "الگوها: humanized, store, low_risk, launch"
        )
    elif choice == "6":
        state["command"] = "addplan_professional_input"
        state["plan_kind"] = "multi_stage"
        await client.send_message(
            user_id,
            "📈 پلن چندمرحله‌ای را وارد کنید:\n"
            "فرمت سریع: 3 روز اول روزی 10 پست بعد 7 روز روزی 5 پست"
        )
    elif choice == "7":
        state["command"] = "addplan_professional_input"
        state["plan_kind"] = "content_mix"
        await client.send_message(
            user_id,
            "🎛️ ترکیب محتوا را وارد کنید:\n"
            "فرمت: روزی 2 ویدیو 3 عکس 1 متن بین 9 تا 22"
        )
    elif choice == "8":
        state["command"] = "addplan_professional_input"
        state["plan_kind"] = "quick"
        await client.send_message(
            user_id,
            "⚡ دستور سریع را بفرستید. نمونه‌ها:\n"
            "روزی 6 پست بین 10 تا 23 چرخشی\n"
            "از 1403/03/01 تا 1403/03/15 روزی 5 پست شنبه تا چهارشنبه\n"
            "روزی 2 ویدیو 3 عکس 1 متن بین 9 تا 22"
        )
    else:
        await client.send_message(user_id, "❌ عدد 1 تا 8 وارد کنید.")


async def handle_addplan_interval_input(client, user_id: int, text: str) -> None:
    try:
        minutes = int(normalize_digits(text.strip()))
    except ValueError:
        await client.send_message(user_id, "❌ عدد وارد کنید.")
        return
    if not 1 <= minutes <= 10080:
        await client.send_message(user_id, "❌ بین 1 و 10080 دقیقه.")
        return
    await handle_addplan_interval(client, user_id, minutes)


async def handle_addplan_daily_count_input(client, user_id: int, text: str) -> None:
    state = conversation_states.get(user_id, {})
    sub_step = state.get("sub_step", 1)

    if sub_step == 1:
        try:
            count = int(normalize_digits(text.strip()))
        except ValueError:
            await client.send_message(user_id, "❌ عدد وارد کنید.")
            return
        if not 1 <= count <= 48:
            await client.send_message(user_id, "❌ بین 1 و 48.")
            return
        await handle_addplan_daily_count(client, user_id, count, _auto_daily_times(count))
    elif sub_step == 2:
        times = []
        try:
            for part in normalize_digits(text.strip()).split():
                h, m = part.split(":")
                times.append((int(h), int(m)))
        except Exception:
            await client.send_message(user_id, "❌ فرمت اشتباه.")
            return
        if len(times) != state.get("daily_count", 0):
            await client.send_message(user_id, f"❌ باید دقیقاً {state['daily_count']} وقت وارد کنید.")
            return
        await handle_addplan_daily_count(client, user_id, state["daily_count"], times)


async def handle_addplan_interval(client, user_id: int, interval_minutes: int) -> None:
    try:
        from src.database import pool
        from src.core.schedule_service import ScheduleService
        state = conversation_states.pop(user_id, {})
        route_id = state.get("route_id")
        if not route_id:
            await client.send_message(user_id, "❌ جلسه منقضی شد.")
            return
        sched = await ScheduleService(pool).create_schedule(
            user_id=user_id, route_id=route_id,
            schedule_type="interval", interval_minutes=interval_minutes
        )
        await client.send_message(
            user_id,
            f"✅ برنامه ساخته شد!\nنوع: هر {interval_minutes} دقیقه\nاجرای بعدی: {fmt_jalali_tehran(sched.next_run)}",
            with_keypad=True,
        )
    except Exception as e:
        logger.error(f"addplan_interval error: {e}")
        conversation_states.pop(user_id, None)
        await client.send_message(user_id, "خطایی رخ داد.")


async def handle_addplan_daily_count(
    client, user_id: str, daily_count: int, times: List[Tuple[int, int]]
) -> None:
    try:
        from src.database import pool
        from src.core.schedule_service import ScheduleService
        state = conversation_states.pop(user_id, {})
        route_id = state.get("route_id")
        if not route_id:
            await client.send_message(user_id, "❌ جلسه منقضی شد.")
            return
        sched = await ScheduleService(pool).create_schedule(
            user_id=user_id, route_id=route_id,
            schedule_type="daily_count", daily_count=daily_count, times=times
        )
        times_str = ", ".join(f"{h:02d}:{m:02d}" for h, m in sorted(times))
        await client.send_message(
            user_id,
            f"✅ برنامه ساخته شد!\nنوع: {daily_count} پیام/روز\nاوقات: {times_str}",
            with_keypad=True,
        )
    except Exception as e:
        logger.error(f"addplan_daily_count error: {e}")
        conversation_states.pop(user_id, None)
        await client.send_message(user_id, "خطایی رخ داد.")


def _parse_professional_plan(plan_kind: str, text: str) -> Tuple[str, Dict[str, Any]]:
    raw = normalize_digits(text.strip())
    if plan_kind == "quick":
        parsed = PersianQuickPlanParser().parse(raw)
        return parsed.plan_kind, parsed.config

    if plan_kind == "campaign":
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) != 4 or "تا" not in parts[0] or "تا" not in parts[2] or "تا" not in parts[3]:
            raise ValueError("فرمت کمپین درست نیست.")
        start_date, end_date = [p.strip() for p in parts[0].split("تا", 1)]
        weekday_start, weekday_end = [p.strip() for p in parts[2].split("تا", 1)]
        start_time, end_time = [p.strip() for p in parts[3].split("تا", 1)]
        config = CampaignPlanConfig(
            start_date=start_date,
            end_date=end_date,
            daily_count=int(parts[1]),
            active_weekdays=expand_weekday_range(weekday_start, weekday_end),
            start_time=start_time,
            end_time=end_time,
            loop_mode=False,
        ).model_dump()
        return "campaign", config

    if plan_kind == "smart_queue":
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) != 3 or "تا" not in parts[1]:
            raise ValueError("فرمت صف هوشمند درست نیست.")
        start_time, end_time = [p.strip() for p in parts[1].split("تا", 1)]
        config = SmartQueuePlanConfig(
            daily_count=int(parts[0]),
            start_time=start_time,
            end_time=end_time,
            loop_mode="چرخشی" in parts[2],
        ).model_dump()
        return "smart_queue", config

    if plan_kind == "timing_pattern":
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) != 4 or "تا" not in parts[2]:
            raise ValueError("فرمت الگوی زمانی درست نیست.")
        start_time, end_time = [p.strip() for p in parts[2].split("تا", 1)]
        pattern_map = {"فروشگاهی": "store", "انسانی": "humanized", "کم‌ریسک": "low_risk", "لانچ": "launch"}
        pattern = pattern_map.get(parts[0], parts[0])
        config = TimingPatternPlanConfig(
            pattern=pattern,
            daily_count=int(parts[1]),
            start_time=start_time,
            end_time=end_time,
            jitter_minutes=int(parts[3]),
        ).model_dump()
        return "timing_pattern", config

    if plan_kind in ("multi_stage", "content_mix"):
        parsed = PersianQuickPlanParser().parse(raw)
        if parsed.plan_kind != plan_kind:
            raise ValueError("فرمت با نوع پلن انتخاب‌شده هم‌خوان نیست.")
        return parsed.plan_kind, parsed.config

    raise ValueError("نوع پلن پشتیبانی نمی‌شود.")


async def handle_addplan_professional_input(client, user_id: int, text: str) -> None:
    state = conversation_states.get(user_id, {})
    try:
        plan_kind, config = _parse_professional_plan(state.get("plan_kind", "quick"), text)
        from src.database import pool
        from src.core.schedule_service import ScheduleService
        preview = ScheduleService(pool).preview_plan(plan_kind, config)
        state["command"] = "addplan_confirm"
        state["plan_kind"] = plan_kind
        state["config"] = config
        await client.send_message(
            user_id,
            f"📋 پیش‌نمایش پلن:\n\n{preview}\n\n"
            "برای ساخت/ذخیره «بله» را بفرستید. برای لغو هر چیز دیگری بفرستید."
        )
    except Exception as e:
        await client.send_message(
            user_id,
            f"❌ نتوانستم پلن را بخوانم: {e}\n"
            "نمونه دستور سریع: روزی 6 پست بین 10 تا 23 چرخشی"
        )


async def handle_addplan_confirm(client, user_id: int, text: str) -> None:
    state = conversation_states.pop(user_id, {})
    if text.strip().lower() not in {"بله", "yes", "y", "آره", "اره", "ok", "اوکی"}:
        await client.send_message(user_id, "❌ ساخت پلن لغو شد.", with_keypad=True)
        return
    try:
        from src.database import pool
        from src.core.schedule_service import ScheduleService
        service = ScheduleService(pool)
        plan_kind = state["plan_kind"]
        config = state["config"]
        if state.get("edit_schedule_id"):
            sched = await service.update_professional_schedule(state["edit_schedule_id"], plan_kind, config)
            action = "به‌روزرسانی شد"
        else:
            sched = await service.create_professional_schedule(
                user_id=user_id,
                route_id=state["route_id"],
                plan_kind=plan_kind,
                config=config,
            )
            action = "ساخته شد"
        await client.send_message(
            user_id,
            f"✅ پلن حرفه‌ای #{sched.id} {action}!\n{describe_plan(plan_kind, config)}\n"
            f"اجرای بعدی: {fmt_jalali_tehran(sched.next_run)}",
            with_keypad=True,
        )
    except Exception as e:
        logger.error(f"addplan_confirm error: {e}")
        await client.send_message(user_id, "خطایی رخ داد.")


async def handle_listplans(client, user_id: int) -> None:
    logger.info(f"/listplans for user {user_id}")
    try:
        from src.database import pool
        from src.core.publishing_program_service import PublishingProgramService
        from src.core.schedule_service import ScheduleService

        programs = await PublishingProgramService(pool).list_programs(user_id)
        if programs:
            await client.send_message(user_id, f"📅 برنامه‌های انتشار شما ({len(programs)} برنامه):", with_keypad=True)
            import json as _json
            for p in programs:
                sched_id = p.get("schedule_id") or p.get("id")
                is_active = p.get("is_active")
                active = "✅" if is_active else "⏸"
                source = p.get("source_name") or "دسته نامشخص"
                channel = p.get("channel_id") or p.get("target_channel_id") or "کانال نامشخص"
                config = p.get("config") or {}
                if isinstance(config, str):
                    config = _json.loads(config)
                type_info = describe_plan(p.get("plan_kind") or p.get("schedule_type"), config)
                next_run = fmt_jalali_tehran(p.get("next_run"), "%m/%d %H:%M") if p.get("next_run") else "—"
                paused = f"\n⚠️ متوقف: {p.get('paused_reason')}" if p.get("paused_reason") else ""
                msg = (
                    f"{active} {source} ← {channel}\n"
                    f"زمان‌بندی: {type_info}\n"
                    f"اجرای بعدی: {next_run}{paused}"
                )
                toggle_label = "⏸ توقف" if is_active else "▶️ فعال‌سازی"
                btns = [
                    ("✏️ ویرایش زمانبندی", f"editplan_{sched_id}"),
                    (toggle_label, f"toggleplan_{sched_id}"),
                    ("🗑️ حذف برنامه", f"removeplan_{sched_id}"),
                ]
                keypad = _make_inline_keypad(btns, cols=2)
                await client.send_message(user_id, msg, inline_keypad=keypad)
            return

        schedules = await ScheduleService(pool).get_user_schedules(user_id)
        if not schedules:
            await client.send_message(user_id, "هنوز برنامه انتشاری ندارید.\n➕ ساخت برنامه جدید")
            return

        msg = "📅 برنامه‌های شما:\n\n"
        for s in schedules:
            active = "✅" if s.is_active else "⛔"
            if (s.plan_kind or s.schedule_type) in ("interval", "daily_count"):
                type_info = f"هر {s.interval_minutes} دقیقه" if s.schedule_type == "interval" else f"{s.daily_count} پیام/روز"
            else:
                type_info = describe_plan(s.plan_kind or s.schedule_type, s.config or {})
            next_run = fmt_jalali_tehran(s.next_run, "%m/%d %H:%M") if s.next_run else "—"
            paused = f"\n   دلیل توقف: {s.paused_reason}" if getattr(s, "paused_reason", None) else ""
            msg += f"{active} برنامه #{s.id}\n   {type_info}\n   بعدی: {next_run}{paused}\n\n"

        msg += "/toggleplan [شناسه] — فعال/غیرفعال\n/removeplan [شناسه] — حذف"
        await client.send_message(user_id, msg, with_keypad=True)
    except Exception as e:
        logger.error(f"/listplans error: {e}")
        await client.send_message(user_id, "خطایی رخ داد.")


async def handle_toggleplan(client, user_id: int, schedule_id: int) -> None:
    try:
        from src.database import pool
        from src.core.schedule_service import ScheduleService
        ss = ScheduleService(pool)
        sched = await ss.get_schedule(schedule_id)
        if not sched or sched.user_id != user_id:
            await client.send_message(user_id, "❌ برنامه یافت نشد.")
            return
        if sched.is_active:
            await ss.deactivate_schedule(schedule_id)
            await client.send_message(user_id, f"⛔ برنامه #{schedule_id} غیرفعال شد.")
        else:
            await ss.activate_schedule(schedule_id)
            await client.send_message(user_id, f"✅ برنامه #{schedule_id} فعال شد.")
    except Exception as e:
        logger.error(f"/toggleplan error: {e}")
        await client.send_message(user_id, "خطایی رخ داد.")


async def handle_removeplan(client, user_id: int, schedule_id: int) -> None:
    try:
        from src.database import pool
        from src.core.schedule_service import ScheduleService
        sched = await ScheduleService(pool).get_schedule(schedule_id)
        if not sched or sched.user_id != user_id:
            await client.send_message(user_id, "❌ برنامه یافت نشد.")
            return
        conversation_states[user_id] = {"command": "removeplan", "schedule_id": schedule_id}
        await client.send_message(user_id, f"🗑️ حذف برنامه #{schedule_id}؟\n«بله» برای تأیید.")
    except Exception as e:
        logger.error(f"/removeplan error: {e}")
        await client.send_message(user_id, "خطایی رخ داد.")


async def handle_removeplan_confirmation(client, user_id: int, text: str) -> None:
    state = conversation_states.pop(user_id, {})
    schedule_id = state.get("schedule_id")
    if text.strip().lower() not in ("بله", "yes", "y"):
        await client.send_message(user_id, "❌ حذف لغو شد.")
        return
    try:
        from src.database import pool
        from src.core.schedule_service import ScheduleService
        await ScheduleService(pool).delete_schedule(schedule_id)
        await client.send_message(user_id, f"✅ برنامه #{schedule_id} حذف شد.", with_keypad=True)
    except Exception as e:
        logger.error(f"removeplan_confirmation error: {e}")
        await client.send_message(user_id, "خطایی رخ داد.")


async def handle_editplan(client, user_id: int, schedule_id: int) -> None:
    try:
        from src.database import pool
        from src.core.schedule_service import ScheduleService
        sched = await ScheduleService(pool).get_schedule(schedule_id)
        if not sched or sched.user_id != user_id:
            await client.send_message(user_id, "❌ برنامه یافت نشد.")
            return
        conversation_states[user_id] = {
            "command": "addplan_type_select",
            "route_id": sched.route_id,
            "edit_schedule_id": schedule_id,
        }
        await client.send_message(
            user_id,
            f"✏️ ویرایش پلن #{schedule_id}\n"
            f"{_plan_type_menu()}"
        )
    except Exception as e:
        logger.error(f"/editplan error: {e}")
        await client.send_message(user_id, "خطایی رخ داد.")


async def handle_calendar(client, user_id: int) -> None:
    """Show channel selection then 7-day calendar for chosen destination."""
    logger.info(f"/calendar for user {user_id}")
    try:
        from src.database import pool
        from src.core.destination_service import DestinationService

        destinations = await DestinationService(pool).list_verified(user_id)

        if not destinations:
            await client.send_message(
                user_id,
                "📊 هیچ کانال مقصدی ندارید.\n"
                "برای شروع، «➕ ساخت برنامه جدید» را بزنید و کانال مقصد را اضافه کنید.",
                with_keypad=True,
            )
            return

        if len(destinations) == 1:
            # Only one channel — go directly to calendar
            await handle_calendar_display(client, user_id, destinations[0].channel_id)
            return

        # Multiple channels — ask user to select
        msg = "📊 تقویم انتشار کدام کانال را می‌خواهید ببینید؟\n\n"
        inline_buttons: List[Tuple[str, str]] = []
        for i, dest in enumerate(destinations, 1):
            ch = dest.channel_id
            msg += f"{i}️⃣ {ch}\n"
            inline_buttons.append((f"{i}️⃣ {ch}", f"cal_{ch}"))

        keypad = _make_inline_keypad(inline_buttons, cols=1)
        await client.send_message(user_id, msg, inline_keypad=keypad)
    except Exception as e:
        logger.error(f"/calendar error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")
