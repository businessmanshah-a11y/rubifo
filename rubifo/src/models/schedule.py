from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal


@dataclass
class Schedule:
    """Schedule model for planning message forwarding."""

    id: int
    user_id: int
    route_id: int
    schedule_type: Literal["interval", "daily_count"]
    interval_minutes: Optional[int] = None
    daily_count: Optional[int] = None
    next_run: Optional[datetime] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Convert timestamps if they come as strings."""
        if isinstance(self.next_run, str):
            self.next_run = datetime.fromisoformat(self.next_run)
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at)


@dataclass
class ScheduleTime:
    """Schedule time model for daily_count distribution."""

    id: int
    schedule_id: int
    hour: int
    minute: int
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Convert timestamp if it comes as string."""
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
