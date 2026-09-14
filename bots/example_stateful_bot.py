"""
Second example: shows an async setup() (for bots that need to open an HTTP
client, DB connection, etc at startup) plus on_shutdown for cleanup, and
per-bot state stashed on app.bot_data instead of module globals — safer when
multiple bots' modules are alive in the same process.
"""

import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler

from core.contract import BotPlugin
from core.shared import get_bot_logger

log = get_bot_logger("stateful-example")


async def ping_command(update: Update, context) -> None:
    client: httpx.AsyncClient = context.application.bot_data["http_client"]
    resp = await client.get("https://api.telegram.org")
    await update.message.reply_text(f"HTTP client alive, status={resp.status_code}")


async def setup(app: Application) -> None:
    # Runs once at startup, before polling begins. Anything opened here
    # (HTTP clients, DB pools) should be closed in on_shutdown below.
    app.bot_data["http_client"] = httpx.AsyncClient(timeout=10)
    app.add_handler(CommandHandler("ping", ping_command))
    log.info("stateful-example setup complete")


async def on_shutdown(app: Application) -> None:
    client: httpx.AsyncClient = app.bot_data.get("http_client")
    if client is not None:
        await client.aclose()
    log.info("stateful-example cleaned up")


bot = BotPlugin(
    name="stateful-example",
    token_env="STATEFUL_EXAMPLE_BOT_TOKEN",
    setup=setup,
    on_shutdown=on_shutdown,
)
