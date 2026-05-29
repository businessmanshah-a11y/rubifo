"""Interaction tests for the publishing-program wizard."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.bot import publishing_flow
from src.bot import handlers


@pytest.mark.asyncio
async def test_begin_program_asks_for_tutorial_or_real_before_channel(mock_bot_client):
    with patch.object(publishing_flow.PublishingProgramService, "get_draft", new_callable=AsyncMock, return_value=None):
        await publishing_flow.begin_program(mock_bot_client, "u1")

    text = mock_bot_client.send_message.await_args.args[1]
    assert "چطور شروع کنید" in text
    assert "برنامه آزمایشی" in text
    assert "برنامه واقعی" in text
    assert "کانال" not in text
    assert mock_bot_client.send_message.await_args.kwargs["inline_keypad"] is not None
    assert "keypad" not in mock_bot_client.send_message.await_args.kwargs
    assert "with_keypad" not in mock_bot_client.send_message.await_args.kwargs


@pytest.mark.asyncio
async def test_start_program_button_opens_publishing_wizard(mock_bot_client):
    with patch("src.bot.handlers.publishing_flow.begin_program", new_callable=AsyncMock) as begin:
        await handlers.route_message(
            mock_bot_client,
            "u1",
            {"text": "➕ ساخت برنامه جدید", "new_message": {"text": "➕ ساخت برنامه جدید"}},
        )

    begin.assert_awaited_once_with(mock_bot_client, "u1")


@pytest.mark.asyncio
async def test_inline_button_click_continues_publishing_wizard(mock_bot_client):
    publishing_flow.active_flows["u1"] = {"step": "choose_kind"}

    with patch("src.bot.handlers.publishing_flow.handle_text", new_callable=AsyncMock, return_value=True) as handle:
        await handlers.route_message(
            mock_bot_client,
            "u1",
            {"text": "🧪 برنامه آزمایشی و آموزشی", "new_message": {}},
        )

    handle.assert_awaited_once_with(mock_bot_client, "u1", "🧪 برنامه آزمایشی و آموزشی")


@pytest.mark.asyncio
async def test_tutorial_choice_warns_before_asking_for_channel(mock_bot_client, mock_db):
    with patch("src.database.pool", mock_db):
        with patch.object(publishing_flow.PublishingProgramService, "save_draft", new_callable=AsyncMock):
            with patch.object(publishing_flow.PublishingProgramService, "can_create_tutorial", new_callable=AsyncMock, return_value=(True, None)):
                publishing_flow.active_flows["u1"] = {"step": "choose_kind"}
                await publishing_flow.handle_text(mock_bot_client, "u1", "🧪 برنامه آزمایشی و آموزشی")

    messages = [call.args[1] for call in mock_bot_client.send_message.await_args_list]
    assert "سه پست" in messages[0]
    assert "واقعاً" in messages[0]
    assert "کانال" in messages[1]


@pytest.mark.asyncio
async def test_verified_real_channel_proceeds_to_content_choice(mock_bot_client, mock_db):
    destination = SimpleNamespace(id=8, channel_id="@shop")
    mock_bot_client.verify_destination_channel = AsyncMock(
        return_value={"status": "verified", "verified": True, "channel_id": "@shop", "title": "Shop"}
    )
    publishing_flow.active_flows["u1"] = {"step": "channel", "flow_kind": "real"}

    with patch("src.database.pool", mock_db):
        with patch.object(publishing_flow.DestinationService, "can_register", new_callable=AsyncMock, return_value=(True, None)):
            with patch.object(publishing_flow.DestinationService, "record_verification", new_callable=AsyncMock, return_value=destination):
                with patch.object(publishing_flow.PublishingProgramService, "save_draft", new_callable=AsyncMock):
                    await publishing_flow.handle_text(mock_bot_client, "u1", "@shop")

    text = mock_bot_client.send_message.await_args.args[1]
    assert "دسته محتوا" in text
    assert publishing_flow.active_flows["u1"]["step"] == "content_choice"


@pytest.mark.asyncio
async def test_invalid_access_channel_asks_for_forwarded_post(mock_bot_client, mock_db):
    mock_bot_client.verify_destination_channel = AsyncMock(
        return_value={"status": "invalid_access", "verified": False, "error": "INVALID_ACCESS"}
    )
    publishing_flow.active_flows["u1"] = {"step": "channel", "flow_kind": "real"}

    with patch("src.database.pool", mock_db):
        with patch.object(publishing_flow.DestinationService, "can_register", new_callable=AsyncMock, return_value=(True, None)):
            await publishing_flow.handle_text(mock_bot_client, "u1", "@shop")

    text = mock_bot_client.send_message.await_args.args[1]
    assert "یک پست از همان کانال را فوروارد کنید" in text
    assert "پیدا نشد" not in text


@pytest.mark.asyncio
async def test_forwarded_channel_message_verifies_real_chat_id(mock_bot_client, mock_db):
    destination = SimpleNamespace(id=8, channel_id="c0real")
    mock_bot_client.verify_destination_channel = AsyncMock(
        return_value={"status": "verified", "verified": True, "channel_id": "c0real", "title": "Shop"}
    )
    publishing_flow.active_flows["u1"] = {"step": "channel", "flow_kind": "real"}
    forwarded_message = {
        "new_message": {
            "forwarded_from": {
                "chat_id": "c0real",
                "object_guid": "c0real",
            }
        }
    }

    with patch("src.database.pool", mock_db):
        with patch.object(publishing_flow.DestinationService, "can_register", new_callable=AsyncMock, return_value=(True, None)) as can_register:
            with patch.object(publishing_flow.DestinationService, "record_verification", new_callable=AsyncMock, return_value=destination) as record:
                with patch.object(publishing_flow.PublishingProgramService, "save_draft", new_callable=AsyncMock):
                    await publishing_flow.handle_text(mock_bot_client, "u1", "", forwarded_message)

    mock_bot_client.verify_destination_channel.assert_awaited_once_with("c0real")
    can_register.assert_awaited_once_with("u1", "c0real")
    record.assert_awaited_once()
    assert record.await_args.args[1] == "c0real"
    assert publishing_flow.active_flows["u1"]["step"] == "content_choice"


@pytest.mark.asyncio
async def test_forwarded_channel_message_uses_rubika_from_chat_id(mock_bot_client, mock_db):
    destination = SimpleNamespace(id=8, channel_id="c0from")
    mock_bot_client.verify_destination_channel = AsyncMock(
        return_value={"status": "verified", "verified": True, "channel_id": "c0from", "title": "Shop"}
    )
    publishing_flow.active_flows["u1"] = {"step": "channel", "flow_kind": "real"}
    forwarded_message = {
        "new_message": {
            "text": "متن پست فوروارد شده که آیدی کانال نیست",
            "forwarded_from": {
                "type_from": "Channel",
                "from_chat_id": "c0from",
                "message_id": "m1",
            },
        }
    }

    with patch("src.database.pool", mock_db):
        with patch.object(publishing_flow.DestinationService, "can_register", new_callable=AsyncMock, return_value=(True, None)):
            with patch.object(publishing_flow.DestinationService, "record_verification", new_callable=AsyncMock, return_value=destination) as record:
                with patch.object(publishing_flow.PublishingProgramService, "save_draft", new_callable=AsyncMock):
                    await publishing_flow.handle_text(
                        mock_bot_client,
                        "u1",
                        "متن پست فوروارد شده که آیدی کانال نیست",
                        forwarded_message,
                    )

    mock_bot_client.verify_destination_channel.assert_awaited_once_with("c0from")
    assert record.await_args.args[1] == "c0from"
    assert publishing_flow.active_flows["u1"]["step"] == "content_choice"


@pytest.mark.asyncio
async def test_full_channel_capacity_offers_reuse_replace_and_upgrade(mock_bot_client, mock_db):
    publishing_flow.active_flows["u1"] = {"step": "channel", "flow_kind": "real"}

    with patch("src.database.pool", mock_db):
        with patch.object(
            publishing_flow.DestinationService,
            "can_register",
            new_callable=AsyncMock,
            return_value=(False, "ظرفیت کانال مقصد شما پر است."),
        ):
            with patch.object(publishing_flow.PublishingProgramService, "save_draft", new_callable=AsyncMock):
                await publishing_flow.handle_text(mock_bot_client, "u1", "@newshop")

    text = mock_bot_client.send_message.await_args.args[1]
    assert "ادامه با کانال ثبت‌شده" in text
    assert "جایگزینی کانال" in text
    assert "ارتقای اشتراک" in text
    assert publishing_flow.active_flows["u1"]["step"] == "channel_limit"


@pytest.mark.asyncio
async def test_real_confirmation_commits_human_program(mock_bot_client, mock_db):
    publishing_flow.active_flows["u1"] = {
        "step": "confirm",
        "flow_kind": "real",
        "destination": SimpleNamespace(id=8, channel_id="@shop"),
        "source": SimpleNamespace(id=4, name="رضایت مشتری"),
        "config": {"program_mode": "recurring", "cadence": "interval", "interval_minutes": 120},
    }
    with patch("src.database.pool", mock_db):
        with patch.object(
            publishing_flow.PublishingProgramService,
            "commit_real_program",
            new_callable=AsyncMock,
            return_value={"waiting_for_content": False, "schedule": SimpleNamespace(id=9)},
        ):
            await publishing_flow.handle_text(mock_bot_client, "u1", "تایید برنامه")

    text = mock_bot_client.send_message.await_args.args[1]
    assert "برنامه انتشار فعال شد" in text
    assert "مسیر" not in text


@pytest.mark.asyncio
async def test_edit_confirmation_updates_existing_program(mock_bot_client, mock_db):
    publishing_flow.active_flows["u1"] = {
        "step": "confirm",
        "flow_kind": "real",
        "edit_schedule_id": 9,
        "destination": SimpleNamespace(id=8, channel_id="@shop"),
        "source": SimpleNamespace(id=4, name="رضایت مشتری"),
        "config": {"program_mode": "recurring", "cadence": "interval", "interval_minutes": 120},
    }
    with patch("src.database.pool", mock_db):
        with patch.object(
            publishing_flow.PublishingProgramService,
            "update_real_program",
            new_callable=AsyncMock,
            return_value={"waiting_for_content": False, "schedule": SimpleNamespace(id=9)},
        ) as update:
            await publishing_flow.handle_text(mock_bot_client, "u1", "تایید برنامه")

    update.assert_awaited_once_with(
        "u1",
        9,
        4,
        {"program_mode": "recurring", "cadence": "interval", "interval_minutes": 120},
    )
    text = mock_bot_client.send_message.await_args.args[1]
    assert "به‌روزرسانی" in text
