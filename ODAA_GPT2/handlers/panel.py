import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from ODAA_GPT2.models import Teacher, Student, SessionLocal
from ODAA_GPT2.utils.keyboards import get_teacher_keyboard

logger = logging.getLogger(__name__)

# Определяем состояния для панели управления учителем
TEACHER_SELECT_STUDENT, TEACHER_ACTION_SELECTION, TEACHER_EDIT_LESSON_DATE, TEACHER_EDIT_HOMEWORK = range(20, 24)

async def panel_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    session = SessionLocal()
    teacher = session.query(Teacher).filter(Teacher.telegram_id == update.effective_user.id).first()
    if not teacher:
        await update.message.reply_text(
            "Функция 'Панель управления' доступна только для участников школы и студии.",
            reply_markup=ReplyKeyboardRemove()
        )
        session.close()
        return ConversationHandler.END
    context.user_data.pop("selected_student_id", None)
    students = session.query(Student).all()
    session.close()
    if not students:
        await update.message.reply_text(
            "В данный момент нет зарегистрированных учеников.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    keyboard = [[KeyboardButton(f"{s.first_name} {s.last_name}")] for s in students]
    keyboard.append([KeyboardButton("Отмена")])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Выберите ученика для управления:", reply_markup=reply_markup)
    return TEACHER_SELECT_STUDENT

async def teacher_select_student(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text.lower() == "отмена":
        await update.message.reply_text("Действие отменено.", reply_markup=get_teacher_keyboard())
        return ConversationHandler.END
    if " " not in text:
        await update.message.reply_text("Неверный формат имени. Используйте 'Имя Фамилия'.", reply_markup=get_teacher_keyboard())
        return ConversationHandler.END
    first_name, last_name = text.split(" ", 1)
    session = SessionLocal()
    student = session.query(Student).filter(
        Student.first_name == first_name,
        Student.last_name == last_name
    ).first()
    session.close()
    if not student:
        await update.message.reply_text("Ученик не найден. Попробуйте ещё раз.", reply_markup=get_teacher_keyboard())
        return ConversationHandler.END
    context.user_data["selected_student_id"] = student.telegram_id
    keyboard = [
        [KeyboardButton("Следующий урок")],
        [KeyboardButton("Редактировать урок")],
        [KeyboardButton("Посмотреть задание")],
        [KeyboardButton("Назад")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        f"Вы выбрали ученика: {student.first_name} {student.last_name}. Выберите действие:",
        reply_markup=reply_markup
    )
    return TEACHER_ACTION_SELECTION

async def teacher_action_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    action = update.message.text.strip().lower()
    if action == "назад":
        return await panel_start(update, context)
    elif action == "следующий урок":
        session = SessionLocal()
        student = session.query(Student).filter(Student.telegram_id == context.user_data["selected_student_id"]).first()
        session.close()
        if student:
            status = "Выполнено" if student.homework and "Сдано:" in student.homework else "Не выполнено"
            await update.message.reply_text(
                f"Ученик {student.first_name} {student.last_name}:\nУрок: {student.next_lesson}\nСтатус домашнего задания: {status}",
                reply_markup=get_teacher_keyboard()
            )
        else:
            await update.message.reply_text("Информация о студенте недоступна.", reply_markup=get_teacher_keyboard())
        return ConversationHandler.END
    elif action == "редактировать урок":
        keyboard = [[KeyboardButton("Назад")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            "Введите дату и время следующего урока (например, 2025-02-08 10:00):",
            reply_markup=reply_markup
        )
        return TEACHER_EDIT_LESSON_DATE
    elif action == "посмотреть задание":
        student_id = context.user_data.get("selected_student_id")
        session = SessionLocal()
        student = session.query(Student).filter(Student.telegram_id == student_id).first()
        session.close()
        if student and student.next_lesson and student.homework:
            await update.message.reply_text(
                f"Ученик {student.first_name} {student.last_name}:\nУрок: {student.next_lesson}\nДомашнее задание: {student.homework}",
                reply_markup=get_teacher_keyboard()
            )
        else:
            await update.message.reply_text(
                "Для этого ученика пока не назначены урок и домашнее задание.",
                reply_markup=get_teacher_keyboard()
            )
        return ConversationHandler.END
    else:
        await update.message.reply_text("Пожалуйста, выберите одно из предложенных действий.", reply_markup=get_teacher_keyboard())
        return ConversationHandler.END

async def teacher_edit_lesson_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text.lower() == "назад":
        return await teacher_action_selection(update, context)
    context.user_data["next_lesson"] = text
    keyboard = [[KeyboardButton("Назад")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Введите домашнее задание для ученика:", reply_markup=reply_markup)
    return TEACHER_EDIT_HOMEWORK

async def teacher_edit_homework(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text.lower() == "назад":
        return await teacher_action_selection(update, context)
    homework = text
    selected_student_id = context.user_data.get("selected_student_id")
    next_lesson = context.user_data.get("next_lesson")
    session = SessionLocal()
    student = session.query(Student).filter(Student.telegram_id == selected_student_id).first()
    if student:
        student.next_lesson = next_lesson
        student.homework = homework
        session.commit()
    session.close()
    app = context.application
    await app.bot.send_message(
        chat_id=selected_student_id, 
        text=f"📢 Вам назначен следующий урок на {next_lesson}.\nДомашнее задание: {homework}"
    )
    session = SessionLocal()
    teachers = session.query(Teacher).all()
    session.close()
    for t in teachers:
        await app.bot.send_message(
            chat_id=t.telegram_id, 
            text=f"Ученик {student.first_name} {student.last_name} получил назначение:\nУрок: {next_lesson}\nДомашнее задание: {homework}"
        )
    await update.message.reply_text("Урок и домашнее задание успешно назначены! 👍", reply_markup=get_teacher_keyboard())
    return ConversationHandler.END

async def teacher_panel_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Действие отменено.", reply_markup=get_teacher_keyboard())
    return ConversationHandler.END
