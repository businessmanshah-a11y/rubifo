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
    """Handle /addroute command."""
    logger.info(f"Handling /addroute command for user {user_id}")
    await client.send_message(user_id, "درحال توسعه...")


async def handle_listroutes(client, user_id: int) -> None:
    """Handle /listroutes command."""
    logger.info(f"Handling /listroutes command for user {user_id}")
    await client.send_message(user_id, "درحال توسعه...")


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
    """Handle /renew command for subscription renewal."""
    logger.info(f"Handling /renew command for user {user_id}")
    await client.send_message(user_id, "درحال توسعه...")
