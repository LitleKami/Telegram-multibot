"""
Discovers bot plugins in the bots/ directory.

Convention: any *.py file directly under bots/ (not starting with "_") is
treated as a candidate bot module. It is loaded and must expose a
module-level `bot: BotPlugin` attribute. Files that don't follow the
convention, fail to import, or are missing a valid token are logged and
skipped — one broken bot file never takes down the others.
"""

from __future__ import annotations

import importlib
import logging
import os
import pkgutil
from dataclasses import dataclass
from typing import List

from core.contract import BotPlugin

logger = logging.getLogger(__name__)

BOTS_PACKAGE = "bots"


@dataclass
class LoadResult:
    plugin: BotPlugin
    token: str


def discover_bots() -> List[LoadResult]:
    """Import every bot file in bots/, validate it, and pair it with its token.

    Returns only bots that imported cleanly AND have their token env var set.
    Everything else is logged as a warning/error and left out, so a typo in
    one new bot file never prevents the others from starting.
    """
    results: List[LoadResult] = []
    package = importlib.import_module(BOTS_PACKAGE)

    for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
        if is_pkg or module_name.startswith("_"):
            continue

        full_name = f"{BOTS_PACKAGE}.{module_name}"
        try:
            module = importlib.import_module(full_name)
        except Exception:
            logger.exception("Skipping '%s': failed to import", full_name)
            continue

        plugin = getattr(module, "bot", None)
        if plugin is None:
            logger.warning(
                "Skipping '%s': no module-level `bot = BotPlugin(...)` found",
                full_name,
            )
            continue
        if not isinstance(plugin, BotPlugin):
            logger.warning(
                "Skipping '%s': `bot` attribute is not a BotPlugin instance",
                full_name,
            )
            continue

        plugin.source_file = full_name

        token = os.environ.get(plugin.token_env)
        if not token:
            logger.warning(
                "Skipping '%s' (bot='%s'): env var %s is not set",
                full_name, plugin.name, plugin.token_env,
            )
            continue

        results.append(LoadResult(plugin=plugin, token=token))
        logger.info("Discovered bot '%s' from %s", plugin.name, full_name)

    return results
