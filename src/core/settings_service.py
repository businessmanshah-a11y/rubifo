from typing import Any, Dict, Optional
from src.logger import logger


class SettingsService:
    """Read/write admin-configurable settings from app_settings table."""

    def __init__(self, db):
        self.db = db

    async def get(self, key: str, default: str = "") -> str:
        row = await self.db.fetchrow(
            "SELECT value FROM app_settings WHERE key = $1", key
        )
        return row["value"] if row else default

    async def get_int(self, key: str, default: int = 0) -> int:
        val = await self.get(key, str(default))
        try:
            return int(val)
        except ValueError:
            return default

    async def set(self, key: str, value: str) -> None:
        await self.db.execute(
            """
            INSERT INTO app_settings (key, value, updated_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
            """,
            key,
            value,
        )
        logger.info(f"Setting updated: {key} = {value}")

    async def get_all(self) -> Dict[str, str]:
        rows = await self.db.fetch("SELECT key, value FROM app_settings ORDER BY key")
        return {row["key"]: row["value"] for row in rows}

    async def get_trial_duration_hours(self) -> int:
        return await self.get_int("trial_duration_hours", 48)

    async def get_plans(self) -> Dict[str, Any]:
        """Return subscription tiers loaded from DB."""
        all_settings = await self.get_all()
        tiers = {}
        for tier_key in ("basic", "pro", "enterprise"):
            tiers[tier_key] = {
                "display_name_fa": all_settings.get(f"plan_{tier_key}_name", tier_key),
                "max_destinations": int(all_settings.get(f"plan_{tier_key}_routes", "1")),
                "price_monthly": int(all_settings.get(f"plan_{tier_key}_price", "0")),
            }
        return tiers
