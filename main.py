"""
Entry point. Run with:

    python main.py

Loads .env, sets up logging, discovers every bot in bots/, and runs them
all concurrently under one asyncio event loop until Ctrl+C.
"""

from __future__ import annotations

import asyncio
import logging

from dotenv import load_dotenv

from core.runner import run_all


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    # python-telegram-bot's internal HTTP logging is noisy at INFO.
    logging.getLogger("httpx").setLevel(logging.WARNING)


def main() -> None:
    load_dotenv()
    _setup_logging()
    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
