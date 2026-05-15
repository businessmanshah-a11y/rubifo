from typing import Optional
from src.logger import logger
from src.bot import commands


async def route_message(client, user_id: int, message: dict) -> None:
    """Route incoming messages to appropriate command handlers."""
    try:
        text = message.get("text", "").strip()

        # Check if user is in an active conversation
        if user_id in commands.conversation_states:
            if not text.startswith("/"):
                await commands.handle_conversation_response(client, user_id, text)
                return
            else:
                # Cancel conversation if user sends a command
                del commands.conversation_states[user_id]

        if text.startswith("/"):
            parts = text.split()
            command = parts[0].lower()

            if command == "/start":
                await commands.handle_start(client, user_id)
            elif command == "/buy":
                await commands.handle_buy(client, user_id)
            elif command == "/buy_basic":
                await commands.handle_buy_basic(client, user_id)
            elif command == "/buy_pro":
                await commands.handle_buy_pro(client, user_id)
            elif command == "/buy_enterprise":
                await commands.handle_buy_enterprise(client, user_id)
            elif command == "/help":
                await commands.handle_help(client, user_id)
            elif command == "/addroute":
                await commands.handle_addroute(client, user_id)
            elif command == "/listroutes":
                await commands.handle_listroutes(client, user_id)
            elif command == "/removeroute" and len(parts) > 1:
                try:
                    route_id = int(parts[1])
                    await commands.handle_removeroute(client, user_id, route_id)
                except (ValueError, IndexError):
                    await client.send_message(user_id, "فرمت دستور اشتباه است.")
            elif command == "/updatesource" and len(parts) > 1:
                try:
                    route_id = int(parts[1])
                    await commands.handle_updatesource(client, user_id, route_id)
                except (ValueError, IndexError):
                    await client.send_message(user_id, "فرمت دستور اشتباه است.")
            elif command == "/sync" and len(parts) > 1:
                try:
                    route_id = int(parts[1])
                    await commands.handle_sync(client, user_id, route_id)
                except (ValueError, IndexError):
                    await client.send_message(user_id, "فرمت دستور اشتباه است.")
            elif command == "/addplan":
                await commands.handle_addplan(client, user_id)
            elif command == "/listplans":
                await commands.handle_listplans(client, user_id)
            elif command == "/editplan" and len(parts) > 1:
                try:
                    schedule_id = int(parts[1])
                    await commands.handle_editplan(client, user_id, schedule_id)
                except (ValueError, IndexError):
                    await client.send_message(user_id, "فرمت دستور اشتباه است.")
            elif command == "/removeplan" and len(parts) > 1:
                try:
                    schedule_id = int(parts[1])
                    await commands.handle_removeplan(client, user_id, schedule_id)
                except (ValueError, IndexError):
                    await client.send_message(user_id, "فرمت دستور اشتباه است.")
            elif command == "/toggleplan" and len(parts) > 1:
                try:
                    schedule_id = int(parts[1])
                    await commands.handle_toggleplan(client, user_id, schedule_id)
                except (ValueError, IndexError):
                    await client.send_message(user_id, "فرمت دستور اشتباه است.")
            elif command == "/renew":
                await commands.handle_renew(client, user_id)
            else:
                await client.send_message(user_id, "دستور نامشخص. /help را بفرستید.")

    except Exception as e:
        logger.error(f"Error routing message from {user_id}: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")
