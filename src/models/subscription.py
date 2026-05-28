from dataclasses import dataclass
from datetime import date
from typing import Literal


@dataclass
class Subscription:
    """Subscription model representing a user's paid subscription."""

    id: int = 0
    user_id: int = 0
    tier: Literal["basic", "pro", "enterprise"] = "basic"
    start_date: date = date.today()
    end_date: date = date.today()
    is_active: bool = True
    created_at: date = date.today()
