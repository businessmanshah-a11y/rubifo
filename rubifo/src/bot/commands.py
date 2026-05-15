from typing import Optional
from datetime import datetime
from src.logger import logger
from src.database import get_db
from src.core.user_service import UserService


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
