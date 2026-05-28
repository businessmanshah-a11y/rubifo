from typing import Optional, Dict, Any, List
from src.models.post_queue import PostQueueItem
from src.logger import logger


class QueueService:
    """Service for managing post queue and forwarding."""

    def __init__(self, db):
        self.db = db

    async def get_next_pending(self, route_id: int, message_type: Optional[str] = None):
        """Get next pending post in FIFO order (by source_date then id).

        Joins source_posts to get order_index for proper ordering.
        Returns raw dict so execution engine can access source_post_id.
        """
        type_filter = "AND sp.message_type = $2" if message_type else ""
        args = [route_id]
        if message_type:
            args.append(message_type)
        result = await self.db.fetchrow(
            f"""
            SELECT pq.*, sp.order_index
            FROM post_queue pq
            LEFT JOIN source_posts sp ON pq.source_post_id = sp.id
            WHERE pq.route_id = $1 AND pq.status = 'pending'
            {type_filter}
            ORDER BY sp.order_index ASC NULLS LAST, pq.id ASC
            LIMIT 1
            """,
            *args,
        )
        return dict(result) if result else None

    async def rebuild_pending_from_source(self, route_id: int) -> int:
        """Rebuild pending queue items from the route source for looped plans."""
        route = await self.db.fetchrow("SELECT source_id FROM routes WHERE id = $1", route_id)
        source_id = route["source_id"] if route else None
        if not source_id:
            logger.warning(f"Route {route_id} has no source_id for queue rebuild")
            return 0

        posts = await self.db.fetch(
            """
            SELECT id FROM source_posts
            WHERE source_id = $1
              AND (message_type = 'text' OR (file_id_valid = true AND file_id IS NOT NULL))
            ORDER BY order_index ASC
            """,
            source_id,
        )
        for post in posts:
            await self.db.execute(
                "INSERT INTO post_queue (route_id, source_post_id, status) VALUES ($1, $2, 'pending')",
                route_id,
                post["id"],
            )
        logger.info(f"Rebuilt route {route_id} queue with {len(posts)} posts")
        return len(posts)

    async def mark_sent(self, queue_id: int) -> None:
        """Mark a queued post as successfully sent.

        Args:
            queue_id: Queue item ID
        """
        await self.db.execute(
            "UPDATE post_queue SET status = 'sent' WHERE id = $1", queue_id
        )

        logger.info(f"Queue item {queue_id} marked as sent")

    async def mark_failed(self, queue_id: int, error_msg: str) -> None:
        """Mark a queued post as failed and increment retry count.

        Args:
            queue_id: Queue item ID
            error_msg: Error message to store
        """
        await self.db.execute(
            """
            UPDATE post_queue
            SET status = 'failed', retry_count = retry_count + 1, last_error = $2
            WHERE id = $1
            """,
            queue_id,
            error_msg,
        )

        logger.warning(f"Queue item {queue_id} marked as failed: {error_msg}")

    async def get_queue_stats(self, route_id: int) -> Dict[str, int]:
        """Get queue statistics for a route (counts by status).

        Args:
            route_id: Route ID

        Returns:
            Dictionary with status counts
        """
        results = await self.db.fetch(
            """
            SELECT status, COUNT(*) as count FROM post_queue
            WHERE route_id = $1
            GROUP BY status
            """,
            route_id,
        )

        stats = {row["status"]: row["count"] for row in results}

        return stats

    async def get_queue_items(
        self, route_id: int, status: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> List[PostQueueItem]:
        """Get queue items for a route with optional status filter.

        Args:
            route_id: Route ID
            status: Optional status filter
            limit: Result limit
            offset: Pagination offset

        Returns:
            List of PostQueueItems
        """
        if status:
            results = await self.db.fetch(
                """
                SELECT * FROM post_queue
                WHERE route_id = $1 AND status = $2
                ORDER BY source_date DESC
                LIMIT $3 OFFSET $4
                """,
                route_id,
                status,
                limit,
                offset,
            )
        else:
            results = await self.db.fetch(
                """
                SELECT * FROM post_queue
                WHERE route_id = $1
                ORDER BY source_date DESC
                LIMIT $2 OFFSET $3
                """,
                route_id,
                limit,
                offset,
            )

        return [PostQueueItem(**dict(row)) for row in results]

    async def reset_route_queue(self, route_id: int) -> int:
        """Reset all pending posts in a route queue (for loop mode).

        Marks all non-sent posts back to pending status.

        Args:
            route_id: Route ID

        Returns:
            Count of posts reset
        """
        result = await self.db.fetchrow(
            """
            UPDATE post_queue
            SET status = 'pending', retry_count = 0
            WHERE route_id = $1 AND status != 'sent'
            RETURNING COUNT(*) as count
            """,
            route_id,
        )

        count = result["count"] if result else 0
        logger.info(f"Route {route_id} queue reset: {count} posts")

        return count

    async def delete_queue_item(self, queue_id: int) -> None:
        """Delete a queue item.

        Args:
            queue_id: Queue item ID
        """
        await self.db.execute("DELETE FROM post_queue WHERE id = $1", queue_id)

        logger.info(f"Queue item {queue_id} deleted")

    async def clear_route_queue(self, route_id: int) -> int:
        """Clear entire queue for a route.

        Args:
            route_id: Route ID

        Returns:
            Count of deleted items
        """
        result = await self.db.fetchrow(
            "DELETE FROM post_queue WHERE route_id = $1 RETURNING COUNT(*) as count",
            route_id,
        )

        count = result["count"] if result else 0
        logger.info(f"Route {route_id} queue cleared: {count} posts deleted")

        return count
