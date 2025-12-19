from logger import tg_logger
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    TypeHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
import config
from data_loader import load_data
import handlers, admin_features.handlers_adm
import stats_manager

async def _async_main():
    if not config.TG_TOKEN:
        tg_logger.error("TG_BOT_TOKEN is not set in env")
        return

    profiles = load_data("data/profiles.json")
    messages = load_data("data/messages.json")
    results  = load_data("data/results.json")

    # ensure stats file exists
    await stats_manager.init_stats()

    app = Application.builder().token(config.TG_TOKEN).build()
    app.bot_data["profiles_data"] = profiles
    app.bot_data["messages"] = messages
    app.bot_data["results"] = results

    # handlers
    app.add_handler(TypeHandler(Update, handlers.collect_ids), group=2)
    app.add_handler(CommandHandler("start", handlers.start))
    #app.add_handler(CommandHandler("reload", handlers.reload_conf))
    #app.add_handler(CommandHandler("stats", handlers.get_statistics))
    app.add_handler(CallbackQueryHandler(handlers.about, pattern="^about$"))
    app.add_handler(CallbackQueryHandler(handlers.get_statistics, pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(handlers.reload_conf, pattern="^reload$"))
    app.add_handler(admin_features.handlers_adm.broadcast_handler)
    app.add_handler(CallbackQueryHandler(handlers.callback_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handlers.handle_text))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    tg_logger.info("Bot started — waiting forever")
    await asyncio.Event().wait()    


def main():
    try:
        asyncio.run(_async_main())
    except KeyboardInterrupt:
        tg_logger.info("Interrupted, exiting...")

if __name__ == "__main__":
    main()
