"""
Builds a python-telegram-bot Application for each discovered bot and runs
all of them concurrently, long-polling, in one asyncio event loop.

Running N Applications in one process/event loop is much lighter on a phone
(Termux) than N separate Python processes, while keeping each bot fully
isolated in its own file with its own token and handlers.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import signal
from typing import List

from telegram.ext import Application, ApplicationBuilder

from core.loader import LoadResult, discover_bots

logger = logging.getLogger(__name__)


async def _maybe_await(value):
    if inspect.isawaitable(value):
        await value


def _build_application(load_result: LoadResult) -> Application:
    plugin = load_result.plugin
    builder = ApplicationBuilder().token(load_result.token)
    if plugin.configure_builder is not None:
        builder = plugin.configure_builder(builder)
    return builder.build()


async def _run_once(load_result: LoadResult) -> None:
    """Run a single bot's Application until cancelled or it errors out."""
    plugin = load_result.plugin
    app = _build_application(load_result)

    await _maybe_await(plugin.setup(app))

    async with app:
        await app.start()
        await app.updater.start_polling()
        logger.info("Bot '%s' is polling", plugin.name)
        try:
            # Idle until this task is cancelled by the host shutdown.
            await asyncio.Event().wait()
        finally:
            logger.info("Stopping bot '%s'", plugin.name)
            await app.updater.stop()
            await app.stop()
            if plugin.on_shutdown is not None:
                await _maybe_await(plugin.on_shutdown(app))


async def _run_one(load_result: LoadResult) -> None:
    """Supervise one bot: restart it with backoff if it crashes.

    A crash in one bot's polling loop (network blip, transient Telegram API
    error, bug in that bot's own handler) never takes down the host or the
    other bots — it just gets retried with exponential backoff, capped, so a
    persistently broken bot doesn't spin hot forever.
    """
    plugin = load_result.plugin
    backoff = 1
    max_backoff = 60

    while True:
        try:
            await _run_once(load_result)
            return  # clean cancellation (shutdown) — stop supervising
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "Bot '%s' crashed; restarting in %ss", plugin.name, backoff
            )
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)


async def run_all() -> None:
    loaded = discover_bots()
    if not loaded:
        logger.error(
            "No bots were loaded. Check that bots/*.py files exist, import "
            "cleanly, and that their token env vars are set. Nothing to run."
        )
        return

    tasks = [asyncio.create_task(_run_one(lr), name=lr.plugin.name) for lr in loaded]

    stop_event = asyncio.Event()

    def _request_stop(*_args) -> None:
        logger.info("Shutdown requested")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_stop)
        except NotImplementedError:
            # add_signal_handler isn't available on all platforms (e.g. some
            # Android/Termux builds) — fall back to default Ctrl+C behavior.
            pass

    await stop_event.wait()

    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    for task in tasks:
        if task.cancelled():
            continue
        exc = task.exception()
        if exc is not None:
            logger.error("Bot '%s' crashed: %r", task.get_name(), exc)
