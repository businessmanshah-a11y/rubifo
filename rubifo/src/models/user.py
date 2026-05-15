from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User model representing a Rubifo user."""

    id: int
    user_id: int
    username: Optional[str]
    trial_start_at: datetime
    trial_end_at: Optional[datetime]
    is_trial_active: bool
    created_at: datetime
    updated_at: datetime
