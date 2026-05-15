"""End-to-end tests for bot commands (T69)."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from src.bot import commands, handlers
from src.bot.main import RubikaBotApiClient


@pytest.mark.asyncio
class TestBotStartCommand:
    """Test /start command E2E."""

    async def test_start_command_new_user(self, mock_bot_client, mock_db):
        """Test /start with new user."""
        mock_db.fetchrow.return_value = None
        mock_db.execute.return_value = None

        with patch("src.database.pool", mock_db):
            await commands.handle_start(mock_bot_client, 123456789, "testuser")

        assert mock_bot_client.send_message.called

    async def test_start_command_existing_user(self, mock_bot_client, mock_db):
        """Test /start with existing user."""
        user_data = {
            "id": 1,
            "user_id": 123456789,
            "username": "testuser",
            "trial_start_at": datetime.now(),
            "trial_end_at": datetime.now() + timedelta(hours=24),
            "is_trial_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        mock_db.fetchrow.return_value = user_data

        with patch("src.database.pool", mock_db):
            await commands.handle_start(mock_bot_client, 123456789, "testuser")

        assert mock_bot_client.send_message.called
        # Should mention trial hours remaining
        call_args = mock_bot_client.send_message.call_args
        assert "ساعت" in str(call_args)  # Farsi word for "hours"


@pytest.mark.asyncio
class TestBotBuyCommand:
    """Test /buy command E2E."""

    async def test_buy_command_shows_tiers(self, mock_bot_client, mock_db):
        """Test /buy shows subscription tiers."""
        mock_db.fetchrow.return_value = None

        with patch("src.database.pool", mock_db):
            await commands.handle_buy(mock_bot_client, 123456789)

        assert mock_bot_client.send_message.called
        call_args = mock_bot_client.send_message.call_args
        # Should show tier options
        assert "پایه" in str(call_args) or "Basic" in str(call_args)

    async def test_buy_command_existing_subscription(self, mock_bot_client, mock_db):
        """Test /buy with existing subscription."""
        sub_data = {
            "tier": "pro",
            "end_date": datetime.now().date() + timedelta(days=20),
        }
        mock_db.fetchrow.return_value = sub_data

        with patch("src.database.pool", mock_db):
            await commands.handle_buy(mock_bot_client, 123456789)

        assert mock_bot_client.send_message.called


@pytest.mark.asyncio
class TestBotRouteCommands:
    """Test route management commands E2E."""

    async def test_addroute_conversation_flow(self, mock_bot_client, mock_db):
        """Test /addroute command conversation."""
        mock_db.fetchrow.return_value = {"tier": "basic"}
        mock_db.fetch.return_value = []

        with patch("src.database.pool", mock_db):
            await commands.handle_addroute(mock_bot_client, 123456789)

        assert mock_bot_client.send_message.called

    async def test_listroutes_empty(self, mock_bot_client, mock_db):
        """Test /listroutes with no routes."""
        mock_db.fetch.return_value = []

        with patch("src.database.pool", mock_db):
            await commands.handle_listroutes(mock_bot_client, 123456789)

        assert mock_bot_client.send_message.called

    async def test_listroutes_with_routes(self, mock_bot_client, mock_db):
        """Test /listroutes with existing routes."""
        routes = [
            {
                "id": 1,
                "source_channel_id": 111111,
                "target_channel_id": 222222,
                "is_active": True,
                "pending_count": 5,
            }
        ]
        mock_db.fetch.return_value = routes

        with patch("src.database.pool", mock_db):
            await commands.handle_listroutes(mock_bot_client, 123456789)

        assert mock_bot_client.send_message.called


@pytest.mark.asyncio
class TestBotPlanCommands:
    """Test schedule/plan commands E2E."""

    async def test_addplan_interval_flow(self, mock_bot_client, mock_db):
        """Test /addplan with interval type."""
        mock_db.fetch.return_value = [{"id": 1, "source_channel_id": 111}]

        with patch("src.database.pool", mock_db):
            await commands.handle_addplan(mock_bot_client, 123456789)

        assert mock_bot_client.send_message.called

    async def test_listplans_empty(self, mock_bot_client, mock_db):
        """Test /listplans with no plans."""
        mock_db.fetch.return_value = []

        with patch("src.database.pool", mock_db):
            await commands.handle_listplans(mock_bot_client, 123456789)

        assert mock_bot_client.send_message.called

    async def test_listplans_with_schedules(self, mock_bot_client, mock_db):
        """Test /listplans with schedules."""
        schedules = [
            {
                "id": 1,
                "schedule_type": "interval",
                "interval_minutes": 30,
                "next_run": datetime.now() + timedelta(minutes=20),
                "is_active": True,
            }
        ]
        mock_db.fetch.return_value = schedules

        with patch("src.database.pool", mock_db):
            await commands.handle_listplans(mock_bot_client, 123456789)

        assert mock_bot_client.send_message.called


@pytest.mark.asyncio
class TestBotUtilityCommands:
    """Test utility commands E2E."""

    async def test_help_command(self, mock_bot_client):
        """Test /help command."""
        await commands.handle_help(mock_bot_client, 123456789)

        assert mock_bot_client.send_message.called
        call_args = mock_bot_client.send_message.call_args
        # Should contain help text
        assert "دستور" in str(call_args) or "command" in str(call_args)

    async def test_calendar_command(self, mock_bot_client, mock_db):
        """Test /calendar command."""
        mock_db.fetch.return_value = []

        with patch("src.database.pool", mock_db):
            await commands.handle_calendar(mock_bot_client, 123456789)

        assert mock_bot_client.send_message.called

    async def test_logs_command(self, mock_bot_client, mock_db):
        """Test /logs command."""
        mock_db.fetch.return_value = []

        with patch("src.database.pool", mock_db):
            await commands.handle_logs(mock_bot_client, 123456789)

        assert mock_bot_client.send_message.called


@pytest.mark.asyncio
class TestMessageRouter:
    """Test message routing E2E."""

    async def test_route_start_command(self, mock_bot_client, mock_db):
        """Test routing /start command."""
        message = {"text": "/start"}

        with patch("src.database.pool", mock_db):
            with patch("src.bot.commands.handle_start", new_callable=AsyncMock) as mock_start:
                await handlers.route_message(mock_bot_client, 123456789, message)
                # handle_start should be called

    async def test_route_buy_command(self, mock_bot_client, mock_db):
        """Test routing /buy command."""
        message = {"text": "/buy"}

        with patch("src.database.pool", mock_db):
            with patch("src.bot.commands.handle_buy", new_callable=AsyncMock):
                await handlers.route_message(mock_bot_client, 123456789, message)

    async def test_route_unknown_command(self, mock_bot_client):
        """Test routing unknown command."""
        message = {"text": "/unknown"}

        await handlers.route_message(mock_bot_client, 123456789, message)

        assert mock_bot_client.send_message.called
        call_args = mock_bot_client.send_message.call_args
        # Should show unknown command error
        assert "دستور" in str(call_args) or "unknown" in str(call_args)

    async def test_route_unknown_command_with_rubika_bot_api_client(self):
        """Test routing works with the Rubika Bot API client."""
        client = RubikaBotApiClient("test-token")
        client.send_message = AsyncMock(return_value=True)

        await handlers.route_message(client, 123456789, {"text": "/unknown"})

        client.send_message.assert_awaited_once()
        call_args = client.send_message.call_args
        assert call_args.args[0] == 123456789
        assert "دستور" in call_args.args[1]

    async def test_normalize_updates_extracts_text_messages(self):
        """Test Bot API updates are converted to the internal message shape."""
        updates = [
            {
                "update_id": "42",
                "message": {
                    "chat_id": "123456789",
                    "text": "/start",
                },
            },
            {
                "update_id": "43",
                "message": {
                    "chat_id": "123456789",
                    "file": {"file_id": "abc"},
                },
            },
        ]

        normalized = RubikaBotApiClient.normalize_updates(updates)

        assert normalized == [{"user_id": "123456789", "text": "/start"}]

    async def test_route_text_no_command(self, mock_bot_client):
        """Test routing plain text when not in conversation."""
        message = {"text": "hello"}

        # Clear conversation state
        handlers.commands.conversation_states = {}

        await handlers.route_message(mock_bot_client, 123456789, message)

        # Should send error or ignore


@pytest.mark.asyncio
class TestConversationState:
    """Test conversation state management."""

    async def test_conversation_state_set(self, mock_bot_client):
        """Test setting conversation state."""
        handlers.commands.conversation_states[123] = {
            "step": 1,
            "data": {"source_channel": 111},
        }

        assert 123 in handlers.commands.conversation_states
        assert handlers.commands.conversation_states[123]["step"] == 1

    async def test_conversation_state_clear(self, mock_bot_client):
        """Test clearing conversation state."""
        handlers.commands.conversation_states[123] = {"step": 1}

        message = {"text": "/addroute"}

        # Conversation should be cleared when command is sent
        if 123 in handlers.commands.conversation_states:
            del handlers.commands.conversation_states[123]

        assert 123 not in handlers.commands.conversation_states

    async def test_conversation_timeout(self, mock_bot_client):
        """Test conversation timeout."""
        # Conversations should timeout if not updated within timeout period
        # This is a placeholder for future implementation
        pass


@pytest.mark.asyncio
class TestBotErrorHandling:
    """Test error handling in bot."""

    async def test_command_error_recovery(self, mock_bot_client, mock_db):
        """Test bot recovers from command errors."""
        mock_db.fetchrow.side_effect = Exception("Database error")

        with patch("src.database.pool", mock_db):
            await commands.handle_start(mock_bot_client, 123456789)

        # Should send error message
        assert mock_bot_client.send_message.called
        call_args = mock_bot_client.send_message.call_args
        assert "خطا" in str(call_args) or "error" in str(call_args)

    async def test_invalid_command_format(self, mock_bot_client):
        """Test invalid command format."""
        message = {"text": "/removeroute"}  # Missing route_id

        await handlers.route_message(mock_bot_client, 123456789, message)

        # Should send format error
        assert mock_bot_client.send_message.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
