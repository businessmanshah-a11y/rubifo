"""
Parspack entry point — runs the bot alongside a web server.
Parspack Python buildpack requires a process bound to 0.0.0.0 on port > 1000.

Routes:
  GET  /          → landing page (index.html)
  GET  /static/*  → static assets (CSS, fonts, JS)
  GET  /health    → "ok" (Parsback health check)
  POST /webhook   → Rubika webhook updates
"""
import asyncio
import os
from pathlib import Path
from aiohttp import web

_bot_ref = None  # set after bot starts

_STATIC_DIR = Path(__file__).parent / "src" / "admin" / "static"


async def landing_page(request):
    """Serve the public landing page."""
    return web.FileResponse(_STATIC_DIR / "index.html")


async def health(request):
    return web.Response(text="ok")


async def webhook(request):
    """Receive a single update from Rubika (webhook mode)."""
    try:
        data = await request.json()
    except Exception:
        return web.Response(status=400, text="bad json")

    # Rubika sends {"update": {...}} for receiveUpdate
    raw_update = data.get("update") or data
    update_type = raw_update.get("type", "")
    chat_id = raw_update.get("chat_id")

    if not chat_id:
        return web.Response(text="ok")

    # Normalise into the same shape route_message expects
    if update_type == "NewMessage":
        msg = raw_update.get("new_message") or {}
        text = (msg.get("text") or "").strip()
        if not text:
            aux = msg.get("aux_data") or {}
            btn_id = aux.get("button_id", "")
            if btn_id:
                text = f"/{btn_id}"
        entry = {"user_id": str(chat_id), "text": text, "new_message": msg}
        forwarded = msg.get("forwarded_from") or {}
        if forwarded:
            entry["forwarded_from_chat"] = str(
                forwarded.get("chat_id") or forwarded.get("object_guid", "")
            )
            entry["forwarded_message_id"] = str(msg.get("message_id", ""))
    elif update_type == "StartedBot":
        entry = {"user_id": str(chat_id), "text": "/start", "new_message": {}}
    else:
        return web.Response(text="ok")

    if _bot_ref and _bot_ref.client:
        from src.bot.handlers import route_message
        asyncio.create_task(route_message(_bot_ref.client, str(chat_id), entry))

    return web.Response(text="ok")


async def run_health_server():
    app = web.Application()
    app.router.add_get("/", landing_page)
    app.router.add_get("/health", health)
    app.router.add_post("/webhook", webhook)
    # Serve static assets so the landing page CSS/fonts load correctly
    app.router.add_static("/static", _STATIC_DIR, show_index=False)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "8000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


async def main():
    global _bot_ref
    from src.config import BOT_TOKEN
    from src.bot.main import RufifoBot

    bot = RufifoBot(BOT_TOKEN)
    _bot_ref = bot
    await asyncio.gather(
        run_health_server(),
        bot.start(),
    )


if __name__ == "__main__":
    asyncio.run(main())
