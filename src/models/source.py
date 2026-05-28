from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Source:
    id: int
    user_id: int
    name: str
    is_active: bool
    created_at: datetime

    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)


@dataclass
class SourcePost:
    id: int
    source_id: int
    order_index: int
    message_type: str  # text | photo | video | voice | music | file | gif
    text_content: Optional[str]
    file_id: Optional[str]
    caption: Optional[str]
    raw_data: Optional[dict]
    file_id_valid: bool
    added_at: datetime

    def __post_init__(self):
        if isinstance(self.added_at, str):
            self.added_at = datetime.fromisoformat(self.added_at)

    @property
    def display_type(self) -> str:
        icons = {
            "text": "📝", "photo": "🖼", "video": "🎬",
            "voice": "🎤", "music": "🎵", "file": "📎", "gif": "🎞",
        }
        return icons.get(self.message_type, "📄")

    @property
    def short_preview(self) -> str:
        if self.text_content:
            return self.text_content[:40]
        if self.caption:
            return self.caption[:40]
        return self.display_type
