import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from ODAA_GPT2.models import Teacher, Student, SessionLocal
from ODAA_GPT2.utils.keyboards import get_main_keyboard, get_teacher_keyboard, get_student_keyboard

# Константы состояний для авторизации/регистрации
TEACHER_LOGIN, TEACHER_PASSWORD = range(2)
STUDENT_FIRST_NAME, STUDENT_LAST_NAME, STUDENT_PHONE = range(10, 13)

# Жёстко заданные учётные данные для учителей (демо-данные)
teacher_credentials = {
    "andrey": "Andrey2025!",
    "ilya": "Ilya2025@",
    "angelina": "Angelina2025#",
    "vika": "Vika2025$",
    "ira": "Ira2025%",
    "mila": "Mila2025^",
    "kristina": "Kristina2025!",
    "vera": "Vera2025@",
    "katerina": "Katerina2025#"
}

logger = logging.getLogger(__name__)

# Функция сброса роли
async def reset_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    session = SessionLocal()
    teacher = session.query(Teacher).filter(Teacher.telegram_id == user.id).first()
    if teacher:
        session.delete(teacher)
        session.commit()
        context.user_data.clear()
        await update.message.reply_text(
            "Ваша роль учителя сброшена. Теперь вы можете заново выбрать роль. 🔄",
            reply_markup=ReplyKeyboardRemove()
        )
        session.close()
        return
    student = session.query(Student).filter(Student.telegram_id == user.id).first()
    if student:
        session.delete(student)
        session.commit()
        context.user_data.clear()
        await update.message.reply_text(
            "Ваша роль ученика сброшена. Теперь вы можете заново выбрать роль. 🔄",
            reply_markup=ReplyKeyboardRemove()
        )
        session.close()
        return
    session.close()
    await update.message.reply_text(
        "У вас нет закреплённой роли. Пожалуйста, выберите роль заново.",
        reply_markup=ReplyKeyboardRemove()
    )

# Обработчики авторизации учителей
async def teacher_login_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data.get("role"):
        await update.message.reply_text(
            "Ваша роль уже закреплена. Если хотите изменить её, воспользуйтесь сбросом роли.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    context.user_data["role"] = "Участник школы и студии"
    await update.message.reply_text(
        "Вы выбрали роль 👨‍🏫 *Участник школы и студии*.\nПожалуйста, введите ваш логин:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return TEACHER_LOGIN

async def teacher_login_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    login_input = update.message.text.strip()
    context.user_data["teacher_login"] = login_input
    await update.message.reply_text(
        "Введите пароль 🔐 (или нажмите 'Назад' для отмены):",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Назад")]], resize_keyboard=True)
    )
    return TEACHER_PASSWORD

async def teacher_password_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text.lower() == "назад":
        context.user_data.pop("role", None)
        await update.message.reply_text("Возврат в главное меню.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    password_input = text
    login_input = context.user_data.get("teacher_login")
    if login_input in teacher_credentials and teacher_credentials[login_input] == password_input:
        session = SessionLocal()
        existing = session.query(Teacher).filter(Teacher.telegram_id == update.effective_user.id).first()
        if not existing:
            teacher = Teacher(
                telegram_id=update.effective_user.id, 
                login=login_input,
                role="Участник школы и студии"
            )
            session.add(teacher)
            session.commit()
        session.close()
        await update.message.reply_text("Успешный вход! 🎉", reply_markup=get_teacher_keyboard())
    else:
        await update.message.reply_text("Ошибка: неверный логин или пароль. Попробуйте ещё раз.", reply_markup=ReplyKeyboardRemove())
        context.user_data.pop("role", None)
    return ConversationHandler.END

async def teacher_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("role", None)
    await update.message.reply_text("Авторизация отменена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Обработчики регистрации учеников
async def student_registration_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data.get("role"):
        await update.message.reply_text(
            "Ваша роль уже закреплена. Если хотите изменить её, воспользуйтесь сбросом роли.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    context.user_data["role"] = "Ученик"
    await update.message.reply_text(
        "Вы выбрали роль 🧑‍🎓 *Ученик*.\nПожалуйста, введите ваше имя:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return STUDENT_FIRST_NAME

async def student_first_name_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    first_name = update.message.text.strip()
    context.user_data["student_first_name"] = first_name
    await update.message.reply_text(
        "Введите вашу фамилию (или нажмите 'Назад' для отмены):",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Назад")]], resize_keyboard=True)
    )
    return STUDENT_LAST_NAME

async def student_last_name_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text.lower() == "назад":
        context.user_data.pop("role", None)
        await update.message.reply_text("Возврат в главное меню.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    last_name = text
    context.user_data["student_last_name"] = last_name
    await update.message.reply_text(
        "Теперь введите ваш номер телефона (или нажмите 'Назад' для отмены):",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Назад")]], resize_keyboard=True)
    )
    return STUDENT_PHONE

async def student_phone_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text.lower() == "назад":
        context.user_data.pop("role", None)
        await update.message.reply_text("Возврат в главное меню.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    phone = text
    first_name = context.user_data["student_first_name"]
    last_name = context.user_data["student_last_name"]
    session = SessionLocal()
    existing_student = session.query(Student).filter(Student.telegram_id == update.effective_user.id).first()
    if not existing_student:
        student = Student(
            telegram_id=update.effective_user.id, 
            first_name=first_name, 
            last_name=last_name, 
            phone=phone, 
            role="Ученик"
        )
        session.add(student)
        session.commit()
    session.close()
    await update.message.reply_text(
        f"🎉 Ура, {first_name} {last_name}! Ваша регистрация прошла успешно.\nВаш номер телефона: {phone}",
        reply_markup=get_student_keyboard()
    )
    return ConversationHandler.END

async def student_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("role", None)
    await update.message.reply_text("Регистрация отменена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
