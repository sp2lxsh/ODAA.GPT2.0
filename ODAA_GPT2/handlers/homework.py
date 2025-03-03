import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from ODAA_GPT2.models import Teacher, Student, SessionLocal
from ODAA_GPT2.utils.keyboards import get_main_keyboard, get_student_keyboard

logger = logging.getLogger(__name__)

# Константа для состояния обработки домашнего задания
SUBMIT_HOMEWORK = 60

# Обработчик начала прикрепления домашнего задания
async def attach_homework_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    session = SessionLocal()
    student = session.query(Student).filter(Student.telegram_id == user.id).first()
    session.close()
    if not student:
        await update.message.reply_text(
            "Эта функция доступна только для зарегистрированных учеников. Пожалуйста, зарегистрируйтесь.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    await update.message.reply_text(
        "📎 Отправьте файл, фото или текст (например, ссылку) с вашим домашним заданием.\nЕсли вы закончили, нажмите кнопку 'Готово'.",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Готово")]], resize_keyboard=True)
    )
    return SUBMIT_HOMEWORK

# Обработчик получения домашнего задания
async def attach_homework_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text and update.message.text.strip().lower() == "готово":
        await update.message.reply_text("Домашнее задание обновлено.", reply_markup=get_student_keyboard())
        return ConversationHandler.END

    submission = None
    if update.message.document:
        submission = f"Документ (file_id: {update.message.document.file_id})"
    elif update.message.photo:
        submission = f"Фото (file_id: {update.message.photo[-1].file_id})"
    elif update.message.text:
        if update.message.text.strip() in ["Мой урок", "Мое домашнее задание", "Прикрепить домашнее задание"]:
            await update.message.reply_text(
                "Пожалуйста, отправьте файл, фото или ссылку с вашим домашним заданием, или нажмите 'Готово' если завершили.",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Готово")]], resize_keyboard=True)
            )
            return SUBMIT_HOMEWORK
        submission = update.message.text.strip()
    
    if not submission:
        await update.message.reply_text(
            "Не удалось определить тип отправленного материала. Попробуйте ещё раз, отправив документ, фото или текст."
        )
        return SUBMIT_HOMEWORK

    user = update.effective_user
    session = SessionLocal()
    student = session.query(Student).filter(Student.telegram_id == user.id).first()
    if student:
        if student.homework:
            student.homework += f"\nСдано: {submission}"
        else:
            student.homework = f"Сдано: {submission}"
        session.commit()
    session.close()
    
    await update.message.reply_text(
        "✅ Ваше домашнее задание получено! Если хотите добавить ещё, отправьте ещё или нажмите 'Готово'.",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Готово")]], resize_keyboard=True)
    )
    
    session = SessionLocal()
    teachers = session.query(Teacher).all()
    session.close()
    app = context.application
    notify_text = f"Ученик {student.first_name} {student.last_name} прикрепил домашнее задание:\n{submission}"
    for teacher in teachers:
        try:
            await app.bot.send_message(chat_id=teacher.telegram_id, text=notify_text)
        except Exception as e:
            logger.error(f"Ошибка уведомления учителю {teacher.telegram_id}: {e}")
    return SUBMIT_HOMEWORK

# Обработчик просмотра домашнего задания ученика
async def view_homework(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    session = SessionLocal()
    student = session.query(Student).filter(Student.telegram_id == user.id).first()
    session.close()
    if student and student.homework:
        await update.message.reply_text(f"Ваше домашнее задание:\n{student.homework}", reply_markup=get_student_keyboard())
    else:
        await update.message.reply_text("Для вас домашнее задание ещё не назначено.", reply_markup=get_student_keyboard())

# Обработчик просмотра информации о следующем уроке
async def view_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    session = SessionLocal()
    student = session.query(Student).filter(Student.telegram_id == user.id).first()
    session.close()
    if student and student.next_lesson:
        await update.message.reply_text(f"Ваш следующий урок назначен на: {student.next_lesson}", reply_markup=get_student_keyboard())
    else:
        await update.message.reply_text("Информация о следующем уроке ещё не назначена.", reply_markup=get_student_keyboard())
