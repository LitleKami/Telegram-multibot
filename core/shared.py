"""
Optional shared helpers for bot files.

Nothing in bots/ is required to import from here — this exists purely so
bots that DO want common logic (e.g. a shared Gemini client, a shared HTTP
session, common logging setup) don't have to duplicate it. Fully isolated
bots can ignore this file entirely.
"""

from __future__ import annotations

import logging


def get_bot_logger(name: str) -> logging.Logger:
    """Convenience: a logger namespaced per bot, so log lines are traceable
    back to which bot emitted them even with several running at once."""
    return logging.getLogger(f"bots.{name}")
