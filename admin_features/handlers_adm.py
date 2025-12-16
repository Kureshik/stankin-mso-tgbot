from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ( 
    ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters   
)

from telegram.error import Forbidden, BadRequest

import asyncio

from admin_features.keyboards_adm import *
from data_loader import load_data
import config
from keyboards import *
from utils import *

import stats_manager

# Состояния для ConversationHandler
WAITING_FOR_CONTENT, PREVIEW_ACTION, CONFIRM_BROADCAST = range(3)

async def reload_conf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    msg = update.callback_query.message

    if not config.is_admin(update.effective_user.id):
        return
    await msg.reply_text("Перезагрузка конфигурации...")
    profiles = load_data("data/profiles.json")
    messages = load_data("data/messages.json")
    results  = load_data("data/results.json")
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
    users    = stats.get("users", {})

    lines = []
    lines.append("*Cчетчики:*")
    for k, v in counters.items():
        match k:
            case "start":
                lines.append(f"- Старт нажали: {v} раз(а), всего пользователей: {len(users)}")
                continue
            case "callbacks":
                lines.append(f"- Колбеков обработано: {v}")
                continue
            case "text_messages":
                lines.append(f"- Текстовые сообщения: {v}")
                continue
            case "reloads":
                lines.append(f"- Перезагрузок конфигурации: {v}")
                continue
            case "start_origin":
                lines.append(f"- Откуда:")
                for origin, cnt in v.items():
                    lines.append(f"    - {origin.replace('_', ' ')}: {cnt}")
                continue
            case _:
                lines.append(f"- {k.replace('_', ' ')}: {v}")
                continue
    if profiles:
        lines.append("\n*Топ 5 профилей по просмотрам:*")
        top_profiles = sorted(
            [(data.get("title", id), data.get("views", 0)) for id, data in profiles.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        for title, views in top_profiles:
            lines.append(f"- {title}: {views}")

    await msg.reply_text("\n".join(lines), parse_mode="Markdown")
    await msg.reply_document(document=open("data/stats.json", "rb"))

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 1: Просьба отправить контент"""
    await update.callback_query.answer()
    user_id = update.effective_user.id
    
    if not config.is_admin(update.effective_user.id):
        return ConversationHandler.END
    
    await update.callback_query.message.reply_text(
        "📢 *Создание рассылки*\n\n"
        "Отправьте сообщение (текст, фото, видео), которое хотите разослать.\n"
        "Форматирование и медиа сохранятся.",
        parse_mode="Markdown"
    )
    return WAITING_FOR_CONTENT

async def receive_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 2: Получение контента и показ предпросмотра"""
    # Сохраняем ID сообщения и ID чата, откуда оно пришло, чтобы потом копировать
    context.user_data['broadcast_msg_id'] = update.message.message_id
    context.user_data['broadcast_chat_id'] = update.message.chat_id

    await update.message.reply_text("👁 Предпросмотр того, что увидят пользователи:")
    
    # Показываем само сообщение (copy_message идеально копирует контент)
    await show_preview(update, context)
    
    return PREVIEW_ACTION

async def show_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вспомогательная функция для отображения меню действий"""
    msg_id = context.user_data['broadcast_msg_id']
    from_chat = context.user_data['broadcast_chat_id']

    # Копируем сообщение админу
    try:
        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=from_chat,
            message_id=msg_id
        )
    except BadRequest as e:
        await update.effective_message.reply_text(f"Ошибка копирования: {e}")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("🚀 Перейти к рассылке", callback_data="go_to_send")],
        [InlineKeyboardButton("✏️ Изменить текст", callback_data="change_content")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    
    await update.effective_chat.send_message(
        "Что делаем с этим сообщением?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def preview_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 3: Обработка кнопок предпросмотра"""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "go_to_send":
        # Получаем кол-во пользователей из БД
        users_count = 1500 # Замените на len(db.get_users())
        
        await query.edit_message_text(
            f"⚠️ *ВЫ УВЕРЕНЫ?*\n\n"
            f"Сообщение будет отправлено *{users_count}* пользователям.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ ДА, РАЗОСЛАТЬ", callback_data="confirm_yes")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_preview")]
            ])
        )
        return CONFIRM_BROADCAST

    elif data == "change_content":
        await query.edit_message_text("Ок, отправьте новое сообщение:")
        return WAITING_FOR_CONTENT

    elif data == "cancel":
        await query.delete_message()
        await query.message.reply_text("Рассылка отменена.")
        context.user_data.clear()
        return ConversationHandler.END

async def confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 4: Финальное подтверждение и рассылка"""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_to_preview":
        await query.delete_message()
        await show_preview(update, context)
        return PREVIEW_ACTION

    if data == "confirm_yes":
        await query.edit_message_text("🚀 Рассылка запущена! Я сообщу, когда закончу.")
        
        # Запускаем фоновую задачу, чтобы не блокировать бота
        admin_chat_id = update.effective_user.id
        context.application.create_task(run_broadcast_task(admin_chat_id, context))
        
        return ConversationHandler.END

async def run_broadcast_task(admin_chat_id, context: ContextTypes.DEFAULT_TYPE):
    """Функция самой рассылки (фоновая)"""
    msg_id = context.user_data['broadcast_msg_id']
    from_chat = context.user_data['broadcast_chat_id']
    
    all_users = stats_manager.get_all_users()
    
    success = 0
    blocked = 0
    errors = 0

    status_msg = await context.bot.send_message(
        chat_id=admin_chat_id, 
        text=f"🚀 Рассылка началась на {len(all_users)} пользователей..."
    )

    for i, user_id in enumerate(all_users):
        try:
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=from_chat,
                message_id=msg_id
            )
            success += 1
            await asyncio.sleep(0.1) # Лимит ~10 сообщений в сек (лимит 30)
            
        except Forbidden:
            blocked += 1
            # db.set_user_inactive(user_id)
        except Exception as e:
            errors += 1
            print(f"Error broadcast to {user_id}: {e}")
        
        if i % 100 == 0 and i > 0:
             try:
                await context.bot.edit_message_text(
                    chat_id=admin_chat_id,
                    message_id=status_msg.message_id,
                    text=f"🚀 Процесс: {i}/{len(all_users)}"
                )
             except: pass

    # Отчет админу
    await context.bot.send_message(
        chat_id=admin_chat_id,
        text=(
            f"🏁 *Рассылка завершена*\n\n"
            f"✅ Успешно: {success}\n"
            f"🚫 Бот заблокирован: {blocked}\n"
            f"⚠️ Ошибки: {errors}"
        ),
        parse_mode="Markdown"
    )
    # Очищаем данные
    context.user_data.pop('broadcast_msg_id', None)
    context.user_data.pop('broadcast_chat_id', None)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.")
    return ConversationHandler.END

broadcast_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_broadcast, pattern="^broadcast$")],
    states={
        WAITING_FOR_CONTENT: [
            MessageHandler(filters.ALL & ~filters.COMMAND, receive_content)
        ],
        PREVIEW_ACTION: [
            CallbackQueryHandler(preview_callback)
        ],
        CONFIRM_BROADCAST: [
            CallbackQueryHandler(confirm_callback)
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)
