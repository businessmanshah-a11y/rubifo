"""Tests for verifying publishing access to a destination channel."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.bot.main import RubikaClient
from rubpy.bot.exceptions import APIException


def client_with_bot():
    client = RubikaClient.__new__(RubikaClient)
    client._bot = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_verify_destination_posts_and_deletes_probe_message():
    client = client_with_bot()
    client._bot.get_chat.return_value = SimpleNamespace(chat_id="c1", title="Shop")
    client._bot.get_me.return_value = SimpleNamespace(bot_id="b1")
    client._bot.get_chat_administrators.return_value = {"members": [{"user_id": "b1"}]}
    client._bot.send_message.return_value = SimpleNamespace(message_id="m1")

    result = await client.verify_destination_channel("@shop")

    assert result["status"] == "verified"
    client._bot.delete_message.assert_awaited_once_with("c1", "m1")


@pytest.mark.asyncio
async def test_verify_destination_reports_non_admin_without_posting():
    client = client_with_bot()
    client._bot.get_chat.return_value = SimpleNamespace(chat_id="c1", title="Shop")
    client._bot.get_me.return_value = SimpleNamespace(bot_id="b1")
    client._bot.get_chat_administrators.return_value = {"members": [{"user_id": "someone"}]}

    result = await client.verify_destination_channel("@shop")

    assert result["status"] == "not_admin"
    client._bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_verify_destination_keeps_verification_when_probe_cleanup_fails():
    client = client_with_bot()
    client._bot.get_chat.return_value = SimpleNamespace(chat_id="c1", title="Shop")
    client._bot.get_me.return_value = SimpleNamespace(bot_id="b1")
    client._bot.get_chat_administrators.return_value = [{"user_id": "b1"}]
    client._bot.send_message.return_value = {"message_id": "m1"}
    client._bot.delete_message.side_effect = Exception("cannot delete")

    result = await client.verify_destination_channel("@shop")

    assert result["status"] == "cleanup_failed"
    assert result["verified"] is True


@pytest.mark.asyncio
async def test_verify_destination_reports_invalid_access_from_rubika_api():
    client = client_with_bot()
    client._bot.get_chat.side_effect = APIException(
        status="INVALID_ACCESS",
        dev_message="The bot doesn’t have access to the chat.",
    )

    result = await client.verify_destination_channel("@shop")

    assert result["status"] == "invalid_access"
    assert result["verified"] is False
    assert "INVALID_ACCESS" in result["error"]


@pytest.mark.asyncio
async def test_verify_destination_reports_invalid_input_from_rubika_api():
    client = client_with_bot()
    client._bot.get_chat.side_effect = APIException(status="INVALID_INPUT")

    result = await client.verify_destination_channel("shop")

    assert result["status"] == "invalid_input"
    assert result["verified"] is False


@pytest.mark.asyncio
async def test_verify_destination_reports_unknown_api_error_separately():
    client = client_with_bot()
    client._bot.get_chat.side_effect = APIException(status="SOMETHING_ELSE")

    result = await client.verify_destination_channel("@shop")

    assert result["status"] == "api_error"
    assert result["verified"] is False
