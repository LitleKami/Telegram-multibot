"""
The plugin contract.

Every file in bots/ is a self-contained Telegram bot. To be picked up by the
host, a bot file must define a module-level object named `bot` that is an
instance of BotPlugin (below). Nothing else about the file is constrained —
imports, helper functions, classes, whatever the bot needs.

Minimal example (see bots/example_echo_bot.py for a full one):

    from core.contract import BotPlugin

    async def setup(app):
        app.add_handler(...)

    bot = BotPlugin(
        name="echo",
        token_env="ECHO_BOT_TOKEN",
        setup=setup,
    )

The host never imports Telegram-specific code itself beyond what's needed to
build the Application — each bot file owns its own handlers, its own token
env var name, and (optionally) its own polling settings.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Optional

from telegram.ext import Application, ApplicationBuilder

logger = logging.getLogger(__name__)

# A setup function receives the built Application and attaches handlers to it.
# It may be sync or async; the host awaits it if it's a coroutine function.
SetupFn = Callable[[Application], Optional[Awaitable[None]]]


@dataclass
class BotPlugin:
    """Declarative description of one bot, provided by each file in bots/."""

    # Short unique identifier, used in logs. Doesn't need to match the filename.
    name: str

    # Name of the environment variable holding this bot's Telegram token.
    # Each bot file picks its own env var name (per your convention), e.g.
    # "TRANSLATOR_BOT_TOKEN", "VIDBOT_TOKEN", etc.
    token_env: str

    # Called once, after the Application is built with this bot's token.
    # Responsible for registering all handlers (commands, messages, etc).
    setup: SetupFn

    # Optional: extra ApplicationBuilder configuration hook, e.g. to set
    # concurrent_updates, connection pool size, etc. Rarely needed.
    configure_builder: Optional[Callable[[ApplicationBuilder], ApplicationBuilder]] = None

    # Optional: called on shutdown (host stop, or Ctrl+C) for cleanup
    # (closing DB connections, HTTP sessions the bot opened, etc).
    on_shutdown: Optional[Callable[[Application], Optional[Awaitable[None]]]] = None

    # Internal, filled in by the loader — not set by bot authors.
    source_file: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("BotPlugin.name must be a non-empty string")
        if not self.token_env or not self.token_env.strip():
            raise ValueError(
                f"BotPlugin '{self.name}' must set token_env to the name of "
                f"the environment variable holding its token"
            )
