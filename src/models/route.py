from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Route:
    """Route model for channel forwarding mapping."""

    id: int
    user_id: int
    source_channel_id: int
    target_channel_id: int
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Convert timestamps if they come as strings."""
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at)
