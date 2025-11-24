import os
import logging
import json
import datetime
import random
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)

load_dotenv()
TG_TOKEN = os.getenv("TG_BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Об олимпиаде", callback_data="about")],
        [InlineKeyboardButton("🔥 Ближайшие даты", callback_data="close_dates"),
        InlineKeyboardButton("✅ Выбрать профиль", callback_data="back_to_groups"),
    ]])
    messages = context.application.bot_data.get("messages")
    welcome_text = messages["welcome"]
    await msg.reply_text(welcome_text, parse_mode="Markdown", reply_markup=keyboard)

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Выбрать профиль", callback_data="back_to_groups")],
        [InlineKeyboardButton("🏠 Домой", callback_data="back_to_home")]
        
    ])
    #await update.callback_query.message.delete()
    messages = context.application.bot_data.get("messages")
    about_text = messages["about"]
    await update.callback_query.edit_message_text(about_text, parse_mode="Markdown", reply_markup=keyboard)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answers = [
        "К сожалению, я не понимаю этот текст🥲 Пожалуйста, используйте кнопки меню",
        "Извините, я не могу обработать это сообщение😔 Пожалуйста, используйте кнопки меню",
        "Похоже, я не знаю, что ответить на это😖 Пожалуйста, используйте кнопки меню"
    ]

    await update.message.reply_text(random.choice(answers))

async def reload_conf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in os.getenv("ADMINS"):
        return
    await update.message.reply_text("Перезагрузка конфигурации...")
    profiles = load_data("profiles.json")
    messages = load_data("messages.json")
    context.application.bot_data["profiles_data"] = profiles
    context.application.bot_data["messages"] = messages
    await update.message.reply_text("Конфигурация перезагружена.")


def load_data(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = context.application.bot_data.get("profiles_data")
    cd = query.data

    # назад к списку групп
    if cd == "back_to_groups":
        kb = build_groups_keyboard(data)
        await query.edit_message_text("Для удобства мы разделили олимпиады по тематическим группам.\n\nВыбирай интересующую:", reply_markup=kb)
        return

    # назад к главному меню
    if cd == "back_to_home":
        await start(update, context)
        return

    # ближайшие даты олимпиад
    if cd == "close_dates":
        top5_profiles = get_top5_profiles(data)
        kb = build_top5_profiles_keyboard(top5_profiles)

        profiles_text = ""
        for i, profile in enumerate(top5_profiles):
            name = profile['name']
            date = profile['date_olimp']
            profiles_text += f"{i+1}. *{name}* — {date}\n"
        text = f"Здесь собраны топ-5 ближайших олимпиад по разным направлениям.\n\n{profiles_text}\n\nВыбери интересующую: "

        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)
        return

    # выбор группы (group1..groupN)
    if cd.startswith("group"):
        group = find_group_by_id(data, cd)
        if not group:
            await query.edit_message_text("Не найдена группа.")
            return
        kb = build_profiles_keyboard(group)
        text = f"Группа *{group['name']}*.\n\n{group.get('description','')}\n\nТеперь выбери профиль:"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)
        return

    # выбор профиля (p_*)
    if cd.startswith("p_"):
        profile, group = find_profile_by_id(data, cd)
        if not profile:
            await query.edit_message_text("Профиль не найден.")
            return
        
        text = build_description(profile)

        buttons = []
        if profile.get("url"):
            buttons.append([InlineKeyboardButton("✅ Регистрация", url=profile['url'])])
        buttons.append([InlineKeyboardButton("🏠 Домой", callback_data="back_to_home")])

        kb = InlineKeyboardMarkup(buttons)

        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)
        return

    await query.edit_message_text("Непонятное действие.")

def build_description(profile):
    """Возвращает форматированное описание профиля"""
    name = profile['name']
    cafedras = profile['cafedras']
    zav_caf = profile['zav_caf']
    description = profile['description']
    date_reg = profile['date_reg']
    date_olimp = profile['date_olimp']
    place = profile['place']

    text = f"*{name}*\n\n"

    if cafedras:
        if len(cafedras) == 1:
            cafedra_text = f"🎓 *Кафедра-организатор:*\n{cafedras[0]}\n"
        else:
            cafedra_text = "🎓 *Кафедры-организаторы:*\n"
            for c in cafedras:
                cafedra_text += f"- {c}\n"
        text += cafedra_text + "\n"
    
    if zav_caf:
        text += f"👨‍🎓 *Заведующий кафедрой:* {zav_caf}\n\n"

    if description == '':
        text += '🕐 Это новый профиль.\nПодробности про него появятся позднее'
    else:
        text += f"📝 *Описание профиля:*\n{description}\n\n"
        text += "✏️ Олимпиада проводится в *очном формате* в МГТУ \"СТАНКИН\"\n\n"

    if date_reg or date_olimp:
        text += f"🗓️ *ОСНОВНЫЕ ДАТЫ*\n"
        if date_reg: 
            text += f"*Регистрация:* {date_reg}\n"
        if date_olimp: 
            text += f"*Проведение олимпиады:* {date_olimp}\n"
        text += "\n"
    
    if place:
        text += f"📍 *Место проведения:* {place}"
    
    return text


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

def get_top5_profiles(data):
    """Возвращает топ-5 профилей по дате проведения"""
    all_profiles = []
    for group in data["groups"]:
        for p in group.get("profiles", []):
            if p.get("date_olimp", "") != "":
                all_profiles.append(p) # (p, group)
    
    # функция извлечения даты для сортировки
    def extract_date(profile):
        date_str = profile["date_olimp"]
        day, month, year = map(int, date_str.split("."))

        #проверка, если дата уже прошла, то не учитывать её
        date = datetime.date(year, month, day)
        if date < datetime.date.today():
            return (9999, 12, 31)
        return (year, month, day)
    
    all_profiles.sort(key=extract_date)
    top5_profiles = all_profiles[:5]
    return top5_profiles

def build_top5_profiles_keyboard(profiles):
    """Возвращает InlineKeyboardMarkup для топ-5 профилей по дате проведения"""
    buttons = []
    for profile in profiles:
        buttons.append([InlineKeyboardButton(profile['name'], callback_data=profile["id"])])

    # кнопка назад к главному меню
    buttons.append([InlineKeyboardButton("🏠 Домой", callback_data="back_to_home")])
    return InlineKeyboardMarkup(buttons)


def find_group_by_id(data, gid):
    for g in data["groups"]:
        if g["id"] == gid:
            return g
    return None


def find_profile_by_id(data, pid):
    for g in data["groups"]:
        for p in g.get("profiles", []):
            if p["id"] == pid:
                return p, g
    return None, None


if __name__ == "__main__": 
    profiles = load_data("profiles.json")
    messages = load_data("messages.json")

    app = Application.builder().token(TG_TOKEN).build()
    app.bot_data["profiles_data"] = profiles
    app.bot_data["messages"] = messages

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reload", reload_conf))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(about, pattern="^about$"))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()
