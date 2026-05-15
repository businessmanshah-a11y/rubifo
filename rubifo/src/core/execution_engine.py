import asyncio
from datetime import datetime
from typing import Optional, Tuple
from src.logger import logger

# Keywords that indicate a file_id has expired or is invalid
FILE_ID_ERROR_KEYWORDS = ("not_found", "invalid", "file_id", "expired", "access", "no such")


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

        # Get next pending item (ordered by source_date/order)
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

        if not post.file_id_valid:
            logger.warning(f"Source post {source_post_id} has invalid file_id — skipping")
            await queue_service.mark_failed(queue_id, "file_id_invalid")
            return False

        # Rate limiting
        from src.config import API_RATE_LIMIT_DELAY
        await asyncio.sleep(API_RATE_LIMIT_DELAY)

        success, error = await self._send_source_post(post, target_channel_id)

        if success:
            await queue_service.mark_sent(queue_id)
            logger.info(f"Post {source_post_id} sent to {target_channel_id} (queue #{queue_id})")
            return True
        else:
            # Check if it's a file_id expiry error
            retry_count = (queue_item.get("retry_count", 0) if isinstance(queue_item, dict)
                           else getattr(queue_item, "retry_count", 0))
            user_id = route.get("user_id")
            route_id = route.get("id")

            if self._is_file_id_error(error):
                await source_service.mark_file_id_invalid(source_post_id, error, user_id, route_id)
                # Alert the user
                source = await source_service.get_source(post.source_id)
                source_name = source.name if source else str(post.source_id)
                try:
                    await self.client.send_message(
                        str(user_id),
                        f"⚠️ پست #{source_post_id} از سورس «{source_name}» منقضی شده.\n"
                        f"لطفاً آن را جایگزین کنید:\n/addpost {post.source_id}"
                    )
                except Exception:
                    pass
                await queue_service.mark_failed(queue_id, f"file_id_expired: {error[:100]}")
                logger.warning(f"Post {source_post_id} file_id expired, user {user_id} alerted")
            else:
                await queue_service.mark_failed(queue_id, error[:200])
                if retry_count >= 3:
                    logger.error(f"Post {source_post_id} failed permanently: {error[:100]}")

            return False

    async def _send_source_post(self, post, target_channel_id: str) -> Tuple[bool, str]:
        """Send a source post to a target channel using the appropriate method."""
        try:
            t = post.message_type
            fid = post.file_id
            cap = post.caption or post.text_content or ""

            if t == "text":
                await self.client.send_message(target_channel_id, post.text_content or "")
            elif t == "photo":
                await self.client.send_file(target_channel_id, file_id=fid, file_type="Image", caption=cap)
            elif t == "video":
                await self.client.send_file(target_channel_id, file_id=fid, file_type="Video", caption=cap)
            elif t == "voice":
                await self.client.send_voice(target_channel_id, file_id=fid)
            elif t == "music":
                await self.client.send_music(target_channel_id, file_id=fid)
            elif t == "gif":
                await self.client.send_file(target_channel_id, file_id=fid, file_type="Gif")
            else:  # file / document
                await self.client.send_file(target_channel_id, file_id=fid, file_type="File", caption=cap)

            return True, ""
        except Exception as e:
            return False, str(e)

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
