import asyncio
import os
import tempfile
from datetime import datetime
from typing import Optional, Tuple
from src.logger import logger

# Keywords that indicate a file_id has expired or is invalid
FILE_ID_ERROR_KEYWORDS = ("not_found", "invalid", "file_id", "expired", "access", "no such")

# Maps message_type → (rubpy upload type, temp file extension)
_FILE_TYPE_MAP = {
    "photo": ("Image", ".jpg"),
    "video": ("Video", ".mp4"),
    "voice": ("File", ".ogg"),
    "music": ("File", ".mp3"),
    "gif":   ("Gif",  ".gif"),
}


class ExecutionEngine:
    """Schedule-based execution engine: dequeues source posts and sends to target channels."""

    def __init__(self, db, bot_client):
        self.db = db
        self.client = bot_client
        self.is_running = False

    async def start(self) -> None:
        from src.core.schedule_service import ScheduleService
        from src.core.queue_service import QueueService
        self.is_running = True
        schedule_service = ScheduleService(self.db)
        queue_service = QueueService(self.db)
        logger.info("Execution engine started")
        try:
            while self.is_running:
                await self._check_and_execute(schedule_service, queue_service)
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Execution engine fatal error: {e}")
            self.is_running = False

    async def stop(self) -> None:
        self.is_running = False
        logger.info("Execution engine stopped")

    async def _check_and_execute(self, schedule_service, queue_service) -> None:
        try:
            schedules = await self.db.fetch(
                "SELECT * FROM schedules WHERE is_active = true AND next_run <= NOW() ORDER BY next_run ASC"
            )
            for sched_row in schedules:
                from src.models.schedule import Schedule
                schedule = Schedule(**dict(sched_row))
                try:
                    executed = await self._execute_schedule(schedule, schedule_service, queue_service)
                    if executed:
                        times = None
                        if schedule.schedule_type == "daily_count":
                            raw_times = await schedule_service.get_schedule_times(schedule.id)
                            times = [(t.hour, t.minute) for t in raw_times]
                        next_run = await schedule_service._calculate_next_run(
                            schedule.schedule_type,
                            schedule.interval_minutes,
                            schedule.daily_count,
                            times,
                        )
                        await schedule_service.update_next_run(schedule.id, next_run)
                        logger.info(f"Schedule {schedule.id} next_run → {next_run}")
                except Exception as e:
                    logger.error(f"Error executing schedule {schedule.id}: {e}")
        except Exception as e:
            logger.error(f"Error checking schedules: {e}")

    async def _execute_schedule(self, schedule, schedule_service, queue_service) -> bool:
        route = await self.db.fetchrow("SELECT * FROM routes WHERE id = $1", schedule.route_id)
        if not route or not route["is_active"]:
            return False

        target_channel_id = route.get("target_channel_id")
        if not target_channel_id:
            logger.warning(f"Route {schedule.route_id} has no target_channel_id")
            return False

        # Get next pending item; populate queue from source if empty
        queue_item = await queue_service.get_next_pending(schedule.route_id)
        if not queue_item:
            filled = await self._fill_queue_from_source(schedule.route_id, dict(route))
            if filled:
                queue_item = await queue_service.get_next_pending(schedule.route_id)
            if not queue_item:
                logger.debug(f"No pending posts for route {schedule.route_id}")
                return True

        queue_id = queue_item["id"] if isinstance(queue_item, dict) else queue_item.id
        source_post_id = (queue_item.get("source_post_id") if isinstance(queue_item, dict)
                          else getattr(queue_item, "source_post_id", None))

        if not source_post_id:
            logger.warning(f"Queue item {queue_id} has no source_post_id — skipping")
            await queue_service.mark_failed(queue_id, "missing source_post_id")
            return False

        # Load source post
        from src.core.source_service import SourceService
        source_service = SourceService(self.db)
        post = await source_service.get_post(source_post_id)

        if not post:
            logger.warning(f"Source post {source_post_id} not found — skipping")
            await queue_service.mark_failed(queue_id, "source_post_not_found")
            return False

        has_message_id = bool(post.raw_data and isinstance(post.raw_data, dict) and post.raw_data.get("message_id"))
        if not post.file_id_valid and not has_message_id:
            logger.warning(f"Source post {source_post_id} has no valid file_id or message_id — skipping")
            await queue_service.mark_failed(queue_id, "file_id_invalid")
            return False

        guid_user_id = route.get("user_id")
        route_id = route.get("id")

        # Rate limiting
        from src.config import API_RATE_LIMIT_DELAY
        await asyncio.sleep(API_RATE_LIMIT_DELAY)

        success, error = await self._send_source_post(post, target_channel_id, user_guid=guid_user_id)

        if success:
            await queue_service.mark_sent(queue_id)
            logger.info(f"Post {source_post_id} sent to {target_channel_id} (queue #{queue_id})")
            return True
        else:
            retry_count = (queue_item.get("retry_count", 0) if isinstance(queue_item, dict)
                           else getattr(queue_item, "retry_count", 0))

            if self._is_file_id_error(error):
                # Look up integer PK for file_id_errors table (BIGINT column)
                user_row = await self.db.fetchrow(
                    "SELECT id FROM users WHERE user_id = $1", str(guid_user_id)
                )
                db_user_id = user_row["id"] if user_row else None
                await source_service.mark_file_id_invalid(source_post_id, error, db_user_id, route_id)
                # Alert the user
                source = await source_service.get_source(post.source_id)
                source_name = source.name if source else str(post.source_id)
                try:
                    await self.client.send_message(
                        str(guid_user_id),
                        f"⚠️ پست #{source_post_id} از سورس «{source_name}» منقضی شده.\n"
                        f"لطفاً آن را جایگزین کنید:\n/addpost {post.source_id}"
                    )
                except Exception:
                    pass
                await queue_service.mark_failed(queue_id, f"file_id_expired: {error[:100]}")
                logger.warning(f"Post {source_post_id} file_id expired, user {guid_user_id} alerted")
            else:
                await queue_service.mark_failed(queue_id, error[:200])
                if retry_count >= 3:
                    logger.error(f"Post {source_post_id} failed permanently: {error[:100]}")

            return False

    async def _fill_queue_from_source(self, route_id: int, route: dict) -> bool:
        """Populate post_queue from source_posts when queue is empty."""
        source_id = route.get("source_id")
        if not source_id:
            logger.warning(f"Route {route_id} has no source_id — cannot fill queue")
            return False

        posts = await self.db.fetch(
            "SELECT id FROM source_posts WHERE source_id = $1 "
            "AND (file_id_valid = true OR raw_data->>'message_id' IS NOT NULL) "
            "ORDER BY order_index ASC",
            source_id,
        )
        if not posts:
            logger.warning(f"Source {source_id} has no valid posts for route {route_id}")
            return False

        for post in posts:
            await self.db.execute(
                "INSERT INTO post_queue (route_id, source_post_id, status) "
                "VALUES ($1, $2, 'pending')",
                route_id,
                post["id"],
            )

        logger.info(f"Filled queue for route {route_id} with {len(posts)} posts from source {source_id}")
        return True

    async def _do_send(self, message_type: str, file_id: Optional[str], target: str,
                       cap: str, text: str) -> None:
        """Dispatch a single send call based on message type."""
        t = message_type
        if t == "text":
            await self.client.send_message(target, text or "")
        elif t == "photo":
            await self.client.send_file(target, file_id=file_id, file_type="Image", caption=cap)
        elif t == "video":
            await self.client.send_file(target, file_id=file_id, file_type="Video", caption=cap)
        elif t == "voice":
            await self.client.send_voice(target, file_id=file_id)
        elif t == "music":
            await self.client.send_music(target, file_id=file_id)
        elif t == "gif":
            await self.client.send_file(target, file_id=file_id, file_type="Gif")
        else:
            await self.client.send_file(target, file_id=file_id, file_type="File", caption=cap)

    async def _reupload_file(self, old_file_id: str, message_type: str, post_id: int) -> str:
        """Download a file by file_id and re-upload it via the bot, returning a new valid file_id."""
        rubpy_type, ext = _FILE_TYPE_MAP.get(message_type, ("File", ".bin"))

        fd, temp_path = tempfile.mkstemp(suffix=ext)
        os.close(fd)

        try:
            import aiohttp
            cdn_url = await self.client._bot.get_file(old_file_id)
            dl_timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=dl_timeout) as session:
                async with session.get(str(cdn_url)) as resp:
                    if resp.status != 200:
                        raise Exception(f"Failed to download file: {resp.status}")
                    file_bytes = await resp.read()
            with open(temp_path, "wb") as f:
                f.write(file_bytes)
            upload_url = await self.client._bot.request_send_file(rubpy_type)
            new_fid = await self.client._bot.upload_file(
                upload_url, f"media{ext}", temp_path
            )
            await self.db.execute(
                "UPDATE source_posts SET file_id = $1 WHERE id = $2",
                new_fid, post_id,
            )
            logger.info(f"Post {post_id} file re-uploaded successfully")
            return new_fid
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass

    async def _send_source_post(self, post, target_channel_id: str,
                                user_guid: str = None) -> Tuple[bool, str]:
        """Send a source post to a target channel.

        Primary path: sendFile with bot-owned file_id (no attribution, created at collection time).
        Fallback: re-upload on demand (if file_id is original/expired).
        Last resort: hidden forward (shows sender name — avoided when possible).
        """
        t = post.message_type
        fid = post.file_id
        cap = post.caption or post.text_content or ""
        text = post.text_content or ""

        # Primary: direct sendFile with stored file_id (bot-owned = no attribution)
        if fid:
            try:
                logger.info(f"[SEND] Trying sendFile for post {post.id} → {target_channel_id}")
                await self._do_send(t, fid, target_channel_id, cap, text)
                logger.info(f"[SEND] sendFile SUCCESS for post {post.id}")
                return True, ""
            except Exception as e:
                orig_error = str(e)
                logger.warning(f"[SEND] sendFile failed for post {post.id}: {orig_error[:80]}")

            # If file_id invalid: try re-upload (download from CDN + re-upload)
            if self._is_file_id_error(orig_error):
                logger.info(f"[SEND] file_id invalid — attempting re-upload for post {post.id}")
                try:
                    new_fid = await self._reupload_file(fid, t, post.id)
                    await self._do_send(t, new_fid, target_channel_id, cap, text)
                    logger.info(f"[SEND] re-upload + sendFile SUCCESS for post {post.id}")
                    return True, ""
                except Exception as e2:
                    logger.warning(f"[SEND] re-upload also failed for post {post.id}: {e2}")
                    orig_error = str(e2)

        elif t == "text":
            try:
                await self._do_send(t, None, target_channel_id, cap, text)
                return True, ""
            except Exception as e:
                return False, str(e)

        # Last resort: hidden forward (will show sender name — only if no other option)
        dm_msg_id = None
        if post.raw_data and isinstance(post.raw_data, dict):
            dm_msg_id = post.raw_data.get("message_id")

        if dm_msg_id and user_guid:
            logger.warning(f"[SEND] Falling back to forward_hidden for post {post.id} (will show sender)")
            try:
                await self.client.forward_hidden(user_guid, dm_msg_id, target_channel_id)
                return True, ""
            except Exception as e:
                logger.warning(f"[SEND] forward_hidden also failed for post {post.id}: {e}")
                return False, str(e)

        return False, orig_error if fid else "no_file_id"

    @staticmethod
    def _is_file_id_error(error: str) -> bool:
        low = error.lower()
        return any(kw in low for kw in FILE_ID_ERROR_KEYWORDS)

    async def get_execution_stats(self) -> dict:
        try:
            sent = await self.db.fetchrow("SELECT COUNT(*) as c FROM post_queue WHERE status='sent'")
            failed = await self.db.fetchrow("SELECT COUNT(*) as c FROM post_queue WHERE status='failed'")
            pending = await self.db.fetchrow("SELECT COUNT(*) as c FROM post_queue WHERE status='pending'")
            return {
                "status": "running" if self.is_running else "stopped",
                "sent": sent["c"] if sent else 0,
                "failed": failed["c"] if failed else 0,
                "pending": pending["c"] if pending else 0,
                "timestamp": datetime.now(),
            }
        except Exception as e:
            return {"error": str(e)}


async def create_execution_engine(db, bot_client) -> ExecutionEngine:
    return ExecutionEngine(db, bot_client)
