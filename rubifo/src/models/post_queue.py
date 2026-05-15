from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PostQueueItem:
    """Post Queue model for managing message forwarding queue."""

    id: int
    route_id: int
    message_id_in_source: int
    source_date: datetime
    status: str = "pending"  # pending, sent, failed, removed
    retry_count: int = 0
    last_error: Optional[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Convert timestamps if they come as strings."""
        if isinstance(self.source_date, str):
            self.source_date = datetime.fromisoformat(self.source_date)
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
