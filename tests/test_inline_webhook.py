import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

import app
import src.config as config
from src.bot.main import RubikaClient


class FakeRequest:
    def __init__(self, payload):
        self.payload = payload

    async def json(self):
        return self.payload


@pytest.mark.asyncio
async def test_send_message_forwards_inline_keypad_to_rubika_sdk():
    client = RubikaClient.__new__(RubikaClient)
    client._bot = AsyncMock()
    inline_keypad = object()

    result = await client.send_message("u1", "choose", inline_keypad=inline_keypad)

    assert result is True
    client._bot.send_message.assert_awaited_once_with(
        chat_id="u1",
        text="choose",
        inline_keypad=inline_keypad,
    )


@pytest.mark.asyncio
async def test_registers_only_inline_message_endpoint():
    client = RubikaClient.__new__(RubikaClient)
    client._bot = AsyncMock()

    await client.register_inline_webhook("https://app.example/webhook")

    client._bot.update_bot_endpoints.assert_awaited_once_with(
        "https://app.example/webhook",
        "ReceiveInlineMessage",
    )


@pytest.mark.asyncio
async def test_rejects_non_https_inline_webhook():
    client = RubikaClient.__new__(RubikaClient)
    client._bot = AsyncMock()

    with pytest.raises(ValueError, match="HTTPS"):
        await client.register_inline_webhook("http://app.example/webhook")

    client._bot.update_bot_endpoints.assert_not_awaited()


@pytest.mark.asyncio
async def test_inline_webhook_routes_button_id(monkeypatch):
    monkeypatch.setattr(app, "_bot_ref", SimpleNamespace(client=AsyncMock()))
    payload = {
        "inline_message": {
            "chat_id": "u1",
            "aux_data": {"button_id": "🧪 برنامه آزمایشی و آموزشی"},
        }
    }

    with patch("src.bot.handlers.route_message", new_callable=AsyncMock) as route:
        response = await app.webhook(FakeRequest(payload))
        await asyncio.sleep(0)

    assert response.status == 200
    route.assert_awaited_once()
    assert route.await_args.args[1] == "u1"
    assert route.await_args.args[2]["text"] == "🧪 برنامه آزمایشی و آموزشی"


@pytest.mark.asyncio
async def test_inline_webhook_ignores_missing_button(monkeypatch):
    monkeypatch.setattr(app, "_bot_ref", SimpleNamespace(client=AsyncMock()))
    payload = {"inline_message": {"chat_id": "u1", "aux_data": {}}}

    with patch("src.bot.handlers.route_message", new_callable=AsyncMock) as route:
        response = await app.webhook(FakeRequest(payload))
        await asyncio.sleep(0)

    assert response.status == 200
    route.assert_not_awaited()


@pytest.mark.asyncio
async def test_paas_startup_requires_inline_webhook_url(monkeypatch):
    monkeypatch.setattr(config, "RUBIKA_INLINE_WEBHOOK_URL", None)

    with pytest.raises(RuntimeError, match="RUBIKA_INLINE_WEBHOOK_URL"):
        await app.main()
