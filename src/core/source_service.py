import json
from typing import List, Optional, Dict, Any
from src.models.source import Source, SourcePost
from src.logger import logger


def _detect_message_type(message: Dict[str, Any]):
    """Parse incoming bot message and extract type, text, file_id, caption.

    Returns (message_type, text_content, file_id, caption, raw_data).
    """
    msg = message.get("new_message") or message
    file_info = msg.get("file") or {}
    sticker_info = msg.get("sticker") or {}

    file_id = file_info.get("file_id") or sticker_info.get("sticker_id") or ""
    mime = (file_info.get("mime") or "").lower()
    fname = (file_info.get("file_name") or "").lower()
    is_round = bool(file_info.get("is_round"))

    # Log raw file info for diagnostics (helps debug voice/video detection issues)
    if file_id:
        logger.debug(f"[DETECT] file_id={file_id[:20]}... mime={mime!r} fname={fname!r} is_round={is_round} raw_file={dict(file_info)}")

    if mime.startswith("image") or fname.endswith((".jpg", ".jpeg", ".png", ".webp")):
        msg_type = "photo"
    elif (mime.startswith("video") or fname.endswith((".mp4", ".mov", ".avi"))) and is_round:
        msg_type = "video_message"
    elif mime.startswith("video") or fname.endswith((".mp4", ".mov", ".avi")):
        msg_type = "video"
    elif (
        mime in ("audio/ogg", "audio/opus", "audio/mpeg", "audio/mp4", "audio/aac", "audio/x-m4a")
        or fname.endswith((".ogg", ".oga", ".opus"))
        or (fname.startswith(("ptt", "voice", "audio_")) and not fname.endswith((".mp3", ".m4a", ".flac")))
    ):
        msg_type = "voice"
    elif mime.startswith("audio") or fname.endswith((".mp3", ".m4a", ".flac")):
        msg_type = "music"
    elif "gif" in mime or fname.endswith(".gif"):
        msg_type = "gif"
    elif file_id:
        msg_type = "file"
    else:
        msg_type = "text"

    text = (msg.get("text") or "").strip()
    caption = ""
    if msg_type != "text":
        caption = (msg.get("caption") or text or "").strip()
        text = ""

    return msg_type, text or None, file_id or None, caption or None, msg


class SourceService:
    """Service for managing user sources and their posts."""

    def __init__(self, db):
        self.db = db

    async def create_source(self, user_id: int, name: str, program_purpose: str = "real") -> Source:
        row = await self.db.fetchrow(
            "INSERT INTO sources (user_id, name, program_purpose) VALUES ($1, $2, $3) RETURNING *",
            user_id, name, program_purpose,
        )
        logger.info(f"Source created: {row['id']} for user {user_id}")
        return Source(**dict(row))

    async def get_source(self, source_id: int) -> Optional[Source]:
        row = await self.db.fetchrow("SELECT * FROM sources WHERE id = $1", source_id)
        return Source(**dict(row)) if row else None

    async def get_user_sources(self, user_id: int) -> List[Source]:
        rows = await self.db.fetch(
            "SELECT * FROM sources WHERE user_id = $1 AND is_active = true ORDER BY created_at DESC",
            user_id,
        )
        return [Source(**dict(r)) for r in rows]

    async def delete_source(self, source_id: int) -> None:
        await self.db.execute("DELETE FROM sources WHERE id = $1", source_id)
        logger.info(f"Source {source_id} deleted")

    async def count_user_sources(self, user_id: int) -> int:
        row = await self.db.fetchrow(
            "SELECT COUNT(*) as c FROM sources WHERE user_id = $1 AND is_active = true", user_id
        )
        return row["c"] if row else 0

    async def add_post(
        self,
        source_id: int,
        message_type: str,
        text_content: Optional[str],
        file_id: Optional[str],
        caption: Optional[str],
        raw_data: Optional[Dict],
    ) -> SourcePost:
        # order_index = next available index
        row_count = await self.db.fetchrow(
            "SELECT COUNT(*) as c FROM source_posts WHERE source_id = $1", source_id
        )
        order_index = row_count["c"] if row_count else 0

        raw_json = json.dumps(raw_data) if raw_data else None

        row = await self.db.fetchrow(
            """
            INSERT INTO source_posts
              (source_id, order_index, message_type, text_content, file_id, caption, raw_data)
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
            RETURNING *
            """,
            source_id, order_index, message_type,
            text_content, file_id, caption, raw_json,
        )
        logger.info(f"Post added to source {source_id}: type={message_type}")
        return SourcePost(**{**dict(row), "raw_data": raw_data})

    async def add_post_from_message(self, source_id: int, message: Dict[str, Any]) -> SourcePost:
        """Parse a raw bot message dict and add it as a source post."""
        msg_type, text, file_id, caption, raw = _detect_message_type(message)
        return await self.add_post(source_id, msg_type, text, file_id, caption, raw)

    async def get_posts(self, source_id: int) -> List[SourcePost]:
        rows = await self.db.fetch(
            "SELECT * FROM source_posts WHERE source_id = $1 ORDER BY order_index ASC",
            source_id,
        )
        result = []
        for r in rows:
            d = dict(r)
            d["raw_data"] = json.loads(d["raw_data"]) if d.get("raw_data") else None
            result.append(SourcePost(**d))
        return result

    async def count_posts(self, source_id: int) -> int:
        row = await self.db.fetchrow(
            "SELECT COUNT(*) as c FROM source_posts WHERE source_id = $1", source_id
        )
        return row["c"] if row else 0

    async def remove_post(self, post_id: int) -> None:
        await self.db.execute("DELETE FROM source_posts WHERE id = $1", post_id)
        logger.info(f"Source post {post_id} removed")

    async def get_post(self, post_id: int) -> Optional[SourcePost]:
        row = await self.db.fetchrow("SELECT * FROM source_posts WHERE id = $1", post_id)
        if not row:
            return None
        d = dict(row)
        d["raw_data"] = json.loads(d["raw_data"]) if d.get("raw_data") else None
        return SourcePost(**d)

    async def mark_file_id_invalid(
        self, post_id: int, error_msg: str, user_id: int, route_id: Optional[int]
    ) -> None:
        await self.db.execute(
            "UPDATE source_posts SET file_id_valid = false WHERE id = $1", post_id
        )
        await self.db.execute(
            "INSERT INTO file_id_errors (source_post_id, user_id, route_id, error_msg) "
            "VALUES ($1, $2, $3, $4)",
            post_id, user_id, route_id, error_msg,
        )
        logger.warning(f"Source post {post_id} marked file_id invalid: {error_msg[:80]}")

    async def get_file_id_error_stats(self, days: int = 7) -> Dict[str, Any]:
        """Return frequency stats for file_id errors in the last N days."""
        row = await self.db.fetchrow(
            """
            SELECT
              COUNT(*) as total,
              COUNT(DISTINCT user_id) as affected_users,
              COUNT(DISTINCT source_post_id) as affected_posts
            FROM file_id_errors
            WHERE occurred_at >= NOW() - ($1 || ' days')::interval
            """,
            str(days),
        )
        return dict(row) if row else {"total": 0, "affected_users": 0, "affected_posts": 0}
