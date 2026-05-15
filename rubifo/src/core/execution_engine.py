import asyncio
from datetime import datetime, timedelta
from typing import Optional
from src.logger import logger
from src.models.post_queue import PostQueueItem


class ExecutionEngine:
    """Main execution engine for schedule-based message forwarding."""

    def __init__(self, db, bot_client):
        self.db = db
        self.client = bot_client
        self.is_running = False

    async def start(self) -> None:
        """Start the execution engine main loop."""
        from src.core.schedule_service import ScheduleService
        from src.core.queue_service import QueueService

        self.is_running = True
        schedule_service = ScheduleService(self.db)
        queue_service = QueueService(self.db)

        logger.info("Execution engine started")

        try:
            while self.is_running:
                await self._check_and_execute(schedule_service, queue_service)
                await asyncio.sleep(30)  # Check every 30 seconds

        except Exception as e:
            logger.error(f"Execution engine fatal error: {e}")
            self.is_running = False

    async def stop(self) -> None:
        """Stop the execution engine."""
        self.is_running = False
        logger.info("Execution engine stopped")

    async def _check_and_execute(
        self, schedule_service, queue_service
    ) -> None:
        """Check for schedules due and execute them."""
        try:
            # Get all active schedules due for execution
            schedules = await self.db.fetch(
                """
                SELECT * FROM schedules
                WHERE is_active = true AND next_run <= NOW()
                ORDER BY next_run ASC
                """
            )

            for schedule_row in schedules:
                from src.models.schedule import Schedule

                schedule = Schedule(**dict(schedule_row))

                try:
                    executed = await self._execute_schedule(
                        schedule, schedule_service, queue_service
                    )

                    if executed:
                        # Calculate next_run for this schedule
                        schedule_type = schedule.schedule_type
                        times = None

                        if schedule_type == "daily_count":
                            times = await schedule_service.get_schedule_times(
                                schedule.id
                            )
                            times = [(t.hour, t.minute) for t in times]

                        next_run = await schedule_service._calculate_next_run(
                            schedule_type,
                            schedule.interval_minutes,
                            schedule.daily_count,
                            times,
                        )

                        await schedule_service.update_next_run(schedule.id, next_run)
                        logger.info(
                            f"Schedule {schedule.id} next_run set to {next_run}"
                        )

                except Exception as e:
                    logger.error(f"Error executing schedule {schedule.id}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error checking schedules: {e}")

    async def _execute_schedule(
        self, schedule, schedule_service, queue_service
    ) -> bool:
        """Execute one schedule's message forwarding.

        Args:
            schedule: Schedule instance
            schedule_service: ScheduleService instance
            queue_service: QueueService instance

        Returns:
            True if schedule executed, False otherwise
        """
        try:
            # Get the route
            route = await self.db.fetchrow(
                "SELECT * FROM routes WHERE id = $1", schedule.route_id
            )

            if not route:
                logger.warning(f"Route {schedule.route_id} not found for schedule {schedule.id}")
                return False

            if not route["is_active"]:
                logger.debug(f"Route {schedule.route_id} is inactive")
                return False

            # Get next pending message from queue
            next_post = await queue_service.get_next_pending(schedule.route_id)

            if not next_post:
                logger.debug(f"No pending posts in route {schedule.route_id}")
                return True  # Still "executed" (no messages to send)

            post_item = PostQueueItem(**next_post)

            # Forward the message
            success, error_msg = await self._forward_message(
                route["source_channel_id"],
                route["target_channel_id"],
                post_item.message_id_in_source,
            )

            if success:
                await queue_service.mark_sent(post_item.id)
                logger.info(
                    f"Message {post_item.message_id_in_source} sent from route {schedule.route_id}"
                )
                return True
            else:
                # Mark as failed
                await queue_service.mark_failed(post_item.id, error_msg)

                if post_item.retry_count >= 3:  # Max 3 retries
                    logger.error(
                        f"Message {post_item.message_id_in_source} failed permanently: {error_msg}"
                    )
                    return False
                else:
                    logger.warning(
                        f"Message {post_item.message_id_in_source} failed (retry {post_item.retry_count + 1}/3): {error_msg}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Error in schedule execution: {e}")
            return False

    async def _forward_message(
        self, source_channel_id: int, target_channel_id: int, message_id: int
    ) -> tuple:
        """Forward a message from source to target channel.

        Args:
            source_channel_id: Source channel ID
            target_channel_id: Target channel ID
            message_id: Message ID in source channel

        Returns:
            Tuple of (success: bool, error_message: str)
        """
        try:
            from src.config import API_RATE_LIMIT_DELAY

            # Rate limiting
            await asyncio.sleep(API_RATE_LIMIT_DELAY)

            # Fetch message from source (stub - would use Rubika API)
            # message = await self.client.get_message(source_channel_id, message_id)

            # For MVP: just acknowledge successful forward
            # In production, would actually fetch and forward via Rubika API
            logger.debug(
                f"Forwarding message {message_id} from {source_channel_id} to {target_channel_id}"
            )

            # Simulate successful forward for now
            return True, ""

        except Exception as e:
            error_msg = f"Forward failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    async def get_execution_stats(self) -> dict:
        """Get execution statistics."""
        try:
            total_sent = await self.db.fetchrow(
                "SELECT COUNT(*) as count FROM post_queue WHERE status = 'sent'"
            )

            total_failed = await self.db.fetchrow(
                "SELECT COUNT(*) as count FROM post_queue WHERE status = 'failed'"
            )

            pending = await self.db.fetchrow(
                "SELECT COUNT(*) as count FROM post_queue WHERE status = 'pending'"
            )

            return {
                "status": "running" if self.is_running else "stopped",
                "sent": total_sent["count"] if total_sent else 0,
                "failed": total_failed["count"] if total_failed else 0,
                "pending": pending["count"] if pending else 0,
                "timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}


async def create_execution_engine(db, bot_client) -> ExecutionEngine:
    """Factory function to create and return execution engine.

    Args:
        db: Database connection pool
        bot_client: Rubpy bot client

    Returns:
        ExecutionEngine instance
    """
    return ExecutionEngine(db, bot_client)
