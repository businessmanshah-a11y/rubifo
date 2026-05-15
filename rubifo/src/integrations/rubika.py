from typing import List, Dict, Any, Optional
from src.logger import logger


class RubikaUserClient:
    """Wrapper around rubpy.Client (user/account API) for reading channel posts."""

    def __init__(self, session_name: str = "rubifo_user"):
        self.session_name = session_name
        self._client = None
        self._started = False

    async def start(self) -> None:
        from rubpy import Client
        self._client = Client(name=self.session_name)
        await self._client.start()
        self._started = True
        logger.info("Rubika user client started")

    async def stop(self) -> None:
        if self._started and self._client:
            try:
                await self._client.stop()
            except Exception:
                pass
            self._started = False
            logger.info("Rubika user client stopped")

    @property
    def is_ready(self) -> bool:
        return self._started and self._client is not None

    async def resolve_channel(self, channel_input: str) -> Optional[str]:
        """Resolve @username, rubika.ir URL, or numeric ID to object_guid.

        Returns object_guid string (e.g. 'c0XXXX') or None on failure.
        """
        if not self.is_ready:
            return None

        t = channel_input.strip()

        # Already an object_guid (starts with c0, g0, u0, etc.)
        if len(t) > 4 and t[:2] in ("c0", "g0", "u0", "b0", "s0"):
            return t

        # Extract username from URL or @prefix
        if "rubika.ir/" in t:
            t = t.rstrip("/").split("rubika.ir/")[-1].strip()
        elif t.startswith("@"):
            t = t[1:].strip()

        if not t:
            return None

        try:
            result = await self._client.get_object_by_username(t)
            if result and hasattr(result, "object_guid"):
                return result.object_guid
            # Some rubpy versions nest it differently
            data = result if isinstance(result, dict) else vars(result)
            return data.get("object_guid") or data.get("data", {}).get("object_guid")
        except Exception as e:
            logger.error(f"Failed to resolve channel '{channel_input}': {e}")
            return None

    async def get_channel_messages(
        self,
        object_guid: str,
        min_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch messages from a channel.

        Args:
            object_guid: Channel object_guid (e.g. 'c0XXXX')
            min_id: Only return messages with message_id > min_id (exclusive)
            limit: Max messages to fetch per request

        Returns:
            List of message dicts with 'message_id' and 'time' keys, oldest first.
        """
        if not self.is_ready:
            return []

        try:
            result = await self._client.get_messages(
                object_guid=object_guid,
                max_id=0,
                limit=limit,
                sort="FromMax",
            )

            raw_messages = []
            if result:
                if hasattr(result, "messages"):
                    raw_messages = result.messages or []
                elif isinstance(result, dict):
                    raw_messages = result.get("messages") or result.get("data", {}).get("messages") or []

            messages = []
            for msg in raw_messages:
                if isinstance(msg, dict):
                    mid = str(msg.get("message_id", ""))
                    ts = msg.get("time", 0)
                else:
                    mid = str(getattr(msg, "message_id", ""))
                    ts = getattr(msg, "time", 0)

                if not mid:
                    continue
                if min_id and int(mid) <= int(min_id):
                    continue
                messages.append({"message_id": mid, "time": int(ts)})

            # Oldest first for queue insertion
            messages.sort(key=lambda m: m["time"])
            logger.info(f"Fetched {len(messages)} new messages from {object_guid}")
            return messages

        except Exception as e:
            logger.error(f"Failed to get messages from {object_guid}: {e}")
            return []

    async def forward_message(
        self,
        from_guid: str,
        to_guid: str,
        message_id: str,
    ) -> bool:
        """Forward a single message from source channel to target channel."""
        if not self.is_ready:
            return False
        try:
            await self._client.forward_messages(
                from_object_guid=from_guid,
                to_object_guid=to_guid,
                message_ids=[message_id],
            )
            return True
        except Exception as e:
            logger.error(f"Failed to forward {message_id} from {from_guid} to {to_guid}: {e}")
            return False
