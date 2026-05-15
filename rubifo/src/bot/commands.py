from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import asyncio
from src.logger import logger
from src.config import SUBSCRIPTION_TIERS
from src.integrations.zarinpal import create_zarinpal_gateway

# In-memory storage for pending payments (authority -> {tier, amount, user_id})
pending_payments: Dict[str, Dict[str, Any]] = {}

# In-memory conversation states (user_id -> conversation_data)
conversation_states: Dict[int, Dict[str, Any]] = {}


# ─────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────

async def handle_start(client, user_id: int, username: Optional[str] = None) -> None:
    logger.info(f"/start for user {user_id}")
    try:
        from src.database import pool
        from src.core.user_service import UserService
        user = await UserService(pool).get_or_create_user(user_id, username)

        if user.is_trial_active:
            hours_left = (user.trial_end_at - datetime.now()).total_seconds() / 3600
            msg = f"👋 خوش آمدید به Rubifo\n\n⏳ تریال: {hours_left:.0f} ساعت باقیمانده"
        else:
            msg = "👋 خوش آمدید به Rubifo\n\n⚠️ تریال شما تمام شده"

        await client.send_message(user_id, msg, with_keypad=True)
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
        source = await SourceService(pool).create_source(user_id, name)

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
            f"وقتی تمام شد /savesource بفرستید."
        )
    except Exception as e:
        logger.error(f"source_name_input error: {e}")
        if user_id in conversation_states:
            del conversation_states[user_id]
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_source_collecting_message(client, user_id: int, message: Dict[str, Any]) -> None:
    """Store an incoming message as a source post during collecting mode."""
    state = conversation_states.get(user_id, {})
    source_id = state.get("source_id")
    if not source_id:
        return

    try:
        from src.database import pool
        from src.core.source_service import SourceService
        post = await SourceService(pool).add_post_from_message(source_id, message)

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
    """Finish collecting and show source summary."""
    state = conversation_states.pop(user_id, {})
    source_id = state.get("source_id")
    source_name = state.get("source_name", "")
    post_count = state.get("post_count", 0)

    if not source_id:
        await client.send_message(user_id, "❌ هیچ سورس فعالی برای ذخیره وجود ندارد.")
        return

    await client.send_message(
        user_id,
        f"✅ سورس «{source_name}» ذخیره شد!\n\n"
        f"📊 تعداد پست‌ها: {post_count}\n\n"
        f"📦 /mysources — مشاهده همه سورس‌ها\n"
        f"➕ /addroute — اتصال این سورس به کانال",
        with_keypad=True,
    )


async def handle_mysources(client, user_id: int) -> None:
    """List all sources for user."""
    logger.info(f"/mysources for user {user_id}")
    try:
        from src.database import pool
        from src.core.source_service import SourceService
        ss = SourceService(pool)
        sources = await ss.get_user_sources(user_id)

        if not sources:
            await client.send_message(
                user_id,
                "📦 هیچ سورسی ندارید.\n✏️ /addsource برای ساختن سورس جدید.",
                with_keypad=True,
            )
            return

        msg = "📦 سورس‌های شما:\n\n"
        for s in sources:
            count = await ss.count_posts(s.id)
            msg += f"#{s.id} — {s.name}\n   📝 {count} پست\n\n"

        msg += (
            "دستورات:\n"
            "/viewsource [شناسه] — مشاهده پست‌ها\n"
            "/addpost [شناسه] — افزودن پست\n"
            "/deletesource [شناسه] — حذف سورس"
        )
        await client.send_message(user_id, msg, with_keypad=True)
    except Exception as e:
        logger.error(f"/mysources error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_viewsource(client, user_id: int, source_id: int) -> None:
    """Show posts in a source."""
    try:
        from src.database import pool
        from src.core.source_service import SourceService
        ss = SourceService(pool)
        source = await ss.get_source(source_id)

        if not source or source.user_id != user_id:
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
        source = await SourceService(pool).get_source(source_id)

        if not source or source.user_id != user_id:
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
        ss = SourceService(pool)
        post = await ss.get_post(post_id)

        if not post:
            await client.send_message(user_id, "❌ پست یافت نشد.")
            return

        source = await ss.get_source(post.source_id)
        if not source or source.user_id != user_id:
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
        source = await SourceService(pool).get_source(source_id)

        if not source or source.user_id != user_id:
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
        from src.core.route_service import RouteService
        from src.core.user_service import UserService

        user = await UserService(pool).get_user(user_id)
        if not user:
            await client.send_message(user_id, "ابتدا /start را بفرستید.")
            return

        can_create, error_msg = await RouteService(pool).can_create_route(user_id)
        if not can_create:
            await client.send_message(user_id, error_msg)
            return

        sources = await SourceService(pool).get_user_sources(user_id)
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

            source_id = state["source_id"]
            source_name = state["source_name"]

            route_id = await RouteService(pool).create_route(user_id, source_id, target)
            del conversation_states[user_id]

            await client.send_message(
                user_id,
                f"✅ مسیر #{route_id} ساخته شد!\n\n"
                f"📦 سورس: {source_name}\n"
                f"📥 مقصد: {target}\n\n"
                f"⚠️ مطمئن شوید ربات @Rubifo ادمین کانال مقصد است.\n\n"
                f"📅 /addplan برای تنظیم زمان‌بندی ارسال",
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

        msg = "📋 مسیرهای شما:\n\n"
        for route in routes:
            route_id = route["id"]
            source_id = route.get("source_id")
            target = route.get("target_channel_id", "?")
            active = "✅" if route["is_active"] else "⛔"

            source_name = "?"
            if source_id:
                source = await SourceService(pool).get_source(source_id)
                source_name = source.name if source else str(source_id)

            pending = await RouteService(pool).get_route_queue_count(route_id, "pending")
            sent = await RouteService(pool).get_route_queue_count(route_id, "sent")

            msg += (
                f"{active} مسیر #{route_id}\n"
                f"   📦 {source_name} → {target}\n"
                f"   صف: {pending} در انتظار | {sent} ارسال شده\n\n"
            )

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

    if command == "source_naming":
        del conversation_states[user_id]
        await handle_source_name_input(client, user_id, text)
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


# ─────────────────────────────────────────────
# PAYMENT
# ─────────────────────────────────────────────

async def handle_buy(client, user_id: int) -> None:
    logger.info(f"/buy for user {user_id}")
    try:
        from src.database import pool
        from src.core.subscription_service import SubscriptionService
        active_sub = await SubscriptionService(pool).get_active_subscription(user_id)
        if active_sub:
            await client.send_message(
                user_id,
                f"شما اشتراک {active_sub.tier} دارید.\nتاریخ پایان: {active_sub.end_date}\n\n/renew برای تمدید"
            )
            return

        await client.send_message(
            user_id,
            "سطح‌های اشتراک Rubifo:\n\n"
            "📦 پایه (Basic)\n   • 1 مسیر | 50,000 تومان/ماه\n   /buy_basic\n\n"
            "⭐ حرفه‌ای (Pro)\n   • 3 مسیر | 120,000 تومان/ماه\n   /buy_pro\n\n"
            "👑 ویژه (Enterprise)\n   • 10 مسیر | 350,000 تومان/ماه\n   /buy_enterprise"
        )
    except Exception as e:
        logger.error(f"/buy error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_buy_tier(client, user_id: int, tier: str) -> None:
    logger.info(f"/buy_{tier} for user {user_id}")
    if tier not in SUBSCRIPTION_TIERS:
        await client.send_message(user_id, "سطح اشتراک نامعتبر است.")
        return
    try:
        from src.database import pool
        from src.core.subscription_service import SubscriptionService
        amount = SUBSCRIPTION_TIERS[tier]["price_monthly"]
        gateway = create_zarinpal_gateway(sandbox=True)
        success, result = await gateway.request_payment(
            amount=amount, description=f"اشتراک {tier} - Rubifo", callback_url=None
        )
        if not success:
            await client.send_message(user_id, f"خطا در درخواست پرداخت: {result}")
            return

        authority = result.split("/StartPay/")[-1]
        pending_payments[authority] = {"user_id": user_id, "tier": tier, "amount": amount}
        await client.send_message(user_id, f"لینک پرداخت:\n{result}\n\nلطفا منتظر تأیید بمانید...")
        asyncio.create_task(
            verify_payment_polling(client, SubscriptionService(pool), authority, amount)
        )
    except Exception as e:
        logger.error(f"/buy_{tier} error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


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
                    f"✅ پرداخت تأیید شد!\n\nاشتراک {tier} فعال شد.\nتاریخ پایان: {sub.end_date}"
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
        gateway = create_zarinpal_gateway(sandbox=True)
        success, result = await gateway.request_payment(
            amount=amount, description=f"تمدید اشتراک {tier} - Rubifo", callback_url=None
        )
        if not success:
            await client.send_message(user_id, f"خطا: {result}")
            return

        authority = result.split("/StartPay/")[-1]
        pending_payments[authority] = {"user_id": user_id, "tier": tier, "amount": amount, "is_renewal": True}
        await client.send_message(user_id, f"لینک تمدید:\n{result}\n\nلطفا منتظر تأیید بمانید...")
        asyncio.create_task(
            verify_renewal_payment_polling(client, SubscriptionService(pool), authority, amount)
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
                    f"✅ تمدید انجام شد!\nتاریخ پایان جدید: {sub.end_date}"
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
        "✏️ سورس‌ها:\n"
        "/addsource — سورس جدید\n"
        "/mysources — سورس‌های من\n"
        "/addpost [شناسه] — افزودن پست به سورس\n"
        "/viewsource [شناسه] — مشاهده پست‌ها\n"
        "/removepost [شناسه] — حذف پست\n"
        "/deletesource [شناسه] — حذف سورس\n\n"
        "➕ مسیرها:\n"
        "/addroute — مسیر جدید\n"
        "/listroutes — مسیرهای من\n"
        "/removeroute [شناسه] — حذف مسیر\n\n"
        "📅 برنامه‌ریزی:\n"
        "/addplan — برنامه جدید\n"
        "/listplans — برنامه‌های من\n"
        "/toggleplan [شناسه] — فعال/غیرفعال\n"
        "/removeplan [شناسه] — حذف برنامه\n\n"
        "💳 اشتراک:\n"
        "/buy — خرید اشتراک\n"
        "/renew — تمدید اشتراک\n\n"
        "📊 /logs — گزارش فعالیت‌ها"
    )
    await client.send_message(user_id, msg, with_keypad=True)


async def handle_logs(client, user_id: int) -> None:
    logger.info(f"/logs for user {user_id}")
    try:
        from src.database import pool
        logs = await pool.fetch(
            """
            SELECT pq.id, pq.status, pq.created_at, pq.last_error,
                   r.target_channel_id, s.name as source_name
            FROM post_queue pq
            JOIN routes r ON pq.route_id = r.id
            LEFT JOIN sources s ON r.source_id = s.id
            WHERE r.user_id = $1
            ORDER BY pq.created_at DESC
            LIMIT 20
            """,
            user_id,
        )
        if not logs:
            await client.send_message(user_id, "هیچ فعالیتی برای نمایش وجود ندارد.")
            return

        msg = "📊 فعالیت‌های اخیر:\n\n"
        for log in logs:
            emoji = "✅" if log["status"] == "sent" else "❌"
            t = log["created_at"].strftime("%H:%M")
            src = log["source_name"] or "?"
            tgt = log["target_channel_id"] or "?"
            msg += f"{emoji} {t} | {src} → {tgt}\n"
            if log["status"] == "failed" and log["last_error"]:
                msg += f"   ❗ {log['last_error'][:50]}\n"

        await client.send_message(user_id, msg, with_keypad=True)
    except Exception as e:
        logger.error(f"/logs error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


# ─────────────────────────────────────────────
# SCHEDULE / PLAN
# ─────────────────────────────────────────────

async def handle_addplan(client, user_id: int) -> None:
    logger.info(f"/addplan for user {user_id}")
    try:
        from src.database import pool
        from src.core.route_service import RouteService
        routes = await RouteService(pool).get_user_routes(user_id)
        if not routes:
            await client.send_message(user_id, "ابتدا یک مسیر بسازید.\n/addroute")
            return

        msg = "📅 برای کدام مسیر برنامه‌ریزی؟\n\n"
        for r in routes:
            msg += f"#{r['id']}: → {r.get('target_channel_id', '?')}\n"
        msg += "\nشناسه مسیر را وارد کنید:"
        await client.send_message(user_id, msg)
        conversation_states[user_id] = {
            "command": "addplan_route_select",
            "routes": {r["id"]: r for r in routes},
            "step": 1,
        }
    except Exception as e:
        logger.error(f"/addplan error: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_addplan_route_selection(client, user_id: int, text: str) -> None:
    state = conversation_states.get(user_id, {})
    try:
        route_id = int(text.strip())
    except ValueError:
        await client.send_message(user_id, "❌ شناسه باید عدد باشد.")
        return

    if route_id not in state.get("routes", {}):
        await client.send_message(user_id, "❌ مسیر یافت نشد.")
        return

    state["route_id"] = route_id
    state["command"] = "addplan_type_select"
    await client.send_message(
        user_id,
        "نوع برنامه:\n\n1️⃣ بازه‌ای — هر N دقیقه\n2️⃣ روزانه — N پیام در اوقات مشخص\n\n1 یا 2 وارد کنید:"
    )


async def handle_addplan_type_selection(client, user_id: int, text: str) -> None:
    state = conversation_states.get(user_id, {})
    if text.strip() == "1":
        state["command"] = "addplan_interval"
        await client.send_message(user_id, "⏱️ هر چند دقیقه یک پیام؟ (مثال: 60)")
    elif text.strip() == "2":
        state["command"] = "addplan_daily_count"
        state["sub_step"] = 1
        await client.send_message(user_id, "📊 چند پیام در روز؟ (مثال: 3)")
    else:
        await client.send_message(user_id, "❌ عدد 1 یا 2 وارد کنید.")


async def handle_addplan_interval_input(client, user_id: int, text: str) -> None:
    try:
        minutes = int(text.strip())
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
            count = int(text.strip())
        except ValueError:
            await client.send_message(user_id, "❌ عدد وارد کنید.")
            return
        if not 1 <= count <= 48:
            await client.send_message(user_id, "❌ بین 1 و 48.")
            return
        state["daily_count"] = count
        state["sub_step"] = 2
        await client.send_message(
            user_id,
            f"{count} وقت را وارد کنید:\nفرمت: HH:MM HH:MM ...\nمثال: 09:00 14:00 19:00"
        )
    elif sub_step == 2:
        times = []
        try:
            for part in text.strip().split():
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
            f"✅ برنامه ساخته شد!\nنوع: هر {interval_minutes} دقیقه\nاجرای بعدی: {sched.next_run}",
            with_keypad=True,
        )
    except Exception as e:
        logger.error(f"addplan_interval error: {e}")
        conversation_states.pop(user_id, None)
        await client.send_message(user_id, "خطایی رخ داد.")


async def handle_addplan_daily_count(
    client, user_id: int, daily_count: int, times: List[Tuple[int, int]]
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


async def handle_listplans(client, user_id: int) -> None:
    logger.info(f"/listplans for user {user_id}")
    try:
        from src.database import pool
        from src.core.schedule_service import ScheduleService
        schedules = await ScheduleService(pool).get_user_schedules(user_id)
        if not schedules:
            await client.send_message(user_id, "هیچ برنامه‌ای ندارید.\n/addplan برای ایجاد.")
            return

        msg = "📅 برنامه‌های شما:\n\n"
        for s in schedules:
            active = "✅" if s.is_active else "⛔"
            type_info = f"هر {s.interval_minutes} دقیقه" if s.schedule_type == "interval" else f"{s.daily_count} پیام/روز"
            next_run = s.next_run.strftime("%d/%m %H:%M") if s.next_run else "—"
            msg += f"{active} #{s.id} — مسیر #{s.route_id}\n   {type_info} | بعدی: {next_run}\n\n"

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
    await client.send_message(
        user_id,
        "ویرایش برنامه در دسترس نیست.\nلطفا برنامه را حذف و دوباره بسازید.\n/removeplan"
    )


async def handle_calendar(client, user_id: int) -> None:
    await handle_listplans(client, user_id)
