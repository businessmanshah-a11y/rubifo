"""Tests for collecting source posts."""

import pytest
from unittest.mock import AsyncMock, patch

from src.bot import commands
from src.bot.main import RubikaClient
from src.core.execution_engine import ExecutionEngine


class _FakeDownloadResponse:
    status = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def read(self):
        return b"ogg-bytes"


class _FakeClientSession:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def get(self, *args, **kwargs):
        return _FakeDownloadResponse()


@pytest.mark.asyncio
async def test_collecting_media_does_not_store_original_file_id_when_reupload_fails(mock_bot_client):
    commands.conversation_states.clear()
    commands.conversation_states[123] = {"command": "collecting_source", "source_id": 7, "post_count": 0}
    mock_bot_client.reupload_media = AsyncMock(side_effect=Exception("Failed to download file: 502"))

    message = {
        "new_message": {
            "message_id": "msg-1",
            "text": "caption",
            "file": {
                "file_id": "original-user-file-id",
                "mime": "image/jpeg",
                "file_name": "post.jpg",
            },
        }
    }

    with patch("src.database.pool", object()):
        with patch("src.core.source_service.SourceService.add_post", new_callable=AsyncMock) as add_post:
            await commands.handle_source_collecting_message(mock_bot_client, 123, message)

    add_post.assert_not_awaited()
    assert commands.conversation_states[123]["post_count"] == 0
    assert "آپلود" in mock_bot_client.send_message.await_args.args[1]


@pytest.mark.asyncio
async def test_voice_reupload_preserves_ogg_filename_for_voice_playback():
    with patch("src.bot.main.BotClient") as bot_client:
        client = RubikaClient("token")

    client._bot.get_file = AsyncMock(return_value="https://cdn.example/voice")
    client._bot.request_send_file = AsyncMock(return_value="upload-url")
    client._cdn_upload = AsyncMock(return_value="new-file-id")

    with patch("aiohttp.ClientSession", _FakeClientSession):
        new_file_id = await client.reupload_media("old-file-id", "voice")

    assert new_file_id == "new-file-id"
    client._bot.request_send_file.assert_awaited_once_with("Voice")
    assert client._cdn_upload.await_args.args[1] == "media.ogg"


@pytest.mark.asyncio
async def test_execution_engine_voice_reupload_preserves_ogg_filename(mock_db, mock_bot_client):
    engine = ExecutionEngine(mock_db, mock_bot_client)
    mock_bot_client._bot.get_file = AsyncMock(return_value="https://cdn.example/voice")
    mock_bot_client._bot.request_send_file = AsyncMock(return_value="upload-url")
    mock_bot_client._cdn_upload = AsyncMock(return_value="new-file-id")

    with patch("aiohttp.ClientSession", _FakeClientSession):
        new_file_id = await engine._reupload_file("old-file-id", "voice", 9)

    assert new_file_id == "new-file-id"
    mock_bot_client._bot.request_send_file.assert_awaited_once_with("Voice")
    assert mock_bot_client._cdn_upload.await_args.args[1] == "media.ogg"


@pytest.mark.asyncio
async def test_addsource_collecting_prompt_warns_about_forwarded_sender_labels(mock_bot_client, mock_db):
    commands.conversation_states.clear()

    fake_source = type("Source", (), {"id": 7})()
    with patch("src.database.pool", mock_db):
        with patch("src.bot.commands._db_uid", new_callable=AsyncMock, return_value=3):
            with patch("src.core.source_service.SourceService.create_source", new_callable=AsyncMock, return_value=fake_source):
                await commands.handle_source_name_input(mock_bot_client, 123, "آموزشی")

    text = mock_bot_client.send_message.await_args.args[1]
    assert "فوروارد" in text
    assert "برچسب" in text
    assert "پنهان" in text
