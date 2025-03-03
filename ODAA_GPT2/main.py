import logging
from datetime import datetime, timedelta
import pytz

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from ODAA_GPT2 import config

# Импорт обработчиков и констант состояний из пакета ODAA_GPT2
from ODAA_GPT2.handlers.auth import (
    teacher_login_start,
    teacher_login_receive,
    teacher_password_receive,
    teacher_cancel,
    student_registration_start,
    student_first_name_receive,
    student_last_name_receive,
    student_phone_receive,
    student_cancel,
    reset_role,
    TEACHER_LOGIN,
    TEACHER_PASSWORD,
    STUDENT_FIRST_NAME,
    STUDENT_LAST_NAME,
    STUDENT_PHONE,
)
from ODAA_GPT2.handlers.panel import (
    panel_start,
    teacher_select_student,
    teacher_action_selection,
    teacher_edit_lesson_date,
    teacher_edit_homework,
    teacher_panel_cancel,
    TEACHER_SELECT_STUDENT,
    TEACHER_ACTION_SELECTION,
    TEACHER_EDIT_LESSON_DATE,
    TEACHER_EDIT_HOMEWORK,
)
from ODAA_GPT2.handlers.trial import (
    handle_trial_registration_start,
    trial_phone_receive,
    trial_name_receive,
    trial_course_receive,
    trial_schedule_choice_receive,
    trial_date_time_receive,
    trial_registration_confirmation,
    quiz_start,
    quiz_answer_receive,
    QUIZ_QUESTION,
    TRIAL_PHONE,
    TRIAL_NAME,
    TRIAL_COURSE,
    TRIAL_SCHEDULE_CHOICE,
    TRIAL_DATE_TIME,
)
from ODAA_GPT2.handlers.homework import (
    attach_homework_start,
    attach_homework_receive,
    view_homework,
    view_lesson,
    SUBMIT_HOMEWORK,
)
from ODAA_GPT2.handlers.announcement import (
    announce_start,
    announce_receive,
    announce_cancel,
    ANNOUNCE_TEXT,
)
from ODAA_GPT2.handlers.openai_handler import openai_query

from ODAA_GPT2.utils.keyboards import get_main_keyboard, get_teacher_keyboard, get_student_keyboard, get_trial_quiz_keyboard

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    from ODAA_GPT2.models import Teacher, Student, SessionLocal
    session = SessionLocal()
    teacher = session.query(Teacher).filter(Teacher.telegram_id == user.id).first()
    student = session.query(Student).filter(Student.telegram_id == user.id).first()
    session.close()
    context.user_data.clear()
    if teacher:
        context.user_data["role"] = teacher.role
        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋\nВы уже авторизованы как {teacher.role} (логин: {teacher.login}).",
            reply_markup=get_teacher_keyboard()
        )
    elif student:
        context.user_data["role"] = student.role
        extra = ""
        if student.next_lesson or student.homework:
            extra = f"\nВаш следующий урок: {student.next_lesson}\nДомашнее задание: {student.homework}"
        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋\nВы уже зарегистрированы как {student.role}: {student.first_name} {student.last_name}.{extra}\nРоль изменить нельзя.",
            reply_markup=get_student_keyboard()
        )
    else:
        welcome_message = (
            f"Привет, {user.first_name}! 👋\n\n"
            "Добро пожаловать в Школу Дизайна и IT Технологий!\n"
            "Этот бот поможет вам получать напоминания о уроках, домашние задания и даже записаться на бесплатный пробный урок.\n\n"
            "Пожалуйста, выберите вашу роль:\n"
            "⚠️ После авторизации роль закрепляется и изменить её будет невозможно."
        )
        await update.message.reply_text(welcome_message, reply_markup=get_main_keyboard())

async def handle_simple_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("role"):
        await update.message.reply_text(
            "Ваша роль уже закреплена. Если хотите изменить её, воспользуйтесь командой /resetrole.",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text("Пожалуйста, выберите одну из предложенных ролей.", reply_markup=get_main_keyboard())

async def check_for_notifications(context: ContextTypes.DEFAULT_TYPE) -> None:
    from ODAA_GPT2.models import Student, Teacher, SessionLocal
    tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(tz)
    session = SessionLocal()
    students = session.query(Student).filter(Student.next_lesson.isnot(None)).all()
    for student in students:
        try:
            lesson_time = datetime.strptime(student.next_lesson, "%Y-%m-%d %H:%M")
            lesson_time = tz.localize(lesson_time)
        except Exception:
            continue
        day_before = lesson_time - timedelta(days=1)
        if now.date() == day_before.date() and now.hour == 20:
            if abs((now - day_before).total_seconds()) < 60:
                await context.bot.send_message(
                    chat_id=student.telegram_id,
                    text=f"Напоминание: завтра в {lesson_time.strftime('%H:%M')} у вас урок! ⏰"
                )
                teachers = session.query(Teacher).all()
                for teacher in teachers:
                    await context.bot.send_message(
                        chat_id=teacher.telegram_id,
                        text=f"Напоминание: ученик {student.first_name} {student.last_name} имеет урок завтра в {lesson_time.strftime('%H:%M')}."
                    )
        two_hours_before = lesson_time - timedelta(hours=2)
        if abs((now - two_hours_before).total_seconds()) < 60:
            await context.bot.send_message(
                chat_id=student.telegram_id,
                text=f"Напоминание: урок начинается через 2 часа в {lesson_time.strftime('%H:%M')}! ⏰"
            )
            teachers = session.query(Teacher).all()
            for teacher in teachers:
                await context.bot.send_message(
                    chat_id=teacher.telegram_id,
                    text=f"Напоминание: ученик {student.first_name} {student.last_name} имеет урок через 2 часа в {lesson_time.strftime('%H:%M')}."
                )
    session.close()

def main() -> None:
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    teacher_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Участник школы и студии$"), teacher_login_start)],
        states={
            TEACHER_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, teacher_login_receive)],
            TEACHER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, teacher_password_receive)],
        },
        fallbacks=[CommandHandler("cancel", teacher_cancel)],
    )

    student_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Ученик$"), student_registration_start)],
        states={
            STUDENT_FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, student_first_name_receive)],
            STUDENT_LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, student_last_name_receive)],
            STUDENT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, student_phone_receive)],
        },
        fallbacks=[CommandHandler("cancel", student_cancel)],
    )

    teacher_panel_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Панель управления$"), panel_start)],
        states={
            TEACHER_SELECT_STUDENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, teacher_select_student)],
            TEACHER_ACTION_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, teacher_action_selection)],
            TEACHER_EDIT_LESSON_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, teacher_edit_lesson_date)],
            TEACHER_EDIT_HOMEWORK: [MessageHandler(filters.TEXT & ~filters.COMMAND, teacher_edit_homework)],
        },
        fallbacks=[CommandHandler("cancel", teacher_panel_cancel)],
    )

    announce_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Сделать объявление$"), announce_start)],
        states={
            ANNOUNCE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, announce_receive)],
        },
        fallbacks=[CommandHandler("cancel", announce_cancel)],
    )

    trial_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Записаться на бесплатный пробный урок$"), handle_trial_registration_start)],
        states={
            TRIAL_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, trial_phone_receive)],
            TRIAL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, trial_name_receive)],
            TRIAL_COURSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, trial_course_receive)],
            TRIAL_SCHEDULE_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, trial_schedule_choice_receive)],
            TRIAL_DATE_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, trial_date_time_receive)],
        },
        fallbacks=[CommandHandler("cancel", teacher_cancel)],
    )

    quiz_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Пройти опрос$"), quiz_start)],
        states={
            QUIZ_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_answer_receive)]
        },
        fallbacks=[CommandHandler("cancel", teacher_cancel)],
    )

    homework_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Прикрепить домашнее задание$"), attach_homework_start)],
        states={
            SUBMIT_HOMEWORK: [MessageHandler(filters.ALL, attach_homework_receive)],
        },
        fallbacks=[CommandHandler("cancel", lambda update, context: update.message.reply_text("Отмена. Возврат в главное меню.", reply_markup=get_student_keyboard()))],
    )

    view_lesson_handler = MessageHandler(filters.Regex("^Мой урок$"), view_lesson)
    view_homework_handler = MessageHandler(filters.Regex("^Мое домашнее задание$"), view_homework)

    openai_handler = CommandHandler("ask", openai_query)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("resetrole", reset_role))
    application.add_handler(teacher_conv_handler)
    application.add_handler(student_conv_handler)
    application.add_handler(teacher_panel_handler)
    application.add_handler(announce_conv_handler)
    application.add_handler(trial_conv_handler)
    application.add_handler(quiz_conv_handler)
    application.add_handler(homework_conv_handler)
    application.add_handler(view_lesson_handler)
    application.add_handler(view_homework_handler)
    application.add_handler(openai_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_simple_user))

    application.job_queue.run_repeating(check_for_notifications, interval=60, first=10)

    application.run_polling()

if __name__ == '__main__':
    main()

