from dataclasses import dataclass
from datetime import date
from typing import Literal


@dataclass
class Subscription:
    """Subscription model representing a user's paid subscription."""

    id: int
    user_id: int
    tier: Literal["basic", "pro", "enterprise"]
    start_date: date
    end_date: date
    is_active: bool
    created_at: date
