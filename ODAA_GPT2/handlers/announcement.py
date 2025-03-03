import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from ODAA_GPT2.models import Teacher, Student, SessionLocal
from ODAA_GPT2.utils.keyboards import get_teacher_keyboard

logger = logging.getLogger(__name__)

# Константа состояния для объявления
ANNOUNCE_TEXT = 30

async def announce_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    session = SessionLocal()
    teacher = session.query(Teacher).filter(Teacher.telegram_id == user.id).first()
    session.close()
    if not teacher:
        await update.message.reply_text(
            "Функция 'Сделать объявление' доступна только для участников школы и студии.",
            reply_markup=get_teacher_keyboard()
        )
        return ConversationHandler.END
    await update.message.reply_text(
        "📝 Пожалуйста, введите текст объявления.\nЕсли передумали – нажмите кнопку 'Отмена'.",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]], resize_keyboard=True)
    )
    return ANNOUNCE_TEXT

async def announce_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    announcement_text = update.message.text.strip()
    if announcement_text.lower() == "отмена":
        return await announce_cancel(update, context)
    session = SessionLocal()
    teachers = session.query(Teacher).all()
    students = session.query(Student).all()
    session.close()
    # Формируем множество получателей: все учителя и ученики
    recipients = {t.telegram_id for t in teachers} | {s.telegram_id for s in students}
    app = context.application
    for recipient in recipients:
        try:
            await app.bot.send_message(chat_id=recipient, text=f"📢 Объявление:\n{announcement_text}")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения пользователю {recipient}: {e}")
    await update.message.reply_text(
        "Ваше объявление успешно отправлено! 📢 Спасибо!",
        reply_markup=get_teacher_keyboard()
    )
    return ConversationHandler.END

async def announce_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Отмена объявления. Вы вернулись в главное меню. 👍",
        reply_markup=get_teacher_keyboard()
    )
    return ConversationHandler.END
