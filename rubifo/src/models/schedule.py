from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal, Dict, Any


@dataclass
class Schedule:
    """Schedule model for planning message forwarding."""

    id: int = 0
    user_id: int = 0
    route_id: int = 0
    schedule_type: Literal["interval", "daily_count", "campaign", "smart_queue", "timing_pattern", "multi_stage", "content_mix"] = "interval"
    plan_kind: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    interval_minutes: Optional[int] = None
    daily_count: Optional[int] = None
    posts_per_run: int = 1
    loop_mode: bool = False
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    paused_reason: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Convert timestamps if they come as strings."""
        if self.plan_kind is None:
            self.plan_kind = self.schedule_type
        if isinstance(self.next_run, str):
            self.next_run = datetime.fromisoformat(self.next_run)
        if isinstance(self.last_run, str):
            self.last_run = datetime.fromisoformat(self.last_run)
        if isinstance(self.ends_at, str):
            self.ends_at = datetime.fromisoformat(self.ends_at)
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at)


@dataclass
class ScheduleTime:
    """Schedule time model for daily_count distribution."""

    id: int = 0
    schedule_id: int = 0
    hour: Optional[int] = None
    minute: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    status: str = "pending"
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Convert timestamp if it comes as string."""
        if isinstance(self.scheduled_at, str):
            self.scheduled_at = datetime.fromisoformat(self.scheduled_at)
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
