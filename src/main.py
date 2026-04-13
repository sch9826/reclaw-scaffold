"""
src/main.py — Service entry point for ReClaw Scaffold.

Loads environment, initializes the Discord client, registers the message
handler, starts the heartbeat scheduler, and runs the async event loop.
"""

import asyncio
import os
import logging

import discord
import schedule
from dotenv import load_dotenv

from agent import process_message
from heartbeat import run_heartbeat
from persona_router import get_persona

# ── Setup ─────────────────────────────────────────────────────────────────────

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("main")

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
DRY_RUN = "--dry-run" in __import__("sys").argv

# ── Discord client ─────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    log.info("Bot connected as %s (id=%s)", client.user, client.user.id)


@client.event
async def on_message(message: discord.Message):
    """Route incoming Discord messages to the agent."""
    if message.author == client.user:
        return  # ignore own messages

    channel_id = str(message.channel.id)
    persona = get_persona(channel_id)
    log.info("Message in channel=%s routed to persona=%s", channel_id, persona)

    async with message.channel.typing():
        response = await asyncio.to_thread(
            process_message, message.content, persona
        )

    if response:
        await message.channel.send(response)


# ── Heartbeat scheduler (runs in background thread) ───────────────────────────

def _start_heartbeat_scheduler():
    """Schedule the heartbeat to fire every 30 minutes (blocking)."""
    schedule.every(30).minutes.do(run_heartbeat)
    log.info("Heartbeat scheduler started — fires every 30 minutes")
    import time
    while True:
        schedule.run_pending()
        time.sleep(60)


# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    if DRY_RUN:
        log.info("--dry-run mode: skipping Discord connection and heartbeat.")
        log.info("Imports and env load succeeded. Exiting cleanly.")
        return

    # Start heartbeat scheduler in a background thread
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _start_heartbeat_scheduler)

    # Run the heartbeat once at startup
    run_heartbeat()

    await client.start(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
