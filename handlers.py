import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from logger import logger

import config
from keyboards import *
from utils import *
import stats_manager

from admin_features.handlers_adm import *

async def collect_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_tag = update.effective_user.username or "no_username"
    await stats_manager.collect_user_ids(user_id, user_tag)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    
    start_parameter = None
    if update.message and len(msg.text.split()) > 1:
        start_parameter = msg.text.split(maxsplit=1)[1]
    
    if update.message:
        user_id = update.effective_user.id
        user_tag = update.effective_user.username or "no_username"
        logger.info(f"User @{user_tag} ({user_id}) started bot with parameter: {start_parameter}")
        
        await stats_manager.increment_start(user_id, user_tag, start_parameter)

    kb = [
        [InlineKeyboardButton("🔍 Об олимпиаде", callback_data="about"),
         InlineKeyboardButton("📊 Результаты", callback_data="results")],
        [InlineKeyboardButton("🔥 Ближайшие даты", callback_data="close_dates"),
        InlineKeyboardButton("✅ Выбрать профиль", callback_data="back_to_groups")]
    ]

    messages = context.application.bot_data.get("messages")
    welcome_text = messages["welcome"]

    if config.is_admin(update.effective_user.id):
        welcome_text = "⚠️ Режим администратора активирован ⚠️" + "\n\n" + welcome_text
        kb.append([InlineKeyboardButton("⚙️ Панель администратора", callback_data="admin_panel")])
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
    logger.info(f"User @{update.effective_user.username} ({update.effective_user.id}) requested 'about' info.")
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
    
    logger.info(f"Received text message from @{update.effective_user.username} ({update.effective_user.id})")

    await stats_manager.increment_counter("text_messages")
    answers = [
        "К сожалению, я не понимаю этот текст🥲 Пожалуйста, используйте кнопки меню",
        "Извините, я не могу обработать это сообщение😔 Пожалуйста, используйте кнопки меню",
        "Похоже, я не знаю, что ответить на это😖 Пожалуйста, используйте кнопки меню"
    ]

    await update.message.reply_text(random.choice(answers))

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

    # админ-панель
    if cd == "admin_panel":
        logger.warning(f"Admin panel accessed by @{update.effective_user.username} ({update.effective_user.id})")
        kb = admin_keyboard()
        text = '⚠️ Режим администратора активирован ⚠️'
        text += "\n\nЗдесь вы можете управлять ботом, просматривать статистику использования и выполнять рассылку пользователям."
        await query.edit_message_text(text, reply_markup=kb)
        return
    
    # результаты олимпиад
    if cd == "results":
        logger.info(f"User @{update.effective_user.username} ({update.effective_user.id}) requested 'results' info.")
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
        logger.info(f"User @{update.effective_user.username} ({update.effective_user.id}) requested 'close_dates' info.")
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
        
        logger.info(f"User @{update.effective_user.username} ({update.effective_user.id}) selected group {group['name']}.")

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

        logger.info(f"User @{update.effective_user.username} ({update.effective_user.id}) selected profile {profile['name']}.")
        # increment profile view
        user_id = update.effective_user.id

        await stats_manager.increment_profile_view(
            profile['id'],
            profile['name'],
            user_id
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