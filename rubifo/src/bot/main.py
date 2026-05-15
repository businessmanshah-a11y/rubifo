import asyncio
from rubpy import Client
from src.database import init_db, close_db
from src.logger import logger
from src.config import BOT_TOKEN, API_RATE_LIMIT_DELAY


class RufifoBot:
    """Main Rubifo bot class for handling Rubika messages and commands."""

    def __init__(self, token: str):
        self.client = Client()
        self.token = token
        self.background_tasks = []

    async def start(self) -> None:
        """Start the bot and database connection."""
        logger.info("Starting Rufifo bot...")

        await init_db()

        @self.client.on_message_receive()
        async def handle_message(user_id: int, message: dict) -> None:
            """Route incoming messages to appropriate handlers."""
            try:
                from src.bot.handlers import route_message
                await route_message(self.client, user_id, message)
            except Exception as e:
                logger.error(f"Error handling message from {user_id}: {e}")

        self.background_tasks.append(
            asyncio.create_task(self._trial_reminder_loop())
        )

        logger.info("Bot started and listening for messages")
        await self.client.run()

    async def stop(self) -> None:
        """Stop the bot and close database connection."""
        logger.info("Stopping bot...")
        for task in self.background_tasks:
            task.cancel()
        await close_db()
        try:
            await self.client.stop()
        except Exception as e:
            logger.warning(f"Error stopping client: {e}")

    async def _trial_reminder_loop(self) -> None:
        """Background loop to send trial expiration reminders."""
        from src.database import fetch
        from datetime import datetime

        while True:
            try:
                await asyncio.sleep(3600)

                users = await fetch(
                    "SELECT user_id, trial_end_at FROM users "
                    "WHERE trial_end_at <= NOW() + interval '24 hours' "
                    "AND trial_end_at > NOW() "
                    "AND is_trial_active = true"
                )

                for user in users:
                    try:
                        hours_left = (
                            (user["trial_end_at"] - datetime.now()).total_seconds()
                            / 3600
                        )
                        message = (
                            f"⏰ تریال شما {hours_left:.0f} ساعت دیگر تمام می‌شود.\n"
                            "/buy برای خرید اشتراک"
                        )
                        await self.client.send_message(user["user_id"], message)
                        logger.info(f"Trial reminder sent to {user['user_id']}")
                    except Exception as e:
                        logger.error(
                            f"Error sending reminder to {user['user_id']}: {e}"
                        )

            except asyncio.CancelledError:
                logger.info("Trial reminder loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in trial reminder loop: {e}")
                await asyncio.sleep(60)


async def main() -> None:
    """Entry point for the bot."""
    bot = RufifoBot(BOT_TOKEN)

    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
