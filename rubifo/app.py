"""
Parspack entry point — runs the bot alongside a minimal health server.
Parspack Python buildpack requires a process bound to 0.0.0.0 on port > 1000.
"""
import asyncio
import os
from aiohttp import web


async def health(request):
    return web.Response(text="ok")


async def run_health_server():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "8000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


async def main():
    from src.config import BOT_TOKEN
    from src.bot.main import RufifoBot

    bot = RufifoBot(BOT_TOKEN)
    await asyncio.gather(
        run_health_server(),
        bot.start(),
    )


if __name__ == "__main__":
    asyncio.run(main())
