import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from data_loader import load_data
import config
from keyboards import build_groups_keyboard, build_profiles_keyboard, build_top5_profiles_keyboard, build_results_keyboard
from utils import build_description, find_group_by_id, find_profile_by_id, get_top5_profiles

import stats_manager


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message

    start_parameter = None
    if update.message and len(msg.text.split()) > 1:
        start_parameter = msg.text.split(maxsplit=1)[1]

    user_tag = f"@{update.effective_user.username}" or "no_username"
    await stats_manager.increment_start(user_tag, start_parameter)

    kb = [
        [InlineKeyboardButton("🔍 Об олимпиаде", callback_data="about"),
         InlineKeyboardButton("📊 Результаты", callback_data="results")],
        [InlineKeyboardButton("🔥 Ближайшие даты", callback_data="close_dates"),
        InlineKeyboardButton("✅ Выбрать профиль", callback_data="back_to_groups")]
    ]

    messages = context.application.bot_data.get("messages")
    welcome_text = messages["welcome"]

    if config.is_admin(update.effective_user.id):
        welcome_text = '⚠️ Режим администратора активирован ⚠️' + "\n\n" + welcome_text
        kb.append([InlineKeyboardButton("[adm] Статистика", callback_data="stats"),
                  InlineKeyboardButton("[adm] Обновить конфиг", callback_data="reload")]
        )
    keyboard = InlineKeyboardMarkup(kb)

    if update.message:
        await msg.reply_text(welcome_text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await msg.edit_text(welcome_text, parse_mode="Markdown", reply_markup=keyboard)

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Выбрать профиль", callback_data="back_to_groups")],
        [InlineKeyboardButton("🌐 Подробнее", url="https://priem.stankin.ru/stud_olymp/")],
        [InlineKeyboardButton("🏠 Домой", callback_data="back_to_home")]
        
    ])
    #await update.callback_query.message.delete()
    messages = context.application.bot_data.get("messages")
    about_text = messages.get("about", "Информация отсутствует.")
    await update.callback_query.edit_message_text(about_text, parse_mode="Markdown", reply_markup=keyboard)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if config.LOG_CHAT:
        await context.bot.forward_message(
            chat_id=config.LOG_CHAT,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )
    await stats_manager.increment_counter("text_messages")
    answers = [
        "К сожалению, я не понимаю этот текст🥲 Пожалуйста, используйте кнопки меню",
        "Извините, я не могу обработать это сообщение😔 Пожалуйста, используйте кнопки меню",
        "Похоже, я не знаю, что ответить на это😖 Пожалуйста, используйте кнопки меню"
    ]

    await update.message.reply_text(random.choice(answers))

async def reload_conf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    msg = update.callback_query.message

    if not config.is_admin(update.effective_user.id):
        return
    await msg.reply_text("Перезагрузка конфигурации...")
    profiles = load_data("profiles.json")
    messages = load_data("messages.json")
    results = load_data("results.json")
    context.application.bot_data["profiles_data"] = profiles
    context.application.bot_data["messages"] = messages
    context.application.bot_data["results"] = results
    await stats_manager.increment_counter("reloads")
    await msg.reply_text("Конфигурация перезагружена.")

async def get_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    msg = update.callback_query.message

    if not config.is_admin(update.effective_user.id):
        return
    await msg.reply_text("Текущая статистика использования бота")

    stats = await stats_manager.get_stats()
    counters = stats.get("counters", {})
    profiles = stats.get("profiles", {})
    lines = []
    lines.append("*Counters:*")
    for k, v in counters.items():
        if k == "start_origin":
            lines.append(f"- {k.replace('_', ' ')}:")
            for origin, cnt in v.items():
                lines.append(f"    - {origin}: {cnt}")
        else:
            lines.append(f"- {k.replace('_', ' ')}: {v}")
    if profiles:
        lines.append("\n*Profiles views (top 10):*")
        top = sorted(profiles.items(), key=lambda x: x[1], reverse=True)[:10]
        for pid, cnt in top:
            lines.append(f"- {pid}: {cnt}")
    else:
        lines.append("\nProfiles views: none")

    await msg.reply_text("\n".join(lines), parse_mode="Markdown")
    await msg.reply_document(document=open("stats.json", "rb"))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = context.application.bot_data.get("profiles_data")
    cd = query.data

    await stats_manager.increment_counter("callbacks")

    # назад к списку групп
    if cd == "back_to_groups":
        kb = build_groups_keyboard(data)
        await query.edit_message_text("Для удобства мы разделили олимпиады по тематическим группам.\n\nВыбирай интересующую:", reply_markup=kb)
        return

    # назад к главному меню
    if cd == "back_to_home":
        await start(update, context)
        return
    
    # результаты олимпиад
    if cd == "results":
        messages = context.application.bot_data.get("messages")
        results_text = messages["results"]
        data = context.application.bot_data.get("results", {})
        kb = []
        if data:
            kb = build_results_keyboard(data)
        kb.append([InlineKeyboardButton("🌐 Подробнее", url="https://priem.stankin.ru/stud_olymp/"),
                   InlineKeyboardButton("🏠 Домой", callback_data="back_to_home")
        ])
        if data:
            await query.edit_message_text(results_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        else:
            await query.edit_message_text("Результатов пока нет, но появятся в ближайшее время.\n\nМы тоже ждем 😔", reply_markup=InlineKeyboardMarkup(kb))
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
        
        # increment profile view
        user = update.effective_user
        user_tag = f"@{user.username}" if user.username else "no_username"

        await stats_manager.increment_profile_view(
            profile['name'],
            user_tag=user_tag
        )


        text = build_description(profile)

        buttons = []
        if profile.get("url"):
            buttons.append([InlineKeyboardButton("✅ Регистрация", url=profile['url'])])
        buttons.append([InlineKeyboardButton("🏠 Домой", callback_data="back_to_home")])

        kb = InlineKeyboardMarkup(buttons)

        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)
        return

    await query.edit_message_text("Непонятное действие.")