from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class DestinationChannel:
    """A user-owned channel verified for automated publishing."""

    id: int = 0
    user_id: str = ""
    channel_id: str = ""
    title: Optional[str] = None
    verification_status: str = "pending"
    verification_error: Optional[str] = None
    verified_at: Optional[datetime] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        for name in ("verified_at", "created_at", "updated_at"):
            value = getattr(self, name)
            if isinstance(value, str):
                setattr(self, name, datetime.fromisoformat(value))

