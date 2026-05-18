"""Tests for collecting source posts."""

import pytest
from unittest.mock import AsyncMock, patch

from src.bot import commands


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
