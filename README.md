# Telegram Multi-Bot Host

Runs any number of independent Telegram bots in one process. To add a new
bot: drop one file into `bots/`. Nothing else needs to change.

## Install

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env, add each bot's token under the env var name it declares
```

## Run

```bash
python main.py
```

Each `bots/*.py` file is discovered, imported, and run concurrently via
long-polling in one asyncio event loop. If a bot file fails to import, or
its token env var isn't set, it's skipped with a logged warning — the rest
still start. If a bot crashes while running, it's restarted with
exponential backoff (capped at 60s) without affecting the others.

## Adding a new bot

Copy `bots/example_echo_bot.py`, rename it, and edit three things:

```python
from core.contract import BotPlugin

def setup(app):
    app.add_handler(...)   # your handlers here

bot = BotPlugin(
    name="my_new_bot",              # unique id, used in logs
    token_env="MY_NEW_BOT_TOKEN",   # env var this bot reads its token from
    setup=setup,                     # sync or async
)
```

Then add `MY_NEW_BOT_TOKEN=...` to `.env`. That's it — the loader picks it
up automatically next run.

See `bots/example_stateful_bot.py` for the pattern when a bot needs async
setup (opening an HTTP client, DB connection, etc.) and cleanup on shutdown
(`on_shutdown`).

## Shared code

`core/shared.py` holds optional helpers any bot may import (e.g.
`get_bot_logger`). Nothing requires it — fully isolated bots can ignore
`core/` entirely beyond the `BotPlugin` contract in `core/contract.py`.

## Project layout

```
main.py                    # entrypoint: loads .env, starts everything
core/contract.py           # BotPlugin dataclass — the plugin contract
core/loader.py             # discovers bots/*.py, validates, pairs with token
core/runner.py             # builds + runs all Applications concurrently, with
                            # crash-isolation and auto-restart per bot
core/shared.py             # optional shared helpers
bots/example_echo_bot.py   # minimal template
bots/example_stateful_bot.py  # async setup + shutdown template
```
