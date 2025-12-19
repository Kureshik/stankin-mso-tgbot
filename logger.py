import logging

# ==========================================================================
# =======                  [ Custom logging setup ]                  =======
# ==========================================================================

logger = logging.getLogger("custom")
logger.setLevel(logging.DEBUG)
logger.propagate = False

# -------------------- Definition of debug handler -------------------------
debug_handler = logging.FileHandler("logs/debug.log", encoding="utf-8")
debug_handler.setLevel(logging.DEBUG)

class OnlyDebug(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.DEBUG

debug_handler.addFilter(OnlyDebug())

debug_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s",
    "%d.%m.%Y %H:%M:%S"
)
debug_handler.setFormatter(debug_formatter)
# ------------------------- End of definition ------------------------------

# --------------------- Definition of info handler -------------------------
info_handler = logging.FileHandler("logs/info.log", encoding="utf-8")
info_handler.setLevel(logging.INFO)

info_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s",
    "%d.%m.%Y %H:%M:%S"
)
info_handler.setFormatter(info_formatter)

# ------------------------- End of definition ------------------------------

logger.addHandler(debug_handler)
logger.addHandler(info_handler)


# ==========================================================================
# =======                 [ Telegram logging setup ]                 =======
# ==========================================================================

# telegram logger
tg_logger = logging.getLogger("telegram")
tg_logger.setLevel(logging.INFO)
tg_logger.propagate = False

# telegram.ext logger
tg_ext_logger = logging.getLogger("telegram.ext")
tg_ext_logger.setLevel(logging.INFO)
tg_ext_logger.propagate = False

# ------------------------ Definition of tg handler ------------------------
tg_handler = logging.FileHandler("logs/telegram.log", encoding="utf-8")
tg_handler.setLevel(logging.INFO)

tg_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    "%d.%m.%Y %H:%M:%S"
)
tg_handler.setFormatter(tg_formatter)
# ------------------------- End of definition ------------------------------

tg_logger.addHandler(tg_handler)
tg_ext_logger.addHandler(tg_handler)

logger.info(   "<==                [ Logger initialized ]                ==>")
logger.debug(  "<==                [ Logger initialized ]                ==>")
tg_logger.info("<==                [ Logger initialized ]                ==>")