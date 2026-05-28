from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User model representing a Rubifo user."""

    id: int = 0
    user_id: str = ""
    username: Optional[str] = None
    trial_start_at: datetime = datetime.now()
    trial_end_at: Optional[datetime] = None
    is_trial_active: bool = True
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
