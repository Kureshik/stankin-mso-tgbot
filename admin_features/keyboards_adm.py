from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def admin_keyboard():
    """Возвращает InlineKeyboardMarkup для админ-панели"""
    buttons = [
        [InlineKeyboardButton("📊 Статистика", callback_data="stats"),
         InlineKeyboardButton("🔄️ Обновить конфиг", callback_data="reload")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="broadcast")],
        [InlineKeyboardButton("🏠 Домой", callback_data="back_to_home")]
    ]
    return InlineKeyboardMarkup(buttons)


