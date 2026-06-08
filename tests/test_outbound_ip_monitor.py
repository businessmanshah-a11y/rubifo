from datetime import datetime

import pytest

from src.core.outbound_ip_monitor import OutboundIPMonitor


class FakeMonitorDb:
    def __init__(self, row=None):
        self.row = row
        self.executed = []

    async def fetchrow(self, query: str, *args):
        if "SELECT * FROM outbound_ip_monitor" in query:
            return self.row
        return None

    async def execute(self, query: str, *args):
        self.executed.append((query, args))
        if "INSERT INTO outbound_ip_monitor" in query:
            self.row = {
                "id": 1,
                "current_ip": args[0],
                "previous_ip": args[1],
                "status": args[2],
                "last_checked_at": datetime.utcnow(),
                "last_changed_at": args[3],
                "last_error": args[4],
                "alert_sent_at": args[5],
                "updated_at": datetime.utcnow(),
            }
        return "OK"


@pytest.mark.asyncio
async def test_first_successful_check_stores_ip_without_alert():
    alerts = []
    monitor = OutboundIPMonitor(
        FakeMonitorDb(),
        fetch_ip=lambda: "185.19.201.63",
        send_alert=lambda message: alerts.append(message),
    )

    result = await monitor.check_once()

    assert result["current_ip"] == "185.19.201.63"
    assert result["previous_ip"] is None
    assert result["status"] == "ok"
    assert alerts == []


@pytest.mark.asyncio
async def test_unchanged_ip_does_not_send_alert():
    alerts = []
    db = FakeMonitorDb(
        {
            "id": 1,
            "current_ip": "185.19.201.63",
            "previous_ip": None,
            "status": "ok",
            "last_checked_at": datetime.utcnow(),
            "last_changed_at": None,
            "last_error": None,
            "alert_sent_at": None,
            "updated_at": datetime.utcnow(),
        }
    )
    monitor = OutboundIPMonitor(
        db,
        fetch_ip=lambda: "185.19.201.63",
        send_alert=lambda message: alerts.append(message),
    )

    result = await monitor.check_once()

    assert result["current_ip"] == "185.19.201.63"
    assert result["previous_ip"] is None
    assert result["status"] == "ok"
    assert alerts == []


@pytest.mark.asyncio
async def test_changed_ip_updates_previous_ip_and_sends_one_alert():
    alerts = []
    db = FakeMonitorDb(
        {
            "id": 1,
            "current_ip": "185.19.201.63",
            "previous_ip": None,
            "status": "ok",
            "last_checked_at": datetime.utcnow(),
            "last_changed_at": None,
            "last_error": None,
            "alert_sent_at": None,
            "updated_at": datetime.utcnow(),
        }
    )
    monitor = OutboundIPMonitor(
        db,
        fetch_ip=lambda: "185.19.201.64",
        send_alert=lambda message: alerts.append(message),
    )

    result = await monitor.check_once()

    assert result["current_ip"] == "185.19.201.64"
    assert result["previous_ip"] == "185.19.201.63"
    assert result["status"] == "changed"
    assert len(alerts) == 1
    assert "185.19.201.63" in alerts[0]
    assert "185.19.201.64" in alerts[0]


@pytest.mark.asyncio
async def test_fetch_error_records_error_without_alert():
    alerts = []

    def fetch_ip():
        raise RuntimeError("ip service timeout")

    monitor = OutboundIPMonitor(
        FakeMonitorDb(),
        fetch_ip=fetch_ip,
        send_alert=lambda message: alerts.append(message),
    )

    result = await monitor.check_once()

    assert result["status"] == "error"
    assert result["last_error"] == "ip service timeout"
    assert alerts == []


def test_alerting_disabled_without_telegram_credentials():
    monitor = OutboundIPMonitor(FakeMonitorDb(), telegram_bot_token="", telegram_chat_id="")

    assert monitor.alerting_enabled is False
