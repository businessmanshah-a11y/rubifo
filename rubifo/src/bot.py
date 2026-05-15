"""
Main Rubika Auto-Forward Bot
Handles message routing, scheduling, and subscription management
"""

import asyncio
import logging
from rubpy import Client

logger = logging.getLogger(__name__)


class RubifoBot:
    def __init__(self):
        self.client = Client()

    async def start(self):
        """Start the bot"""
        logger.info("Starting Rubifo bot...")
        await self.client.run()

    async def stop(self):
        """Stop the bot"""
        logger.info("Stopping Rubifo bot...")
        await self.client.stop()


async def main():
    bot = RubifoBot()
    await bot.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
