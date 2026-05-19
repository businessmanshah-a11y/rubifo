import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from rubpy import BotClient
from rubpy.bot.models import Keypad, KeypadRow, Button
from rubpy.bot.enums import ChatKeypadTypeEnum, ButtonTypeEnum
from src.database import init_db, close_db
from src.logger import logger
from src.config import BOT_TOKEN

OFFSET_FILE = "logs/bot_offset.json"

_OFFSET_KEY = "offset_id"


async def _load_offset_db() -> Optional[str]:
    try:
        from src.database import pool
        row = await pool.fetchrow(
            "SELECT value FROM bot_state WHERE key = $1", _OFFSET_KEY
        )
        if row and row["value"]:
            return row["value"]
    except Exception:
        pass
    return None


async def _save_offset_db(offset_id: str) -> None:
    try:
        from src.database import pool
        await pool.execute(
            "INSERT INTO bot_state (key, value) VALUES ($1, $2) "
            "ON CONFLICT (key) DO UPDATE SET value = $2",
            _OFFSET_KEY, offset_id,
        )
    except Exception:
        pass


MAIN_KEYPAD = Keypad(rows=[
    KeypadRow(buttons=[
        Button(id="mysources", type=ButtonTypeEnum.SIMPLE, button_text="📦 سورس‌های من"),
        Button(id="my_destinations", type=ButtonTypeEnum.SIMPLE, button_text="📍 کانال‌های من"),
        Button(id="listroutes", type=ButtonTypeEnum.SIMPLE, button_text="📋 مسیرهای من"),
    ]),
    KeypadRow(buttons=[
        Button(id="listplans", type=ButtonTypeEnum.SIMPLE, button_text="📅 پلن‌های من"),
        Button(id="calendar", type=ButtonTypeEnum.SIMPLE, button_text="📊 تقویم محتوایی"),
        Button(id="subscription_status", type=ButtonTypeEnum.SIMPLE, button_text="💳 اشتراک"),
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

    async def send_message(
        self,
        user_id: str,
        text: str,
        with_keypad: bool = False,
        keypad=None,
    ) -> bool:
        """Send a text message to a user.

        Args:
            user_id: Rubika user ID
            text: Message text
            with_keypad: If True, attach the main persistent keypad
            keypad: Custom Keypad object to attach (overrides with_keypad)
        """
        try:
            kwargs: Dict[str, Any] = {"chat_id": str(user_id), "text": text}
            if keypad is not None:
                kwargs["chat_keypad"] = keypad
                kwargs["chat_keypad_type"] = ChatKeypadTypeEnum.NEW
            elif with_keypad:
                kwargs["chat_keypad"] = MAIN_KEYPAD
                kwargs["chat_keypad_type"] = ChatKeypadTypeEnum.NEW
            await self._bot.send_message(**kwargs)
            logger.info(f"Message sent to {user_id}: {text[:50]}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}: {e}")
            return False

    async def send_file(self, chat_id: str, file_id: str, file_type: str = "File", caption: str = "") -> bool:
        try:
            kwargs: Dict[str, Any] = {"chat_id": str(chat_id), "file_id": file_id, "type": file_type}
            if caption:
                kwargs["text"] = caption  # rubpy uses 'text' not 'caption'
            await self._bot.send_file(**kwargs)
            return True
        except Exception as e:
            logger.error(f"Failed to send_file to {chat_id}: {e}")
            raise

    async def send_voice(self, chat_id: str, file_id: str) -> bool:
        try:
            await self._bot.send_voice(chat_id=str(chat_id), file_id=file_id)
            return True
        except Exception as e:
            logger.error(f"Failed to send_voice to {chat_id}: {e}")
            raise

    async def send_music(self, chat_id: str, file_id: str) -> bool:
        try:
            await self._bot.send_music(chat_id=str(chat_id), file_id=file_id)
            return True
        except Exception as e:
            logger.error(f"Failed to send_music to {chat_id}: {e}")
            raise

    async def forward_hidden(self, from_chat_id: str, message_id: str, to_chat_id: str) -> bool:
        """Forward a message without 'forwarded from' attribution (hide_sender_name=True)."""
        try:
            await self._bot._make_request("forwardMessage", {
                "from_chat_id": str(from_chat_id),
                "message_id": str(message_id),
                "to_chat_id": str(to_chat_id),
                "hide_sender_name": True,
            })
            logger.info(f"Hidden forward msg {message_id} → {to_chat_id}")
            return True
        except Exception as e:
            logger.error(f"forward_hidden failed: {e}")
            raise

    async def reupload_media(self, file_id: str, message_type: str) -> str:
        """Download a file from Rubika CDN and re-upload via bot upload endpoint.

        Returns a new bot-owned file_id usable for sendFile to channels.
        Raises on failure.
        """
        import os
        import tempfile

        _type_map = {
            "photo": ("Image", ".jpg"),
            "video": ("Video", ".mp4"),
            "voice": ("File", ".ogg"),
            "music": ("File", ".mp3"),
            "gif":   ("Gif",  ".gif"),
        }
        rubpy_type, ext = _type_map.get(message_type, ("File", ".bin"))

        fd, temp_path = tempfile.mkstemp(suffix=ext)
        os.close(fd)
        try:
            import aiohttp
            logger.info(f"[REUPLOAD] Step 1: getFile for file_id={file_id[:20]}...")
            cdn_url = await self._bot.get_file(file_id)
            logger.info(f"[REUPLOAD] Step 2: CDN url={cdn_url[:80]}")

            dl_timeout = aiohttp.ClientTimeout(total=30)
            headers = {"User-Agent": "Mozilla/5.0 (compatible; RubikaBot/1.0)", "Referer": "https://rubika.ir/"}
            last_err = None
            for attempt in range(3):
                try:
                    async with aiohttp.ClientSession(timeout=dl_timeout) as session:
                        async with session.get(cdn_url, headers=headers) as resp:
                            if resp.status != 200:
                                raise Exception(f"Failed to download file: {resp.status}")
                            file_bytes = await resp.read()
                    break
                except Exception as e:
                    last_err = e
                    logger.warning(f"[REUPLOAD] Download attempt {attempt+1} failed: {e}")
                    await asyncio.sleep(2)
            else:
                raise last_err
            logger.info(f"[REUPLOAD] Step 3: Downloaded {len(file_bytes)} bytes OK")

            with open(temp_path, "wb") as f:
                f.write(file_bytes)

            logger.info(f"[REUPLOAD] Step 4: Requesting upload slot ({rubpy_type})...")
            upload_url = await self._bot.request_send_file(rubpy_type)
            logger.info(f"[REUPLOAD] Step 5: Uploading to bot CDN...")
            new_fid = await self._bot.upload_file(upload_url, f"media{ext}", temp_path)
            logger.info(f"[REUPLOAD] Step 6: SUCCESS — new file_id={new_fid[:20]}...")
            return new_fid
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass

    async def drain_old_updates(self) -> None:
        """Skip all pending messages on fresh start — just fast-forward the offset."""
        import aiohttp
        url = f"https://botapi.rubika.ir/v3/{self.token}/getUpdates"
        timeout = aiohttp.ClientTimeout(total=15)
        drained = 0
        try:
            while True:
                payload: Dict[str, Any] = {"limit": 50}
                if self.offset_id:
                    payload["offset_id"] = self.offset_id
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, json=payload) as resp:
                        data = await resp.json(content_type=None)
                body = data.get("data", data)
                updates = body.get("updates") or []
                next_offset = body.get("next_offset_id")
                drained += len(updates)
                if next_offset:
                    self.offset_id = str(next_offset)
                if not updates:
                    break
            if self.offset_id:
                save_offset(self.offset_id)
                await _save_offset_db(self.offset_id)
            logger.info(f"Drained {drained} old updates. Offset: {self.offset_id}")
        except Exception as e:
            logger.warning(f"drain_old_updates failed: {e}")

    async def get_updates(self, limit: int = 50) -> List[Dict[str, Any]]:
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
                await _save_offset_db(self.offset_id)

            return self._normalize(updates)
        except Exception as e:
            logger.warning(f"Failed to get updates: {e}")
            return []

    @staticmethod
    def _normalize(updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        started_bot_users: set = set()
        messages = []

        for update in updates:
            update_type = update.get("type", "")
            chat_id = update.get("chat_id")
            if not chat_id:
                continue

            if update_type == "StartedBot":
                started_bot_users.add(str(chat_id))

            elif update_type == "NewMessage":
                msg = update.get("new_message") or {}
                text = (msg.get("text") or "").strip()

                # Button press via aux_data
                if not text:
                    aux = msg.get("aux_data") or {}
                    btn_id = aux.get("button_id", "")
                    if btn_id:
                        text = f"/{btn_id}"

                # Always include the full message for media handling
                entry: Dict[str, Any] = {
                    "user_id": str(chat_id),
                    "text": text,
                    "new_message": msg,
                }

                # Forwarded message info
                forwarded = msg.get("forwarded_from") or {}
                if forwarded:
                    entry["forwarded_from_chat"] = str(
                        forwarded.get("chat_id") or forwarded.get("object_guid", "")
                    )
                    entry["forwarded_message_id"] = str(msg.get("message_id", ""))

                if text or msg.get("file") or msg.get("sticker") or forwarded:
                    # If Rubika sent StartedBot + NewMessage /start together, skip duplicate
                    if text == "/start" and str(chat_id) in started_bot_users:
                        started_bot_users.discard(str(chat_id))
                    messages.append(entry)

            else:
                logger.info(f"Unknown update type: {update_type} | raw: {update}")

        # Add /start for users who had StartedBot but no NewMessage /start
        for uid in started_bot_users:
            messages.insert(0, {"user_id": uid, "text": "/start"})

        return messages

    @staticmethod
    def normalize_updates(updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compatibility helper for older Bot API update shapes used in tests."""
        normalized = []
        for update in updates:
            message = update.get("message") or {}
            text = (message.get("text") or "").strip()
            chat_id = message.get("chat_id")
            if chat_id and text:
                normalized.append({"user_id": str(chat_id), "text": text})
        if normalized:
            return normalized
        return RubikaClient._normalize(updates)


RubikaBotApiClient = RubikaClient


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
        self.running = True

        self.background_tasks.append(asyncio.create_task(self._polling_loop()))
        self.background_tasks.append(asyncio.create_task(self._trial_reminder_loop()))
        self.background_tasks.append(asyncio.create_task(self._execution_loop()))

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
        await close_db()

    async def _polling_loop(self) -> None:
        from src.bot.handlers import route_message
        logger.info("Message polling loop started")

        # Load persisted offset from DB (survives restarts/redeploys)
        db_offset = await _load_offset_db()
        if db_offset:
            self.client.offset_id = db_offset
            logger.info(f"Offset restored from DB: {db_offset}")
        else:
            # Fresh start — skip all queued messages to avoid processing history
            logger.info("No saved offset — draining old updates to start fresh...")
            await self.client.drain_old_updates()

        consecutive_errors = 0

        while self.running:
            try:
                await asyncio.sleep(3)
                updates = await self.client.get_updates()
                consecutive_errors = 0

                for update in updates:
                    user_id = update.get("user_id")
                    text = update.get("text", "")
                    has_media = bool(
                        (update.get("new_message") or {}).get("file") or
                        (update.get("new_message") or {}).get("sticker")
                    )
                    if user_id and (text or has_media):
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

    async def _execution_loop(self) -> None:
        """Fire scheduled posts to target channels."""
        from src.core.execution_engine import ExecutionEngine
        from src.database import pool
        logger.info("Execution loop started")
        engine = ExecutionEngine(pool, self.client)
        await engine.start()

    async def send_message(self, user_id: str, text: str, with_keypad: bool = False) -> bool:
        if not self.client:
            return False
        return await self.client.send_message(user_id, text, with_keypad=with_keypad)

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


_bot_instance: Optional[RufifoBot] = None


def _get_bot_client():
    """Return the running bot's RubikaClient for use in other modules."""
    if _bot_instance and _bot_instance.client:
        return _bot_instance.client
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
