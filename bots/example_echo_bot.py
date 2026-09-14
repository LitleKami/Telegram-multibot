"""
Example bot: replies with whatever text it's sent, and has a /start command.

This is the minimal template for adding a new bot — copy this file, rename
it, change `name` and `token_env`, and write your own handlers in setup().
Nothing else in the project needs to change; the loader picks it up
automatically the next time main.py runs.
"""

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from core.contract import BotPlugin
from core.shared import get_bot_logger

log = get_bot_logger("echo")


async def start_command(update: Update, context) -> None:
    await update.message.reply_text("Echo bot online. Send me anything.")


async def echo_message(update: Update, context) -> None:
    log.info("Echoing message from chat %s", update.effective_chat.id)
    await update.message.reply_text(update.message.text)


def setup(app: Application) -> None:
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))


bot = BotPlugin(
    name="echo",
    token_env="ECHO_BOT_TOKEN",
    setup=setup,
)
