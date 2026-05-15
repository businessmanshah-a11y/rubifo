from typing import Optional
from src.logger import logger
from src.bot import commands


async def route_message(client, user_id: int, message: dict) -> None:
    """Route incoming messages to appropriate command handlers."""
    try:
        text = message.get("text", "").strip()

        if text.startswith("/"):
            parts = text.split()
            command = parts[0].lower()

            if command == "/start":
                await commands.handle_start(client, user_id)
            elif command == "/buy":
                await commands.handle_buy(client, user_id)
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
            elif command == "/renew":
                await commands.handle_renew(client, user_id)
            else:
                await client.send_message(user_id, "دستور نامشخص. /help را بفرستید.")

    except Exception as e:
        logger.error(f"Error routing message from {user_id}: {e}")
        await client.send_message(user_id, "خطایی رخ داد. لطفا دوباره سعی کنید.")
