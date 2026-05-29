import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

import app
import src.config as config
from src.bot import commands, handlers
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


def test_main_keypad_uses_publishing_program_language():
    from src.bot.main import MAIN_KEYPAD

    labels = [
        button.button_text
        for row in MAIN_KEYPAD.rows
        for button in row.buttons
    ]

    assert "➕ ساخت برنامه جدید" in labels
    assert "📅 برنامه‌های انتشار" in labels
    assert "📊 تقویم انتشار" in labels
    assert "📁 دسته‌های محتوا" in labels
    assert "📋 مسیرهای من" not in labels
    assert "📦 سورس‌های من" not in labels


def test_inline_keypad_uses_payload_as_button_id():
    keypad = commands._make_inline_keypad([("Visible label", "stable_payload")], cols=1)
    button = keypad.rows[0].buttons[0]

    assert button.id == "stable_payload"
    assert button.button_text == "Visible label"


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
async def test_inline_webhook_registration_raises_on_rubika_rejection():
    client = RubikaClient.__new__(RubikaClient)
    client._bot = AsyncMock(return_value={"status": "InvalidUrl"})
    client._bot.update_bot_endpoints = AsyncMock(return_value={"status": "InvalidUrl"})

    with pytest.raises(RuntimeError, match="InvalidUrl"):
        await client.register_inline_webhook("https://app.example/webhook")


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
async def test_route_stable_new_program_button_id(monkeypatch):
    client = AsyncMock()

    with patch("src.bot.handlers.publishing_flow.begin_program", new_callable=AsyncMock) as begin:
        await handlers.route_message(client, "u1", {"text": "new_program", "new_message": {}})

    begin.assert_awaited_once_with(client, "u1")


@pytest.mark.asyncio
async def test_route_stable_source_button_ids(monkeypatch):
    client = AsyncMock()

    with patch("src.bot.commands.handle_viewsource", new_callable=AsyncMock) as viewsource:
        await handlers.route_message(client, "u1", {"text": "viewsource_5", "new_message": {}})
    viewsource.assert_awaited_once_with(client, "u1", 5)

    with patch("src.bot.commands.handle_addpost", new_callable=AsyncMock) as addpost:
        await handlers.route_message(client, "u1", {"text": "addpost_5", "new_message": {}})
    addpost.assert_awaited_once_with(client, "u1", 5)


@pytest.mark.asyncio
async def test_route_stable_destination_button_ids(monkeypatch):
    client = AsyncMock()

    with patch("src.bot.commands.handle_destination_plans", new_callable=AsyncMock) as plans:
        await handlers.route_message(client, "u1", {"text": "dst_plans_@shop", "new_message": {}})
    plans.assert_awaited_once_with(client, "u1", "@shop")

    with patch("src.bot.commands.handle_calendar_display", new_callable=AsyncMock) as calendar:
        await handlers.route_message(client, "u1", {"text": "dst_cal_@shop", "new_message": {}})
    calendar.assert_awaited_once_with(client, "u1", "@shop")

    with patch("src.bot.commands.handle_calendar_display", new_callable=AsyncMock) as calendar:
        await handlers.route_message(client, "u1", {"text": "cal_@shop", "new_message": {}})
    calendar.assert_awaited_once_with(client, "u1", "@shop")


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


@pytest.mark.asyncio
async def test_startup_continues_when_inline_webhook_registration_fails(monkeypatch):
    import src.bot.main as bot_main
    import src.database as database

    class FakePool:
        async def execute(self, *args, **kwargs):
            return None

    class FakeClient:
        async def register_inline_webhook(self, url):
            raise RuntimeError("Rubika webhook registration failed: InvalidUrl")

    class FakeBot:
        def __init__(self, token):
            self.client = None

        async def start_webhook_mode(self):
            return None

    monkeypatch.setattr(database, "init_db", AsyncMock())
    monkeypatch.setattr(database, "pool", FakePool())
    monkeypatch.setattr(config, "BOT_TOKEN", "token")
    monkeypatch.setattr(config, "RUBIKA_INLINE_WEBHOOK_URL", "https://rubifo.ir/webhook")
    monkeypatch.setattr(bot_main, "RufifoBot", FakeBot)
    monkeypatch.setattr(bot_main, "RubikaClient", lambda token: FakeClient())

    def close_created_coroutine(coro):
        coro.close()

    monkeypatch.setattr(app.asyncio, "create_task", close_created_coroutine)

    await app._startup()
