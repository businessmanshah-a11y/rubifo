from typing import Optional, Dict, Any
from datetime import datetime
import asyncio
from src.logger import logger
from src.database import get_db
from src.core.user_service import UserService
from src.config import SUBSCRIPTION_TIERS
from src.integrations.zarinpal import create_zarinpal_gateway

# In-memory storage for pending payments (authority -> {tier, amount, user_id})
pending_payments: Dict[str, Dict[str, Any]] = {}

# In-memory storage for conversation states (user_id -> conversation_data)
conversation_states: Dict[int, Dict[str, Any]] = {}


async def handle_start(client, user_id: int, username: Optional[str] = None) -> None:
    """Handle /start command for user registration."""
    logger.info(f"Handling /start command for user {user_id}")

    try:
        from src.database import pool
        user_service = UserService(pool)
        user = await user_service.get_or_create_user(user_id, username)

        if user.is_trial_active:
            hours_left = (user.trial_end_at - datetime.now()).total_seconds() / 3600
            message = (
                f"سلام! خوش آمدید به Rubifo 🎉\n\n"
                f"تریال شما {hours_left:.0f} ساعت فعال است.\n\n"
                f"دستورات:\n"
                f"/buy - خرید اشتراک\n"
                f"/help - راهنما"
            )
        else:
            message = (
                "سلام! تریال شما تمام شد.\n"
                "/buy را برای خرید اشتراک بفرستید."
            )

        await client.send_message(user_id, message)
        logger.info(f"Welcome message sent to user {user_id}")

    except Exception as e:
        logger.error(f"Error in /start command: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_buy(client, user_id: int) -> None:
    """Handle /buy command to display subscription tiers."""
    logger.info(f"Handling /buy command for user {user_id}")

    try:
        from src.database import pool
        from src.core.subscription_service import SubscriptionService
        from src.core.user_service import UserService

        user_service = UserService(pool)
        subscription_service = SubscriptionService(pool)

        # Check if user already has active subscription
        active_sub = await subscription_service.get_active_subscription(user_id)

        if active_sub:
            message = (
                f"شما در حال حاضر اشتراک {active_sub.tier} دارید.\n"
                f"تاریخ پایان: {active_sub.end_date}\n\n"
                f"/renew برای تمدید"
            )
            await client.send_message(user_id, message)
            return

        # Display tier options
        tiers_message = (
            "سطح‌های اشتراک Rubifo:\n\n"
            "📦 پایه (Basic)\n"
            "   • 1 مسیر فوروارد\n"
            "   • قیمت: 50,000 تومان/ماهانه\n"
            "   /buy_basic\n\n"
            "⭐ حرفه‌ای (Pro)\n"
            "   • 3 مسیر فوروارد\n"
            "   • قیمت: 120,000 تومان/ماهانه\n"
            "   /buy_pro\n\n"
            "👑 ویژه (Enterprise)\n"
            "   • 10 مسیر فوروارد\n"
            "   • قیمت: 350,000 تومان/ماهانه\n"
            "   /buy_enterprise"
        )

        await client.send_message(user_id, tiers_message)
        logger.info(f"Subscription tiers displayed to user {user_id}")

    except Exception as e:
        logger.error(f"Error in /buy command: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_buy_tier(client, user_id: int, tier: str) -> None:
    """Handle tier selection and initiate payment.

    Args:
        client: Rubpy bot client
        user_id: Rubika user ID
        tier: Subscription tier (basic, pro, enterprise)
    """
    logger.info(f"Handling /buy_{tier} command for user {user_id}")

    if tier not in SUBSCRIPTION_TIERS:
        await client.send_message(user_id, "سطح اشتراک نامعتبر است.")
        return

    try:
        from src.database import pool
        from src.core.subscription_service import SubscriptionService

        subscription_service = SubscriptionService(pool)

        # Get tier info
        tier_info = SUBSCRIPTION_TIERS[tier]
        amount = tier_info["price_monthly"]

        # Create payment request
        gateway = create_zarinpal_gateway(sandbox=True)
        success, result = await gateway.request_payment(
            amount=amount,
            description=f"اشتراک {tier} - Rubifo",
            callback_url=None,
        )

        if not success:
            logger.error(f"Payment request failed for user {user_id}: {result}")
            await client.send_message(user_id, f"خطا در درخواست پرداخت: {result}")
            return

        # Extract authority from result (payment_url)
        # URL format: https://sandbox.zarinpal.com/pg/StartPay/{authority}
        authority = result.split("/StartPay/")[-1]

        # Store pending payment
        pending_payments[authority] = {
            "user_id": user_id,
            "tier": tier,
            "amount": amount,
        }

        # Send payment link to user
        payment_message = (
            f"درخواست پرداخت برای اشتراک {tier} ایجاد شد.\n\n"
            f"لطفا بر روی لینک کلیک کنید و پرداخت را تکمیل کنید:\n"
            f"{result}\n\n"
            f"لطفا منتظر تأیید بمانید..."
        )
        await client.send_message(user_id, payment_message)

        # Start payment verification polling as background task
        asyncio.create_task(
            verify_payment_polling(client, subscription_service, authority, amount)
        )

        logger.info(f"Payment link sent to user {user_id}, authority: {authority}")

    except Exception as e:
        logger.error(f"Error in /buy_{tier} command: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def verify_payment_polling(
    client, subscription_service: "SubscriptionService", authority: str, amount: int
) -> None:
    """Poll Zarinpal for payment verification.

    Args:
        client: Rubpy bot client
        subscription_service: SubscriptionService instance
        authority: Payment authority from Zarinpal
        amount: Payment amount in Rials
    """
    MAX_ATTEMPTS = 30  # 5 minutes with 10-second intervals
    attempt = 0

    while attempt < MAX_ATTEMPTS:
        try:
            # Check if payment data exists
            if authority not in pending_payments:
                logger.warning(f"Payment {authority} no longer pending")
                break

            payment_data = pending_payments[authority]
            user_id = payment_data["user_id"]
            tier = payment_data["tier"]

            # Verify payment with Zarinpal
            gateway = create_zarinpal_gateway(sandbox=True)
            success, ref_id = await gateway.verify_payment(authority, amount)

            if success:
                # Payment verified - create subscription
                from src.database import pool
                from src.core.transaction_service import TransactionService

                transaction_service = TransactionService(pool)

                # Create subscription
                subscription = await subscription_service.create_subscription(user_id, tier, days=30)

                # Insert transaction
                await transaction_service.insert_transaction(
                    user_id=user_id,
                    amount=amount,
                    tier=tier,
                    status="completed",
                    reference_id=ref_id,
                )

                # Remove from pending
                del pending_payments[authority]

                # Send confirmation
                confirmation_message = (
                    f"✅ پرداخت تأیید شد!\n\n"
                    f"اشتراک {tier} شما فعال شد.\n"
                    f"تاریخ پایان: {subscription.end_date}\n\n"
                    f"اکنون می‌توانید از /addroute استفاده کنید."
                )
                await client.send_message(user_id, confirmation_message)

                logger.info(
                    f"Payment verified for user {user_id}, subscription {subscription.id} created"
                )
                return

            attempt += 1
            if attempt < MAX_ATTEMPTS:
                await asyncio.sleep(10)

        except Exception as e:
            logger.error(f"Error in payment verification for {authority}: {e}")
            attempt += 1
            if attempt < MAX_ATTEMPTS:
                await asyncio.sleep(10)

    # Timeout - send error message
    if authority in pending_payments:
        payment_data = pending_payments.pop(authority)
        user_id = payment_data["user_id"]

        timeout_message = (
            "⏱ مهلت تأیید پرداخت تمام شد.\n"
            "لطفا دوباره /buy را بفرستید."
        )
        await client.send_message(user_id, timeout_message)
        logger.warning(f"Payment verification timeout for {authority}")


async def handle_buy_basic(client, user_id: int) -> None:
    """Handle /buy_basic command."""
    await handle_buy_tier(client, user_id, "basic")


async def handle_buy_pro(client, user_id: int) -> None:
    """Handle /buy_pro command."""
    await handle_buy_tier(client, user_id, "pro")


async def handle_buy_enterprise(client, user_id: int) -> None:
    """Handle /buy_enterprise command."""
    await handle_buy_tier(client, user_id, "enterprise")


async def handle_help(client, user_id: int) -> None:
    """Handle /help command."""
    logger.info(f"Handling /help command for user {user_id}")
    help_text = (
        "دستورات Rubifo:\n"
        "/start - شروع\n"
        "/buy - خرید اشتراک\n"
        "/help - راهنما"
    )
    await client.send_message(user_id, help_text)


async def handle_addroute(client, user_id: int) -> None:
    """Handle /addroute command - start multi-step route creation.

    Step 1: Validate subscription and ask for source channel ID.
    """
    logger.info(f"Handling /addroute command for user {user_id}")

    try:
        from src.database import pool
        from src.core.route_service import RouteService
        from src.core.user_service import UserService

        user_service = UserService(pool)
        route_service = RouteService(pool)

        # Check if user account is active
        user = await user_service.get_user(user_id)
        if not user:
            await client.send_message(user_id, "ابتدا /start را بفرستید.")
            return

        # Check if can create route
        can_create, error_msg = await route_service.can_create_route(user_id)
        if not can_create:
            await client.send_message(user_id, error_msg)
            return

        # Initialize conversation state
        conversation_states[user_id] = {
            "command": "addroute",
            "step": 1,
            "source_channel_id": None,
            "target_channel_id": None,
        }

        # Ask for source channel ID
        prompt = (
            "یک مسیر جدید ایجاد کنید:\n\n"
            "1️⃣ شناسه کانال منبع را وارد کنید:\n"
            "(کانالی که می‌خواهید پست‌ها را از آن فوروارد کنید)"
        )
        await client.send_message(user_id, prompt)
        logger.info(f"Started /addroute conversation for user {user_id}")

    except Exception as e:
        logger.error(f"Error in /addroute command: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_addroute_conversation(client, user_id: int, text: str) -> None:
    """Handle conversation steps for /addroute command.

    Args:
        client: Rubpy bot client
        user_id: Rubika user ID
        text: User input text
    """
    if user_id not in conversation_states:
        return

    state = conversation_states[user_id]
    if state.get("command") != "addroute":
        return

    try:
        from src.database import pool
        from src.core.route_service import RouteService

        route_service = RouteService(pool)

        step = state.get("step", 1)

        if step == 1:
            # Parse source channel ID
            try:
                source_channel_id = int(text.strip())
            except ValueError:
                await client.send_message(user_id, "❌ شناسه کانال باید عدد باشد.")
                return

            # Verify bot has access to source channel
            # For now, we accept it (Rubika API verification would go here)
            state["source_channel_id"] = source_channel_id
            state["step"] = 2

            prompt = (
                "✅ کانال منبع ثبت شد.\n\n"
                "2️⃣ شناسه کانال مقصد را وارد کنید:\n"
                "(کانالی که می‌خواهید پست‌ها را به آن فوروارد کنید)"
            )
            await client.send_message(user_id, prompt)
            logger.info(f"User {user_id} provided source channel: {source_channel_id}")

        elif step == 2:
            # Parse target channel ID
            try:
                target_channel_id = int(text.strip())
            except ValueError:
                await client.send_message(user_id, "❌ شناسه کانال باید عدد باشد.")
                return

            source_channel_id = state["source_channel_id"]

            if source_channel_id == target_channel_id:
                await client.send_message(
                    user_id, "❌ کانال‌های منبع و مقصد نمی‌تواند یکی باشند."
                )
                return

            # Verify bot has access to target channel
            # For now, we accept it (Rubika API verification would go here)
            state["target_channel_id"] = target_channel_id
            state["step"] = 3

            # Create the route
            route_id = await route_service.create_route(
                user_id, source_channel_id, target_channel_id
            )

            confirmation = (
                f"✅ مسیر ایجاد شد!\n\n"
                f"شناسه مسیر: {route_id}\n"
                f"منبع: {source_channel_id}\n"
                f"مقصد: {target_channel_id}\n\n"
                "در حال جمع‌آوری پست‌های قدیمی..."
            )
            await client.send_message(user_id, confirmation)

            # Remove from conversation states
            del conversation_states[user_id]

            # Populate queue with existing posts from source channel
            await populate_route_queue(client, user_id, route_id, source_channel_id)

            logger.info(f"Route created and queue populated for user {user_id}: {route_id}")

    except Exception as e:
        logger.error(f"Error in /addroute conversation for user {user_id}: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")
        if user_id in conversation_states:
            del conversation_states[user_id]


async def populate_route_queue(
    client, user_id: int, route_id: int, source_channel_id: int
) -> None:
    """Populate queue with existing posts from source channel (T22).

    Args:
        client: Rubpy bot client
        user_id: Rubika user ID
        route_id: Route ID
        source_channel_id: Source channel ID
    """
    try:
        from src.database import pool
        from datetime import datetime, timedelta

        # Fetch posts from source channel via Rubika API
        # For MVP, we'll create a stub that can be replaced with real API calls
        posts = await fetch_channel_posts(client, source_channel_id)

        if not posts:
            await client.send_message(
                user_id, "✅ مسیر ایجاد شد! (هیچ پست قدیمی برای فوروارد نیافت)"
            )
            return

        # Insert posts into post_queue table, ordered by source_date ASC
        inserted_count = 0
        for post in sorted(posts, key=lambda p: p.get("date", 0)):
            try:
                await pool.execute(
                    """
                    INSERT INTO post_queue
                    (route_id, message_id_in_source, source_date, status)
                    VALUES ($1, $2, $3, 'pending')
                    """,
                    route_id,
                    post.get("message_id"),
                    datetime.fromtimestamp(post.get("date", 0)),
                )
                inserted_count += 1
            except Exception as e:
                logger.error(f"Error inserting post {post.get('message_id')}: {e}")
                continue

        completion_message = (
            f"✅ مسیر ایجاد شد!\n\n"
            f"تعداد پست‌های درج شده: {inserted_count}\n\n"
            f"/listroutes برای دیدن مسیرهایتان."
        )
        await client.send_message(user_id, completion_message)
        logger.info(f"Route {route_id}: {inserted_count} posts added to queue")

    except Exception as e:
        logger.error(f"Error populating queue for route {route_id}: {e}")
        await client.send_message(
            user_id, "خطایی در جمع‌آوری پست‌ها رخ داد. مسیر ایجاد شد اما بدون پست."
        )


async def fetch_channel_posts(client, channel_id: int) -> list:
    """Fetch recent posts from a channel via Rubika API.

    This is a stub that returns an empty list.
    Should be replaced with real Rubika API calls.

    Args:
        client: Rubpy bot client
        channel_id: Channel ID to fetch posts from

    Returns:
        List of post dictionaries with message_id and date
    """
    try:
        # Stub: would use client.get_channel_messages() or similar
        # For now, return empty list - real implementation depends on Rubpy/Rubika API
        logger.info(f"Fetching posts from channel {channel_id} (stub implementation)")
        return []

    except Exception as e:
        logger.error(f"Error fetching posts from channel {channel_id}: {e}")
        return []


async def handle_listroutes(client, user_id: int) -> None:
    """Handle /listroutes command to show all user routes.

    Displays routes with queue counts and status.
    """
    logger.info(f"Handling /listroutes command for user {user_id}")

    try:
        from src.database import pool
        from src.core.route_service import RouteService

        route_service = RouteService(pool)

        # Get all routes for user
        routes = await route_service.get_user_routes(user_id)

        if not routes:
            await client.send_message(user_id, "شما هیچ مسیری ندارید.\n/addroute برای اضافه کردن مسیر.")
            return

        # Build message with route list
        message = "📍 مسیرهای شما:\n\n"

        for i, route in enumerate(routes, 1):
            route_id = route["id"]
            source = route["source_channel_id"]
            target = route["target_channel_id"]
            is_active = "✅" if route["is_active"] else "⛔"

            # Get queue count
            pending_count = await route_service.get_route_queue_count(route_id, "pending")
            sent_count = await route_service.get_route_queue_count(route_id, "sent")
            failed_count = await route_service.get_route_queue_count(route_id, "failed")

            route_info = (
                f"{i}. {is_active} مسیر #{route_id}\n"
                f"   {source} ← → {target}\n"
                f"   صف: {pending_count} درانتظار | {sent_count} ارسال شده | {failed_count} ناموفق\n\n"
            )
            message += route_info

        # Add action buttons/instructions
        message += (
            "دستورات:\n"
            "/removeroute [شناسه] - حذف مسیر\n"
            "/updatesource [شناسه] - بروزرسانی پست‌های جدید\n"
            "/sync [شناسه] - همگام‌سازی مسیر\n"
        )

        await client.send_message(user_id, message)
        logger.info(f"Listed {len(routes)} routes for user {user_id}")

    except Exception as e:
        logger.error(f"Error in /listroutes command: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def handle_removeroute(client, user_id: int, route_id: int) -> None:
    """Handle /removeroute command."""
    logger.info(f"Handling /removeroute command for user {user_id}")
    await client.send_message(user_id, "درحال توسعه...")


async def handle_updatesource(client, user_id: int, route_id: int) -> None:
    """Handle /updatesource command."""
    logger.info(f"Handling /updatesource command for user {user_id}")
    await client.send_message(user_id, "درحال توسعه...")


async def handle_sync(client, user_id: int, route_id: int) -> None:
    """Handle /sync command."""
    logger.info(f"Handling /sync command for user {user_id}")
    await client.send_message(user_id, "درحال توسعه...")


async def handle_renew(client, user_id: int) -> None:
    """Handle /renew command for subscription renewal.

    Shows current subscription and initiates renewal payment.
    """
    logger.info(f"Handling /renew command for user {user_id}")

    try:
        from src.database import pool
        from src.core.subscription_service import SubscriptionService
        from src.core.transaction_service import TransactionService

        subscription_service = SubscriptionService(pool)
        transaction_service = TransactionService(pool)

        # Check current active subscription
        active_sub = await subscription_service.get_active_subscription(user_id)

        if not active_sub:
            await client.send_message(
                user_id,
                "شما اشتراک فعالی ندارید.\n"
                "/buy را برای خرید اشتراک بفرستید."
            )
            return

        # Show current subscription info
        tier = active_sub.tier
        tier_info = SUBSCRIPTION_TIERS.get(tier, {})
        amount = tier_info.get("price_monthly", 0)

        info_message = (
            f"اشتراک فعلی: {tier}\n"
            f"تاریخ پایان: {active_sub.end_date}\n"
            f"قیمت تمدید: {amount:,} تومان\n\n"
            "درحال ایجاد درخواست پرداخت..."
        )

        await client.send_message(user_id, info_message)

        # Create payment request for same tier
        gateway = create_zarinpal_gateway(sandbox=True)
        success, result = await gateway.request_payment(
            amount=amount,
            description=f"تمدید اشتراک {tier} - Rubifo",
            callback_url=None,
        )

        if not success:
            logger.error(f"Renewal payment request failed for user {user_id}: {result}")
            await client.send_message(user_id, f"خطا در درخواست پرداخت: {result}")
            return

        # Extract authority from payment URL
        authority = result.split("/StartPay/")[-1]

        # Store pending payment (mark as renewal)
        pending_payments[authority] = {
            "user_id": user_id,
            "tier": tier,
            "amount": amount,
            "is_renewal": True,
        }

        # Send payment link
        payment_message = (
            f"لینک پرداخت تمدید اشتراک:\n{result}\n\n"
            f"لطفا منتظر تأیید بمانید..."
        )
        await client.send_message(user_id, payment_message)

        # Start payment verification polling
        asyncio.create_task(
            verify_renewal_payment_polling(
                client, subscription_service, authority, amount
            )
        )

        logger.info(f"Renewal payment link sent to user {user_id}, authority: {authority}")

    except Exception as e:
        logger.error(f"Error in /renew command: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")


async def verify_renewal_payment_polling(
    client, subscription_service: "SubscriptionService", authority: str, amount: int
) -> None:
    """Poll Zarinpal for renewal payment verification.

    Args:
        client: Rubpy bot client
        subscription_service: SubscriptionService instance
        authority: Payment authority from Zarinpal
        amount: Payment amount in Rials
    """
    MAX_ATTEMPTS = 30  # 5 minutes with 10-second intervals
    attempt = 0

    while attempt < MAX_ATTEMPTS:
        try:
            # Check if payment data exists
            if authority not in pending_payments:
                logger.warning(f"Renewal payment {authority} no longer pending")
                break

            payment_data = pending_payments[authority]
            user_id = payment_data["user_id"]
            tier = payment_data["tier"]

            # Verify payment with Zarinpal
            gateway = create_zarinpal_gateway(sandbox=True)
            success, ref_id = await gateway.verify_payment(authority, amount)

            if success:
                # Payment verified - extend subscription
                from src.database import pool
                from src.core.transaction_service import TransactionService

                transaction_service = TransactionService(pool)

                # Extend subscription by 30 days
                subscription = await subscription_service.extend_subscription(user_id, days=30)

                # Insert transaction
                await transaction_service.insert_transaction(
                    user_id=user_id,
                    amount=amount,
                    tier=tier,
                    status="completed",
                    reference_id=ref_id,
                )

                # Remove from pending
                del pending_payments[authority]

                # Send confirmation
                confirmation_message = (
                    f"✅ تمدید پرداخت شد!\n\n"
                    f"اشتراک {tier} شما تمدید شد.\n"
                    f"تاریخ پایان جدید: {subscription.end_date}\n\n"
                    f"سپاسگزاریم!"
                )
                await client.send_message(user_id, confirmation_message)

                logger.info(
                    f"Renewal payment verified for user {user_id}, subscription {subscription.id} extended"
                )
                return

            attempt += 1
            if attempt < MAX_ATTEMPTS:
                await asyncio.sleep(10)

        except Exception as e:
            logger.error(f"Error in renewal payment verification for {authority}: {e}")
            attempt += 1
            if attempt < MAX_ATTEMPTS:
                await asyncio.sleep(10)

    # Timeout - send error message
    if authority in pending_payments:
        payment_data = pending_payments.pop(authority)
        user_id = payment_data["user_id"]

        timeout_message = (
            "⏱ مهلت تأیید پرداخت تمام شد.\n"
            "لطفا دوباره /renew را بفرستید."
        )
        await client.send_message(user_id, timeout_message)
        logger.warning(f"Renewal payment verification timeout for {authority}")
