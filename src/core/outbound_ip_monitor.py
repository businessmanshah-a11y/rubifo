import asyncio
import inspect
from datetime import datetime
from typing import Any, Awaitable, Callable, Optional, Union

import httpx

from src.config import (
    OUTBOUND_IP_CHECK_INTERVAL_SECONDS,
    OUTBOUND_IP_CHECK_URL,
    TELEGRAM_ALERT_BOT_TOKEN,
    TELEGRAM_ALERT_CHAT_ID,
)
from src.logger import logger


FetchIP = Callable[[], Union[str, Awaitable[str]]]
SendAlert = Callable[[str], Union[Any, Awaitable[Any]]]


async def _maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value


class OutboundIPMonitor:
    """Tracks the app's public outbound IP and alerts only when it changes."""

    def __init__(
        self,
        db,
        *,
        fetch_ip: Optional[FetchIP] = None,
        send_alert: Optional[SendAlert] = None,
        telegram_bot_token: str = TELEGRAM_ALERT_BOT_TOKEN,
        telegram_chat_id: str = TELEGRAM_ALERT_CHAT_ID,
        check_url: str = OUTBOUND_IP_CHECK_URL,
        interval_seconds: int = OUTBOUND_IP_CHECK_INTERVAL_SECONDS,
    ):
        self.db = db
        self._fetch_ip = fetch_ip
        self._send_alert = send_alert
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.check_url = check_url
        self.interval_seconds = max(30, interval_seconds)

    @property
    def alerting_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    async def ensure_table(self) -> None:
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS outbound_ip_monitor (
                id              INTEGER PRIMARY KEY DEFAULT 1,
                current_ip      TEXT,
                previous_ip     TEXT,
                status          TEXT NOT NULL DEFAULT 'unknown',
                last_checked_at TIMESTAMP,
                last_changed_at TIMESTAMP,
                last_error      TEXT,
                alert_sent_at   TIMESTAMP,
                updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),
                CONSTRAINT outbound_ip_monitor_singleton CHECK (id = 1)
            )
            """
        )

    async def get_status(self) -> dict:
        row = await self.db.fetchrow("SELECT * FROM outbound_ip_monitor WHERE id = 1")
        if not row:
            return {
                "current_ip": None,
                "previous_ip": None,
                "status": "unknown",
                "last_checked_at": None,
                "last_changed_at": None,
                "last_error": None,
                "alert_sent_at": None,
                "alerting_enabled": self.alerting_enabled,
                "check_url": self.check_url,
                "interval_seconds": self.interval_seconds,
            }

        data = dict(row)
        data["alerting_enabled"] = self.alerting_enabled
        data["check_url"] = self.check_url
        data["interval_seconds"] = self.interval_seconds
        return data

    async def check_once(self) -> dict:
        existing = await self.db.fetchrow("SELECT * FROM outbound_ip_monitor WHERE id = 1")
        old_ip = existing["current_ip"] if existing else None

        try:
            current_ip = (await self._get_current_ip()).strip()
            if not current_ip:
                raise RuntimeError("empty IP response")
        except Exception as exc:
            error = str(exc)
            await self._save_state(
                current_ip=old_ip,
                previous_ip=existing["previous_ip"] if existing else None,
                status="error",
                last_changed_at=existing["last_changed_at"] if existing else None,
                last_error=error,
                alert_sent_at=existing["alert_sent_at"] if existing else None,
            )
            return await self.get_status()

        changed = bool(old_ip and current_ip != old_ip)
        status = "changed" if changed else "ok"
        previous_ip = old_ip if changed else (existing["previous_ip"] if existing else None)
        changed_at = datetime.utcnow() if changed else (existing["last_changed_at"] if existing else None)
        alert_sent_at = existing["alert_sent_at"] if existing else None

        if changed:
            message = self._build_change_message(old_ip, current_ip)
            try:
                await self._notify(message)
                alert_sent_at = datetime.utcnow()
            except Exception as exc:
                logger.error(f"Outbound IP Telegram alert failed: {exc}")

        await self._save_state(
            current_ip=current_ip,
            previous_ip=previous_ip,
            status=status,
            last_changed_at=changed_at,
            last_error=None,
            alert_sent_at=alert_sent_at,
        )
        return await self.get_status()

    async def run_forever(self) -> None:
        await self.ensure_table()
        while True:
            try:
                await self.check_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error(f"Outbound IP monitor loop failed: {exc}")
            await asyncio.sleep(self.interval_seconds)

    async def _get_current_ip(self) -> str:
        if self._fetch_ip:
            return await _maybe_await(self._fetch_ip())

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(self.check_url)
            response.raise_for_status()
            return response.text

    async def _notify(self, message: str) -> None:
        if self._send_alert:
            await _maybe_await(self._send_alert(message))
            return

        if not self.alerting_enabled:
            return

        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url,
                json={
                    "chat_id": self.telegram_chat_id,
                    "text": message,
                    "disable_web_page_preview": True,
                },
            )
            response.raise_for_status()

    async def _save_state(
        self,
        *,
        current_ip: Optional[str],
        previous_ip: Optional[str],
        status: str,
        last_changed_at: Optional[datetime],
        last_error: Optional[str],
        alert_sent_at: Optional[datetime],
    ) -> None:
        await self.db.execute(
            """
            INSERT INTO outbound_ip_monitor (
                id, current_ip, previous_ip, status, last_checked_at,
                last_changed_at, last_error, alert_sent_at, updated_at
            )
            VALUES (1, $1, $2, $3, NOW(), $4, $5, $6, NOW())
            ON CONFLICT (id) DO UPDATE SET
                current_ip = EXCLUDED.current_ip,
                previous_ip = EXCLUDED.previous_ip,
                status = EXCLUDED.status,
                last_checked_at = EXCLUDED.last_checked_at,
                last_changed_at = EXCLUDED.last_changed_at,
                last_error = EXCLUDED.last_error,
                alert_sent_at = EXCLUDED.alert_sent_at,
                updated_at = NOW()
            """,
            current_ip,
            previous_ip,
            status,
            last_changed_at,
            last_error,
            alert_sent_at,
        )

    def _build_change_message(self, old_ip: str, current_ip: str) -> str:
        checked_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        return (
            "هشدار روبیفو: IP خروجی سرور تغییر کرد.\n"
            f"IP قبلی: {old_ip}\n"
            f"IP جدید: {current_ip}\n"
            f"زمان بررسی: {checked_at}\n"
            "لطفاً IP مجاز در پنل درگاه پرداخت را بررسی/به‌روزرسانی کنید."
        )
