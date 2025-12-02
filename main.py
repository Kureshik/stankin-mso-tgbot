import logging
import asyncio
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
import config
from data_loader import load_data
import handlers
import stats_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def _async_main():
    if not config.TG_TOKEN:
        logger.error("TG_BOT_TOKEN is not set in env")
        return

    profiles = load_data("profiles.json")
    messages = load_data("messages.json")

    # ensure stats file exists
    await stats_manager.init_stats()

    app = Application.builder().token(config.TG_TOKEN).build()
    app.bot_data["profiles_data"] = profiles
    app.bot_data["messages"] = messages

    # handlers
    app.add_handler(CommandHandler("start", handlers.start))
    #app.add_handler(CommandHandler("reload", handlers.reload_conf))
    #app.add_handler(CommandHandler("stats", handlers.get_statistics))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_text))
    app.add_handler(CallbackQueryHandler(handlers.about, pattern="^about$"))
    app.add_handler(CallbackQueryHandler(handlers.get_statistics, pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(handlers.reload_conf, pattern="^reload$"))
    app.add_handler(CallbackQueryHandler(handlers.callback_handler))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    logger.info("Bot started — waiting forever")
    await asyncio.Event().wait()    


def main():
    try:
        asyncio.run(_async_main())
    except KeyboardInterrupt:
        logger.info("Interrupted, exiting...")

if __name__ == "__main__":
    main()
