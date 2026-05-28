"""
Register (or clear) the Rubika bot webhook endpoint.

Usage:
    python3 register_webhook.py set https://yourdomain.com/webhook
    python3 register_webhook.py clear
"""
import asyncio
import sys
import os
import aiohttp


BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BASE = f"https://botapi.rubika.ir/v3/{BOT_TOKEN}"


async def set_webhook(url: str):
    async with aiohttp.ClientSession() as session:
        resp = await session.post(
            f"{BASE}/updateBotEndpoints",
            json={"url": url, "type": "ReceiveUpdate"},
        )
        data = await resp.json(content_type=None)
        print("Set webhook:", data)


async def clear_webhook():
    async with aiohttp.ClientSession() as session:
        resp = await session.post(
            f"{BASE}/updateBotEndpoints",
            json={"url": "", "type": "ReceiveUpdate"},
        )
        data = await resp.json(content_type=None)
        print("Cleared webhook:", data)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "set" and len(sys.argv) == 3:
        asyncio.run(set_webhook(sys.argv[2]))
    elif cmd == "clear":
        asyncio.run(clear_webhook())
    else:
        print(__doc__)
