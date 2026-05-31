"""End-to-end tests for bot commands (T69)."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from src.bot import commands, handlers
from src.bot import main as bot_main
from src.bot.main import RubikaBotApiClient


@pytest.mark.asyncio
class TestBotStartCommand:
    """Test /start command E2E."""

    async def test_start_command_new_user(self, mock_bot_client, mock_db):
        """Test /start with new user."""
        mock_db.fetchrow.return_value = {
            "id": 1,
            "user_id": 123456789,
            "username": "testuser",
            "trial_start_at": datetime.now(),
            "trial_end_at": datetime.now() + timedelta(hours=72),
            "is_trial_active": True,
            "phone_number": None,
            "password_hash": None,
            "onboarding_completed_at": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        mock_db.execute.return_value = None

        with patch("src.database.pool", mock_db):
            await commands.handle_start(mock_bot_client, 123456789, "testuser")

        assert mock_bot_client.send_message.called
        message = mock_bot_client.send_message.call_args.args[1]
        assert "شماره تماس" in message
        assert commands.conversation_states[123456789]["command"] == "web_onboarding_phone"

    async def test_start_command_existing_user_with_web_credentials(self, mock_bot_client, mock_db):
        """Existing onboarded users see the regular welcome."""
        mock_db.fetchrow.return_value = {
            "id": 1,
            "user_id": 123456789,
            "username": "testuser",
            "trial_start_at": datetime.now(),
            "trial_end_at": datetime.now() + timedelta(hours=72),
            "is_trial_active": True,
            "phone_number": "09123456789",
            "password_hash": "$2b$12$abcdefghijklmnopqrstuu4YlTEPm.yp3MB7Dd3UtDm5.86iA/5PS",
            "onboarding_completed_at": datetime.now(),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        with patch("src.database.pool", mock_db):
            await commands.handle_start(mock_bot_client, 123456789, "testuser")

        assert mock_bot_client.send_message.called
        message = mock_bot_client.send_message.call_args.args[1]
        assert "برنامه انتشار" in message
        assert "دسته محتوا" in message
        assert "ادمین" in message
        assert "➕ ایجاد برنامه جدید انتشار محتوا" in message
        assert "مسیر" not in message
        assert "سورس" not in message
        assert mock_bot_client.send_message.call_args.kwargs["inline_keypad"] is not None

    async def test_start_command_existing_user(self, mock_bot_client, mock_db):
        """Test /start with existing user."""
        user_data = {
            "id": 1,
            "user_id": 123456789,
            "username": "testuser",
            "trial_start_at": datetime.now(),
            "trial_end_at": datetime.now() + timedelta(hours=24),
            "is_trial_active": True,
            "phone_number": "09123456789",
            "password_hash": "$2b$12$abcdefghijklmnopqrstuu4YlTEPm.yp3MB7Dd3UtDm5.86iA/5PS",
            "onboarding_completed_at": datetime.now(),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        mock_db.fetchrow.return_value = user_data

        with patch("src.database.pool", mock_db):
            await commands.handle_start(mock_bot_client, 123456789, "testuser")

        assert mock_bot_client.send_message.called
        call_args = mock_bot_client.send_message.call_args
        assert "تریال" in str(call_args)
        assert "برنامه انتشار" in str(call_args)

    async def test_start_command_paid_user_does_not_show_trial_warning(self, mock_bot_client, mock_db):
        """Paid users should see paid subscription status on /start, not trial copy."""
        user = SimpleNamespace(
            phone_number="09123456789",
            password_hash="$2b$12$abcdefghijklmnopqrstuu4YlTEPm.yp3MB7Dd3UtDm5.86iA/5PS",
            onboarding_completed_at=datetime.now(),
            is_trial_active=True,
            trial_end_at=datetime.now() + timedelta(hours=2),
        )
        status = {
            "status": "active",
            "tier": "enterprise",
            "end_date": date.today() + timedelta(days=90),
            "days_left": 90,
            "hours_left": 0,
            "destinations_used": 1,
            "destinations_limit": 10,
        }

        with patch("src.database.pool", mock_db):
            with patch(
                "src.core.user_service.UserService.get_or_create_user",
                new_callable=AsyncMock,
                return_value=user,
            ):
                with patch(
                    "src.core.subscription_service.SubscriptionService.get_subscription_status",
                    new_callable=AsyncMock,
                    return_value=status,
                ):
                    await commands.handle_start(mock_bot_client, 123456789, "testuser")

        message = mock_bot_client.send_message.call_args.args[1]
        assert "پلن مقیاس" in message
        assert "۹۰ روز باقیمانده" in message or "90 روز باقیمانده" in message
        assert "تریال" not in message

    async def test_onboarding_rejects_invalid_phone_and_keeps_state(self, mock_bot_client):
        """Invalid phone numbers keep the user in the phone step."""
        user_id = 123456789
        commands.conversation_states[user_id] = {"command": "web_onboarding_phone"}

        await commands.handle_conversation_response(mock_bot_client, user_id, "12345")

        assert commands.conversation_states[user_id]["command"] == "web_onboarding_phone"
        assert "09" in mock_bot_client.send_message.call_args.args[1]

    async def test_onboarding_password_completes_credentials(self, mock_bot_client, mock_db):
        """A valid password stores hashed credentials and completes onboarding."""
        user_id = 123456789
        commands.conversation_states[user_id] = {
            "command": "web_onboarding_password",
            "phone_number": "09123456789",
        }

        with patch("src.database.pool", mock_db):
            await commands.handle_conversation_response(mock_bot_client, user_id, "secret123")

        assert user_id not in commands.conversation_states
        query, saved_phone, saved_hash, saved_user_id = mock_db.execute.call_args.args
        assert "phone_number" in query
        assert saved_phone == "09123456789"
        assert saved_hash != "secret123"
        assert saved_user_id == user_id
        assert "ثبت شد" in mock_bot_client.send_message.call_args.args[1]


@pytest.mark.asyncio
class TestBotBuyCommand:
    """Test /buy command E2E."""

    async def test_buy_command_shows_tiers(self, mock_bot_client, mock_db):
        """Test /buy sends the website checkout link."""
        mock_db.fetchrow.return_value = None

        with patch("src.database.pool", mock_db):
            await commands.handle_buy(mock_bot_client, 123456789)

        assert mock_bot_client.send_message.called
        message = mock_bot_client.send_message.call_args.args[1]
        assert "/checkout" in message
        assert "StartPay" not in message

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
        mock_db.fetchrow.return_value = {"id": 1, "user_id": 123456789}
        mock_db.fetch.return_value = []

        with patch("src.database.pool", mock_db):
            await commands.handle_addroute(mock_bot_client, 123456789)

        assert mock_bot_client.send_message.called
        message = mock_bot_client.send_message.call_args.args[1]
        assert "ابتدا باید یک سورس بسازید" in message

    async def test_addroute_does_not_check_destination_limit_before_target_input(self, mock_bot_client, mock_db):
        """Route creation asks for a source before enforcing destination limits."""
        mock_db.fetchrow.return_value = {"id": 1, "user_id": 123456789}
        mock_db.fetch.return_value = [
            {
                "id": 10,
                "user_id": 1,
                "name": "کمپین",
                "is_active": True,
                "created_at": datetime.now(),
            }
        ]

        with patch("src.database.pool", mock_db):
            with patch("src.core.source_service.SourceService.count_posts", new_callable=AsyncMock) as mock_count:
                with patch("src.core.route_service.RouteService.can_create_route", new_callable=AsyncMock) as mock_can_create:
                    mock_count.return_value = 4
                    await commands.handle_addroute(mock_bot_client, 123456789)

        mock_can_create.assert_not_called()
        message = mock_bot_client.send_message.call_args.args[1]
        assert "کدام سورس" in message

    async def test_addroute_blocks_new_destination_after_target_input_when_limit_full(self, mock_bot_client, mock_db):
        """Destination limit is enforced after target normalization."""
        user_id = 123456789
        commands.conversation_states[user_id] = {
            "command": "addroute",
            "step": 2,
            "source_id": 10,
            "source_name": "کمپین",
        }

        with patch("src.database.pool", mock_db):
            with patch("src.core.route_service.RouteService.can_create_route", new_callable=AsyncMock) as mock_can_create:
                with patch("src.core.route_service.RouteService.create_route", new_callable=AsyncMock) as mock_create:
                    mock_can_create.return_value = (False, "شما حداکثر 1 کانال مقصد دارید.")
                    await commands.handle_addroute_conversation(
                        mock_bot_client,
                        user_id,
                        "https://rubika.ir/new_dest",
                    )

        mock_can_create.assert_awaited_once_with(user_id, "@new_dest")
        mock_create.assert_not_called()
        message = mock_bot_client.send_message.call_args.args[1]
        assert "کانال مقصد" in message

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

    async def test_trial_user_sees_professional_plan_lock(self, mock_bot_client, mock_db):
        """Trial users can see professional options but cannot enter them."""
        user_id = 123456789
        commands.conversation_states[user_id] = {
            "command": "addplan_type_select",
            "route_id": 1,
        }
        mock_db.fetchrow.side_effect = [
            None,
            {"is_trial_active": True, "trial_end_at": datetime.now() + timedelta(hours=24)},
        ]

        with patch("src.database.pool", mock_db):
            await commands.handle_addplan_type_selection(mock_bot_client, user_id, "3")

        assert commands.conversation_states[user_id]["command"] == "addplan_type_select"
        message = mock_bot_client.send_message.call_args.args[1]
        assert "در تریال" in message
        assert "پلن‌های حرفه‌ای بعد از خرید فعال می‌شوند" in message

    async def test_paid_user_can_enter_professional_plan_flow(self, mock_bot_client, mock_db):
        """Paid users can create professional plans."""
        user_id = 123456789
        commands.conversation_states[user_id] = {
            "command": "addplan_type_select",
            "route_id": 1,
        }
        mock_db.fetchrow.return_value = {
            "tier": "pro",
            "end_date": datetime.now().date() + timedelta(days=20),
        }

        with patch("src.database.pool", mock_db):
            await commands.handle_addplan_type_selection(mock_bot_client, user_id, "3")

        assert commands.conversation_states[user_id]["command"] == "addplan_professional_input"
        assert commands.conversation_states[user_id]["plan_kind"] == "campaign"

    async def test_trial_daily_count_auto_distributes_times(self, mock_bot_client, mock_db):
        """Simple daily count asks only for count and auto-generates distribution times."""
        user_id = 123456789
        commands.conversation_states[user_id] = {
            "command": "addplan_daily_count",
            "route_id": 1,
            "sub_step": 1,
        }

        with patch("src.database.pool", mock_db):
            with patch("src.core.schedule_service.ScheduleService.create_schedule", new_callable=AsyncMock) as mock_create:
                mock_create.return_value.next_run = datetime.now() + timedelta(hours=1)
                await commands.handle_addplan_daily_count_input(mock_bot_client, user_id, "3")

        _, kwargs = mock_create.call_args
        assert kwargs["daily_count"] == 3
        assert kwargs["times"] == [(9, 0), (13, 40), (18, 20)]
        assert user_id not in commands.conversation_states

    async def test_addplan_route_selection_accepts_persian_digits(self, mock_bot_client):
        """Route selection maps Persian digits to saved ASCII route keys."""
        user_id = 123456789
        commands.conversation_states[user_id] = {
            "command": "addplan_route_select",
            "route_map": {"1": 42},
        }

        await commands.handle_addplan_route_selection(mock_bot_client, user_id, "۱")

        assert commands.conversation_states[user_id]["route_id"] == 42
        assert commands.conversation_states[user_id]["command"] == "addplan_type_select"

    async def test_addplan_type_selection_accepts_persian_digits(self, mock_bot_client):
        """Plan type selection accepts Persian digits from Farsi keyboards."""
        user_id = 123456789
        commands.conversation_states[user_id] = {
            "command": "addplan_type_select",
            "route_id": 42,
        }

        await commands.handle_addplan_type_selection(mock_bot_client, user_id, "۲")

        assert commands.conversation_states[user_id]["command"] == "addplan_daily_count"
        assert commands.conversation_states[user_id]["sub_step"] == 1

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
        message = mock_bot_client.send_message.call_args.args[1]
        # Should contain help text
        assert "دستور" in message or "command" in message
        assert "حذف ادمین بارگذاری" in message
        assert "آپلود دستی" in message

    async def test_calendar_command(self, mock_bot_client, mock_db):
        """Test /calendar command."""
        mock_db.fetch.return_value = []

        with patch("src.database.pool", mock_db):
            await commands.handle_calendar(mock_bot_client, 123456789)

        assert mock_bot_client.send_message.called

    async def test_calendar_display_uses_jalali_dates(self, mock_bot_client, mock_db):
        """Calendar day headers and times use Jalali display with Persian digits."""
        mock_db.fetch.side_effect = [
            [{"id": 1}],
            [
                {
                    "id": 9,
                    "route_id": 1,
                    "schedule_type": "publishing_program",
                    "plan_kind": "publishing_program",
                    "config": {"program_mode": "recurring", "cadence": "interval", "interval_minutes": 60},
                    "interval_minutes": 60,
                    "daily_count": None,
                    "next_run": datetime(2026, 5, 20, 8, 30),
                    "is_active": True,
                    "paused_reason": None,
                    "program_purpose": "real",
                    "source_name": "رضایت مشتری",
                }
            ],
        ]
        mock_db.fetchval.return_value = 2

        with patch("src.database.pool", mock_db):
            await commands.handle_calendar_display(mock_bot_client, 123456789, "@shop")

        message = mock_bot_client.send_message.await_args.args[1]
        assert "۱۴۰۵/۰۲/۳۰" in message
        assert "۱۲:۰۰" in message
        assert "2026/05/20" not in message

    async def test_destination_plans_use_jalali_next_run(self, mock_bot_client, mock_db):
        """Destination plan summaries render next_run as Jalali."""
        mock_db.fetch.return_value = [
            {
                "is_active": True,
                "plan_kind": "publishing_program",
                "schedule_type": "publishing_program",
                "config": {"program_mode": "recurring", "cadence": "interval", "interval_minutes": 60},
                "next_run": datetime(2026, 5, 20, 8, 30),
                "paused_reason": None,
                "source_name": "رضایت مشتری",
            }
        ]

        with patch("src.database.pool", mock_db):
            await commands.handle_destination_plans(mock_bot_client, 123456789, "@shop")

        message = mock_bot_client.send_message.await_args.args[1]
        assert "۰۲/۳۰ ۱۲:۰۰" in message
        assert "05/20" not in message

    async def test_subscription_status_uses_jalali_end_date(self, mock_bot_client, mock_db):
        """Subscription end dates shown to users are Jalali."""
        status = {
            "status": "active",
            "tier": "basic",
            "end_date": date(2026, 5, 20),
            "days_left": 10,
            "hours_left": 240,
            "destinations_used": 1,
            "destinations_limit": 1,
        }

        with patch("src.database.pool", mock_db):
            with patch(
                "src.core.subscription_service.SubscriptionService.get_subscription_status",
                new_callable=AsyncMock,
                return_value=status,
            ):
                await commands.handle_subscription_status(mock_bot_client, 123456789)

        message = mock_bot_client.send_message.await_args.args[1]
        assert "تاریخ پایان: ۱۴۰۵/۰۲/۳۰" in message
        assert "2026-05-20" not in message

    async def test_active_subscription_status_has_action_buttons_and_no_trial_warning(self, mock_bot_client, mock_db):
        """Paid users should not see trial warning copy and should get renewal/upgrade buttons."""
        status = {
            "status": "active",
            "tier": "enterprise",
            "end_date": date.today() + timedelta(days=90),
            "days_left": 90,
            "hours_left": 2160,
            "destinations_used": 3,
            "destinations_limit": 10,
        }

        with patch("src.database.pool", mock_db):
            with patch(
                "src.core.subscription_service.SubscriptionService.get_subscription_status",
                new_callable=AsyncMock,
                return_value=status,
            ):
                await commands.handle_subscription_status(mock_bot_client, 123456789)

        message = mock_bot_client.send_message.await_args.args[1]
        assert "تریال" not in message
        assert "۹۰ روز باقیمانده" in message or "90 روز باقیمانده" in message
        inline_keypad = mock_bot_client.send_message.await_args.kwargs["inline_keypad"]
        button_texts = [
            button.button_text
            for row in inline_keypad.rows
            for button in row.buttons
        ]
        button_ids = [
            button.id
            for row in inline_keypad.rows
            for button in row.buttons
        ]
        assert "🔄 تمدید اشتراک" in button_texts
        assert "⬆️ ارتقا / تغییر پلن" in button_texts
        assert "/renew" in button_ids
        assert "/buy" in button_ids

    async def test_checkout_urls_use_public_site_not_localhost(self):
        """Bot payment links must send real Rubika users to the public plans page."""
        assert commands._checkout_url("enterprise") == "https://rubifo.ir/#plans"
        assert "localhost" not in commands._checkout_url("enterprise")
        assert "rubifo.datayar.ir" not in commands._checkout_url("enterprise")

    async def test_trial_reminder_query_excludes_paid_users(self):
        """Trial reminder candidates must not include users with active paid subscriptions."""
        query = bot_main._trial_reminder_candidates_query()

        assert "NOT EXISTS" in query
        assert "FROM subscriptions" in query
        assert "is_active = true" in query

    async def test_logs_command(self, mock_bot_client, mock_db):
        """Test /logs command."""
        mock_db.fetch.return_value = []

        with patch("src.database.pool", mock_db):
            await commands.handle_logs(mock_bot_client, 123456789)

        assert mock_bot_client.send_message.called

    async def test_logs_empty_state_uses_publishing_program_language(self, mock_bot_client, mock_db):
        """Empty activity report should not send users back to source/route commands."""
        mock_db.fetchrow.return_value = {
            "total_sent": 0,
            "total_failed": 0,
            "total_pending": 0,
            "today_sent": 0,
            "today_failed": 0,
        }
        mock_db.fetch.return_value = []

        with patch("src.database.pool", mock_db):
            await commands.handle_logs(mock_bot_client, 123456789)

        message = mock_bot_client.send_message.call_args.args[1]
        assert "ساخت برنامه جدید" in message
        assert "دسته محتوا" in message
        assert "سورس" not in message
        assert "مسیر" not in message


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

    async def test_old_route_keypad_button_opens_publishing_programs(self, mock_bot_client, mock_db):
        """Legacy route button should no longer expose the route-management UI."""
        message = {"text": "📋 مسیرهای من"}

        with patch("src.database.pool", mock_db):
            with patch("src.bot.commands.handle_listplans", new_callable=AsyncMock) as list_programs:
                with patch("src.bot.commands.handle_listroutes", new_callable=AsyncMock) as list_routes:
                    await handlers.route_message(mock_bot_client, 123456789, message)

        list_programs.assert_awaited_once()
        list_routes.assert_not_awaited()

    async def test_old_new_route_button_starts_program_wizard(self, mock_bot_client, mock_db):
        """Legacy new-route button should enter the new publishing-program wizard."""
        message = {"text": "➕ مسیر جدید"}

        with patch("src.database.pool", mock_db):
            with patch("src.bot.publishing_flow.begin_program", new_callable=AsyncMock) as begin_program:
                with patch("src.bot.commands.handle_addroute", new_callable=AsyncMock) as add_route:
                    await handlers.route_message(mock_bot_client, 123456789, message)

        begin_program.assert_awaited_once_with(mock_bot_client, 123456789)
        add_route.assert_not_awaited()

    async def test_old_destination_new_route_inline_starts_program_wizard(self, mock_bot_client, mock_db):
        """Legacy per-channel new-route inline text should start program creation."""
        message = {"text": "➕ مسیر جدید (@shop)"}

        with patch("src.database.pool", mock_db):
            with patch("src.bot.publishing_flow.begin_program", new_callable=AsyncMock) as begin_program:
                with patch("src.bot.commands.handle_addroute_for_channel", new_callable=AsyncMock) as add_route:
                    await handlers.route_message(mock_bot_client, 123456789, message)

        begin_program.assert_awaited_once_with(mock_bot_client, 123456789)
        add_route.assert_not_awaited()

    async def test_legacy_addroute_command_starts_program_wizard(self, mock_bot_client, mock_db):
        """Typing old route/setup commands should not expose the legacy wizard."""
        message = {"text": "/addroute"}

        with patch("src.database.pool", mock_db):
            with patch("src.bot.publishing_flow.begin_program", new_callable=AsyncMock) as begin_program:
                with patch("src.bot.commands.handle_addroute", new_callable=AsyncMock) as add_route:
                    await handlers.route_message(mock_bot_client, 123456789, message)

        begin_program.assert_awaited_once_with(mock_bot_client, 123456789)
        add_route.assert_not_awaited()

    async def test_legacy_addplan_command_starts_program_wizard(self, mock_bot_client, mock_db):
        """Typing old plan command should enter program creation instead of route selection."""
        message = {"text": "/addplan"}

        with patch("src.database.pool", mock_db):
            with patch("src.bot.publishing_flow.begin_program", new_callable=AsyncMock) as begin_program:
                with patch("src.bot.commands.handle_addplan", new_callable=AsyncMock) as add_plan:
                    await handlers.route_message(mock_bot_client, 123456789, message)

        begin_program.assert_awaited_once_with(mock_bot_client, 123456789)
        add_plan.assert_not_awaited()

    async def test_route_numeric_command_accepts_persian_digits(self, mock_bot_client, mock_db):
        """Slash commands with numeric IDs accept Persian digits."""
        message = {"text": "/editplan ۱۲"}

        with patch("src.database.pool", mock_db):
            with patch("src.bot.commands.handle_editplan", new_callable=AsyncMock) as edit_plan:
                await handlers.route_message(mock_bot_client, 123456789, message)

        edit_plan.assert_awaited_once_with(mock_bot_client, 123456789, 12)

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
