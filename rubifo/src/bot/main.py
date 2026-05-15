import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from rubpy import BotClient
from rubpy.bot.models import Keypad, KeypadRow, Button
from rubpy.bot.enums import ChatKeypadTypeEnum, ButtonTypeEnum
from src.database import init_db, close_db
from src.logger import logger
from src.config import BOT_TOKEN, USER_SESSION_NAME, CHANNEL_POLL_INTERVAL

OFFSET_FILE = "logs/bot_offset.json"

MAIN_KEYPAD = Keypad(rows=[
    KeypadRow(buttons=[
        Button(id="addroute", type=ButtonTypeEnum.SIMPLE, button_text="➕ مسیر جدید"),
        Button(id="listroutes", type=ButtonTypeEnum.SIMPLE, button_text="📋 مسیرهای من"),
    ]),
    KeypadRow(buttons=[
        Button(id="updatesource", type=ButtonTypeEnum.SIMPLE, button_text="🔄 بروزرسانی مبدأ"),
        Button(id="buy", type=ButtonTypeEnum.SIMPLE, button_text="💳 خرید اشتراک"),
    ]),
    KeypadRow(buttons=[
        Button(id="listplans", type=ButtonTypeEnum.SIMPLE, button_text="📅 برنامه‌ریزی"),
        Button(id="logs", type=ButtonTypeEnum.SIMPLE, button_text="📊 گزارش‌ها"),
    ]),
    KeypadRow(buttons=[
        Button(id="help", type=ButtonTypeEnum.SIMPLE, button_text="❓ راهنما"),
    ]),
])


def load_offset() -> Optional[str]:
    try:
        if os.path.exists(OFFSET_FILE):
            with open(OFFSET_FILE) as f:
                return json.load(f).get("offset_id")
    except Exception:
        pass
    return None


def save_offset(offset_id: str) -> None:
    try:
        with open(OFFSET_FILE, "w") as f:
            json.dump({"offset_id": offset_id}, f)
    except Exception:
        pass


class RubikaClient:
    """Wrapper around rubpy BotClient for sending/receiving messages."""

    def __init__(self, token: str):
        self.token = token
        self._bot = BotClient(token=token)
        self.offset_id: Optional[str] = load_offset()
        if self.offset_id:
            logger.info(f"Resumed from saved offset: {self.offset_id}")

    async def send_message(self, user_id: str, text: str, with_keypad: bool = False) -> bool:
        try:
            kwargs: Dict[str, Any] = {
                "chat_id": str(user_id),
                "text": text,
            }
            if with_keypad:
                kwargs["chat_keypad"] = MAIN_KEYPAD
                kwargs["chat_keypad_type"] = ChatKeypadTypeEnum.NEW

            await self._bot.send_message(**kwargs)
            logger.info(f"Message sent to {user_id}: {text[:50]}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}: {e}")
            return False

    async def get_updates(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get normalized text message updates."""
        try:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=15)
            url = f"https://botapi.rubika.ir/v3/{self.token}/getUpdates"
            payload: Dict[str, Any] = {"limit": limit}
            if self.offset_id:
                payload["offset_id"] = self.offset_id

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    data = await response.json(content_type=None)

            body = data.get("data", data)
            updates = body.get("updates") or []
            next_offset = body.get("next_offset_id")
            if next_offset:
                self.offset_id = str(next_offset)
                save_offset(self.offset_id)

            return self._normalize(updates)
        except Exception as e:
            logger.warning(f"Failed to get updates: {e}")
            return []

    @staticmethod
    def _normalize(updates: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        messages = []
        for update in updates:
            update_type = update.get("type", "")
            chat_id = update.get("chat_id")
            if not chat_id:
                continue

            if update_type == "StartedBot":
                messages.append({"user_id": str(chat_id), "text": "/start"})

            elif update_type == "NewMessage":
                msg = update.get("new_message") or {}
                text = (msg.get("text") or "").strip()
                # forwarded message from a channel
                forwarded = msg.get("forwarded_from") or {}
                if not text:
                    aux = msg.get("aux_data") or {}
                    btn_id = aux.get("button_id", "")
                    if btn_id:
                        text = f"/{btn_id}"
                if text:
                    entry: Dict[str, str] = {"user_id": str(chat_id), "text": text}
                    if forwarded:
                        entry["forwarded_from_chat"] = str(forwarded.get("chat_id") or forwarded.get("object_guid", ""))
                        entry["forwarded_message_id"] = str(msg.get("message_id", ""))
                    messages.append(entry)

            else:
                logger.info(f"Unknown update type: {update_type} | raw: {update}")

        return messages


class RufifoBot:
    """Main bot class."""

    def __init__(self, token: str):
        self.token = token
        self.background_tasks = []
        self.running = False
        self.client: Optional[RubikaClient] = None
        logger.info(f"Bot initialized with token: {token[:20]}...")

    async def start(self) -> None:
        logger.info("Starting Rufifo bot...")
        await init_db()

        self.client = RubikaClient(self.token)
        logger.info("Rubika client initialized")
        self.running = True

        # Start user client for channel reading (if session file exists)
        from src.integrations.rubika import RubikaUserClient
        self.user_client = RubikaUserClient(session_name=USER_SESSION_NAME)
        try:
            await self.user_client.start()
            logger.info("Rubika user client started — channel monitoring active")
            self.background_tasks.append(asyncio.create_task(self._channel_monitor_loop()))
        except Exception as e:
            logger.warning(f"User client failed to start (run setup_session.py first): {e}")
            self.user_client = None

        self.background_tasks.append(asyncio.create_task(self._polling_loop()))
        self.background_tasks.append(asyncio.create_task(self._trial_reminder_loop()))

        logger.info("Bot started and listening for messages")
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    async def stop(self) -> None:
        logger.info("Stopping bot...")
        self.running = False
        for task in self.background_tasks:
            task.cancel()
        if self.user_client:
            await self.user_client.stop()
        await close_db()

    async def _polling_loop(self) -> None:
        from src.bot.handlers import route_message
        logger.info("Message polling loop started")
        consecutive_errors = 0

        while self.running:
            try:
                await asyncio.sleep(3)
                updates = await self.client.get_updates()
                consecutive_errors = 0

                for update in updates:
                    user_id = update.get("user_id")
                    text = update.get("text", "")
                    has_forward = bool(update.get("forwarded_from_chat"))
                    if user_id and (text or has_forward):
                        logger.info(f"New message from {user_id}: {text[:80]}")
                        try:
                            await route_message(self.client, user_id, update)
                        except Exception as e:
                            logger.error(f"Error handling message: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                consecutive_errors += 1
                wait = min(5 * consecutive_errors, 60)
                logger.error(f"Polling error ({consecutive_errors}): {e}")
                await asyncio.sleep(wait)

    async def send_message(self, user_id: str, text: str, with_keypad: bool = False) -> bool:
        if not self.client:
            return False
        return await self.client.send_message(user_id, text, with_keypad=with_keypad)

    async def _channel_monitor_loop(self) -> None:
        """Poll source channels for new posts and add them to post_queue."""
        from src.database import fetch
        from datetime import datetime
        logger.info("Channel monitor loop started")

        while self.running:
            try:
                await asyncio.sleep(CHANNEL_POLL_INTERVAL)

                # Get all active routes with their channel GUIDs
                routes = await fetch(
                    "SELECT id, user_id, source_channel_id, source_guid FROM routes WHERE is_active = true"
                )

                for route in routes:
                    route_id = route["id"]
                    source_input = route["source_channel_id"]
                    cached_guid = route.get("source_guid")

                    try:
                        # Resolve channel to object_guid if not cached
                        object_guid = cached_guid
                        if not object_guid:
                            object_guid = await self.user_client.resolve_channel(source_input)
                            if object_guid:
                                # Cache the resolved guid in DB
                                from src.database import execute
                                await execute(
                                    "UPDATE routes SET source_guid = $1 WHERE id = $2",
                                    object_guid, route_id
                                )
                            else:
                                logger.warning(f"Route {route_id}: could not resolve channel '{source_input}'")
                                continue

                        # Get last seen message_id for this route
                        last = await fetch(
                            "SELECT MAX(message_id_in_source::bigint) as max_id FROM post_queue WHERE route_id = $1",
                            route_id
                        )
                        min_id = str(last[0]["max_id"]) if last and last[0]["max_id"] else None

                        # Fetch new messages
                        messages = await self.user_client.get_channel_messages(
                            object_guid=object_guid,
                            min_id=min_id,
                            limit=50,
                        )

                        inserted = 0
                        from src.database import execute as db_execute
                        for msg in messages:
                            mid = msg["message_id"]
                            ts = datetime.fromtimestamp(msg["time"]) if msg["time"] else datetime.now()
                            try:
                                await db_execute(
                                    "INSERT INTO post_queue (route_id, message_id_in_source, source_date, status) "
                                    "VALUES ($1, $2, $3, 'pending') ON CONFLICT DO NOTHING",
                                    route_id, mid, ts,
                                )
                                inserted += 1
                            except Exception:
                                pass

                        if inserted:
                            logger.info(f"Route {route_id}: {inserted} new posts added from {object_guid}")

                    except Exception as e:
                        logger.error(f"Monitor error for route {route_id}: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Channel monitor loop error: {e}")
                await asyncio.sleep(30)

    async def _trial_reminder_loop(self) -> None:
        from src.database import fetch
        from datetime import datetime
        logger.info("Trial reminder loop started")

        while self.running:
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
                            (user["trial_end_at"] - datetime.now()).total_seconds() / 3600
                        )
                        await self.send_message(
                            user["user_id"],
                            f"⏰ تریال شما {hours_left:.0f} ساعت دیگر تمام می‌شود.\n💳 /buy برای خرید اشتراک"
                        )
                    except Exception as e:
                        logger.error(f"Reminder error for {user['user_id']}: {e}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Trial reminder loop error: {e}")
                await asyncio.sleep(60)


_bot_instance: Optional["RufifoBot"] = None


def _get_user_client():
    """Return the running bot's user client (for use in command handlers)."""
    if _bot_instance and _bot_instance.user_client:
        return _bot_instance.user_client
    return None


async def main() -> None:
    global _bot_instance
    bot = RufifoBot(BOT_TOKEN)
    _bot_instance = bot
    try:
        await bot.start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
