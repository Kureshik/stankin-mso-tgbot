from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def build_groups_keyboard(data):
    """Возвращает InlineKeyboardMarkup для выбора группы"""
    buttons = []
    for group in data["groups"]:
        buttons.append([InlineKeyboardButton(group["name"], callback_data=group["id"])])
    # кнопка назад к главному меню
    buttons.append([InlineKeyboardButton("🏠 Домой", callback_data="back_to_home")])
    return InlineKeyboardMarkup(buttons)

def build_profiles_keyboard(group):
    """Возвращает InlineKeyboardMarkup для профилей выбранной группы"""
    buttons = []
    for p in group.get("profiles", []):
        buttons.append([InlineKeyboardButton(p["name"], callback_data=p["id"])])
    # кнопка назад к выбору группы
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_groups")])
    return InlineKeyboardMarkup(buttons)

def build_top5_profiles_keyboard(profiles):
    """Возвращает InlineKeyboardMarkup для топ-5 профилей по дате проведения"""
    buttons = []
    for profile in profiles:
        buttons.append([InlineKeyboardButton(profile['name'], callback_data=profile["id"])])

    # кнопка назад к главному меню
    buttons.append([InlineKeyboardButton("🏠 Домой", callback_data="back_to_home")])
    return InlineKeyboardMarkup(buttons)

def build_results_keyboard(data):
    """Возвращает InlineKeyboardMarkup для результатов олимпиад"""
    buttons = []
    for result in data:
        buttons.append([InlineKeyboardButton(result["name"], url=result["url"])])
    return buttons
