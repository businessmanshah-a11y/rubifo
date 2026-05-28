import re
from src.logger import logger
from src.bot import commands


async def _log_action(user_id: str, action: str, message: str, level: str = "info") -> None:
    """Insert a user action log entry into the logs table."""
    try:
        from src.database import execute
        await execute(
            """
            INSERT INTO logs (level, user_id, action, message)
            VALUES ($1, $2, $3, $4)
            """,
            level, user_id, action, message[:2000],
        )
    except Exception as e:
        logger.warning(f"Failed to write action log: {e}")


BUTTON_COMMAND_MAP = {
    "📦 سورس‌های من": "/mysources",
    "📍 کانال‌های من": "/my_destinations",
    "📋 مسیرهای من": "/listroutes",
    "📅 پلن‌های من": "/listplans",
    "📊 تقویم محتوایی": "/calendar",
    "💳 اشتراک": "/subscription_status",
    "❓ راهنما": "/help",
    # Backward compatibility
    "✏️ سورس جدید": "/addsource",
    "➕ مسیر جدید": "/addroute",
    "💳 خرید اشتراک": "/buy",
    "📅 برنامه‌ریزی": "/listplans",
    "📊 گزارش‌ها": "/logs",
}

# Rubika SIMPLE buttons send their label text as the message (not button_id).
# These patterns match the dynamic inline button labels and extract the channel.
_INLINE_BTN_PATTERNS = [
    (re.compile(r"^📋 مسیرها \((.+)\)$"), "routes"),
    (re.compile(r"^📅 پلن‌ها \((.+)\)$"), "plans"),
    (re.compile(r"^📊 تقویم \((.+)\)$"), "cal"),
    (re.compile(r"^➕ مسیر جدید \((.+)\)$"), "addroute"),
]

# Pattern for mysources inline buttons: "📝 #5 پست‌ها" and "➕ #5 افزودن"
_VIEWSOURCE_BTN = re.compile(r"^📝 #(\d+) پست‌ها$")
_ADDPOST_BTN = re.compile(r"^➕ #(\d+) افزودن$")

# Pattern for calendar channel selection: "1️⃣ @channel", "2️⃣ @channel", etc.
_CAL_SELECT_BTN = re.compile(r"^[1-9️⃣️]+\s+(@\S+)$")


async def _route_inline_button(client, user_id: str, text: str) -> bool:
    """Try to route dynamic inline button text. Returns True if matched."""
    # Per-destination hub buttons
    for pattern, action in _INLINE_BTN_PATTERNS:
        m = pattern.match(text)
        if m:
            channel = m.group(1)
            if action == "routes":
                await commands.handle_destination_routes(client, user_id, channel)
            elif action == "plans":
                await commands.handle_destination_plans(client, user_id, channel)
            elif action == "cal":
                await commands.handle_calendar_display(client, user_id, channel)
            elif action == "addroute":
                await commands.handle_addroute_for_channel(client, user_id, channel)
            return True

    # Mysources inline buttons
    m = _VIEWSOURCE_BTN.match(text)
    if m:
        await commands.handle_viewsource(client, user_id, int(m.group(1)))
        return True

    m = _ADDPOST_BTN.match(text)
    if m:
        await commands.handle_addpost(client, user_id, int(m.group(1)))
        return True

    # Calendar channel selection buttons
    m = _CAL_SELECT_BTN.match(text)
    if m:
        await commands.handle_calendar_display(client, user_id, m.group(1))
        return True

    return False


async def route_message(client, user_id: str, message: dict) -> None:
    """Route incoming messages to appropriate command handlers."""
    try:
        text = (message.get("text") or "").strip()

        # ── log every incoming message ──────────────────────────────────────
        if text:
            action = text if text.startswith("/") else "message"
            await _log_action(user_id, action, text)

        # ── collecting_source: handle ALL messages (media + text) ──────────
        state = commands.conversation_states.get(user_id, {})
        if state.get("command") == "collecting_source":
            if text == "/savesource":
                await commands.handle_savesource(client, user_id)
                return
            elif text.startswith("/"):
                # Any other command cancels collecting mode
                del commands.conversation_states[user_id]
                # fall through to normal command handling
            else:
                # Any non-command message (text, media, forwarded) → add to source
                await commands.handle_source_collecting_message(client, user_id, message)
                return

        # ── dynamic inline button routing (button label text patterns) ─────
        # Must run BEFORE BUTTON_COMMAND_MAP so dynamic labels aren't lost
        if not text.startswith("/") and text not in BUTTON_COMMAND_MAP:
            handled = await _route_inline_button(client, user_id, text)
            if handled:
                return

        # ── map keyboard button text → command ─────────────────────────────
        if text in BUTTON_COMMAND_MAP:
            text = BUTTON_COMMAND_MAP[text]

        # ── active text-based conversation ─────────────────────────────────
        if user_id in commands.conversation_states:
            if not text.startswith("/"):
                await commands.handle_conversation_response(client, user_id, text)
                return
            else:
                # New command cancels any active conversation
                del commands.conversation_states[user_id]

        # ── command dispatch ────────────────────────────────────────────────
        if not text.startswith("/"):
            return

        parts = text.split()
        cmd = parts[0].lower()

        if cmd == "/start":
            await commands.handle_start(client, user_id)
        elif cmd == "/addsource":
            await commands.handle_addsource(client, user_id)
        elif cmd == "/savesource":
            await commands.handle_savesource(client, user_id)
        elif cmd == "/mysources":
            await commands.handle_mysources(client, user_id)
        elif cmd == "/my_destinations":
            await commands.handle_my_destinations(client, user_id)
        elif cmd == "/subscription_status":
            await commands.handle_subscription_status(client, user_id)
        elif cmd == "/viewsource" and len(parts) > 1:
            await commands.handle_viewsource(client, user_id, int(parts[1]))
        elif cmd == "/addpost" and len(parts) > 1:
            await commands.handle_addpost(client, user_id, int(parts[1]))
        elif cmd == "/removepost" and len(parts) > 1:
            await commands.handle_removepost(client, user_id, int(parts[1]))
        elif cmd == "/deletesource" and len(parts) > 1:
            await commands.handle_deletesource(client, user_id, int(parts[1]))
        elif cmd == "/addroute":
            await commands.handle_addroute(client, user_id)
        elif cmd == "/listroutes":
            await commands.handle_listroutes(client, user_id)
        elif cmd == "/removeroute" and len(parts) > 1:
            await commands.handle_removeroute(client, user_id, int(parts[1]))
        elif cmd == "/buy":
            await commands.handle_buy(client, user_id)
        elif cmd == "/buy_basic":
            await commands.handle_buy_basic(client, user_id)
        elif cmd == "/buy_pro":
            await commands.handle_buy_pro(client, user_id)
        elif cmd == "/buy_enterprise":
            await commands.handle_buy_enterprise(client, user_id)
        elif cmd == "/renew":
            await commands.handle_renew(client, user_id)
        elif cmd == "/addplan":
            await commands.handle_addplan(client, user_id)
        elif cmd == "/listplans":
            await commands.handle_listplans(client, user_id)
        elif cmd == "/editplan" and len(parts) > 1:
            await commands.handle_editplan(client, user_id, int(parts[1]))
        elif cmd == "/removeplan" and len(parts) > 1:
            await commands.handle_removeplan(client, user_id, int(parts[1]))
        elif cmd == "/toggleplan" and len(parts) > 1:
            await commands.handle_toggleplan(client, user_id, int(parts[1]))
        elif cmd == "/logs":
            await commands.handle_logs(client, user_id)
        elif cmd == "/calendar":
            await commands.handle_calendar(client, user_id)
        elif cmd == "/help":
            await commands.handle_help(client, user_id)
        else:
            await client.send_message(user_id, "دستور نامشخص. /help را بفرستید.")

    except ValueError:
        await _log_action(user_id, "error", "ValueError in route_message", level="error")
        await client.send_message(user_id, "فرمت دستور اشتباه است.")
    except Exception as e:
        logger.error(f"Error routing message from {user_id}: {e}")
        await _log_action(user_id, "error", str(e), level="error")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")
