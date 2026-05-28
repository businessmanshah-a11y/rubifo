from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class PublishingDraft:
    """Persisted progress for a publishing-program creation wizard."""

    id: int = 0
    user_id: str = ""
    flow_kind: str = "real"
    step: str = "choose_kind"
    destination_id: Optional[int] = None
    source_id: Optional[int] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

