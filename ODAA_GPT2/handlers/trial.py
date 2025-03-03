import logging
import random
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from ODAA_GPT2.models import Teacher, Student, SessionLocal
from ODAA_GPT2.utils.keyboards import get_course_keyboard, get_schedule_choice_keyboard, get_trial_quiz_keyboard

logger = logging.getLogger(__name__)

# Определяем состояния для пробного урока и опроса
TRIAL_PHONE, TRIAL_NAME, TRIAL_COURSE, TRIAL_SCHEDULE_CHOICE, TRIAL_DATE_TIME, TRIAL_CONFIRMATION = range(40, 46)
QUIZ_QUESTION = 50

# Полный глобальный словарь с данными опроса
quiz_data = {
    "Мастер ПК": [
        {
            "question": "Что такое операционная система?",
            "options": [
                "Программа для управления компьютерными ресурсами",
                "Компьютерная игра",
                "Антивирусная программа",
                "Игровой движок"
            ],
            "answer": "Программа для управления компьютерными ресурсами",
            "explanation": "Операционная система управляет аппаратными ресурсами компьютера и обеспечивает работу приложений."
        },
        {
            "question": "Какую программу обычно используют для обработки текстов?",
            "options": [
                "Microsoft Excel",
                "Microsoft Word",
                "Adobe Illustrator",
                "Mozilla Firefox"
            ],
            "answer": "Microsoft Word",
            "explanation": "Microsoft Word — стандартный текстовый редактор для создания и редактирования документов."
        },
        {
            "question": "Что такое компьютерный вирус?",
            "options": [
                "Безобидная программа",
                "Программа, улучшающая производительность",
                "Вредоносная программа",
                "Программа для редактирования фото"
            ],
            "answer": "Вредоносная программа",
            "explanation": "Компьютерный вирус — это вредоносное ПО, предназначенное для повреждения или несанкционированного доступа."
        },
        {
            "question": "Какой из этих браузеров является популярным?",
            "options": [
                "Google Chrome",
                "Microsoft Word",
                "Adobe Photoshop",
                "Steam"
            ],
            "answer": "Google Chrome",
            "explanation": "Google Chrome популярен благодаря своей скорости, безопасности и множеству расширений."
        },
        {
            "question": "Какой язык программирования используется для создания скриптов в Windows?",
            "options": [
                "Bash",
                "PowerShell",
                "Python",
                "Java"
            ],
            "answer": "PowerShell",
            "explanation": "PowerShell — встроенный инструмент Windows для автоматизации задач."
        },
        {
            "question": "Что такое файл?",
            "options": [
                "Физический носитель информации",
                "Набор данных, сохраненных на диске",
                "Операционная система",
                "Компьютерная сеть"
            ],
            "answer": "Набор данных, сохраненных на диске",
            "explanation": "Файл — логически связанный набор данных, сохраненный в файловой системе."
        },
        {
            "question": "Какой компонент компьютера отвечает за обработку данных?",
            "options": [
                "Процессор",
                "Жесткий диск",
                "Оперативная память",
                "Видеокарта"
            ],
            "answer": "Процессор",
            "explanation": "Процессор (CPU) выполняет арифметические и логические операции, обрабатывая данные."
        },
        {
            "question": "Что означает термин 'интернет'?",
            "options": [
                "Локальная сеть",
                "Глобальная сеть, объединяющая компьютеры по всему миру",
                "Офисное приложение",
                "Файловый менеджер"
            ],
            "answer": "Глобальная сеть, объединяющая компьютеры по всему миру",
            "explanation": "Интернет — всемирная сеть, соединяющая миллионы устройств для обмена информацией."
        },
        {
            "question": "Какая программа используется для просмотра веб-страниц?",
            "options": [
                "Браузер",
                "Текстовый редактор",
                "Плеер",
                "Антивирус"
            ],
            "answer": "Браузер",
            "explanation": "Браузер позволяет отображать и взаимодействовать с веб-страницами через интернет."
        },
        {
            "question": "Что такое облачное хранилище?",
            "options": [
                "Местное жесткое дисковое пространство",
                "Устройство для создания резервных копий",
                "Удалённое хранилище данных, доступное через интернет",
                "Программа для защиты компьютера"
            ],
            "answer": "Удалённое хранилище данных, доступное через интернет",
            "explanation": "Облачное хранилище хранит данные на удалённых серверах, доступных онлайн."
        }
    ],
    "WOW Design & AI 2.0": [
        {
            "question": "Что такое дизайн?",
            "options": [
                "Процесс создания визуальных концепций",
                "Программирование веб-сайтов",
                "Администрирование серверов",
                "Настройка оборудования"
            ],
            "answer": "Процесс создания визуальных концепций"
        },
        {
            "question": "Какой инструмент часто используется для создания макетов в дизайне?",
            "options": [
                "Figma",
                "Visual Studio Code",
                "Blender",
                "Excel"
            ],
            "answer": "Figma"
        },
        {
            "question": "Что такое AI?",
            "options": [
                "Искусственный интеллект",
                "Автоматический индекс",
                "Антивирусная система",
                "Интернет-магазин"
            ],
            "answer": "Искусственный интеллект"
        },
        {
            "question": "Какой термин описывает гармоничное сочетание цветов в дизайне?",
            "options": [
                "Контраст",
                "Цветовая палитра",
                "Минимализм",
                "Типографика"
            ],
            "answer": "Цветовая палитра"
        },
        {
            "question": "Что такое прототипирование?",
            "options": [
                "Создание предварительной версии продукта для тестирования",
                "Процесс финального дизайна",
                "Написание кода для приложения",
                "Разработка логотипа"
            ],
            "answer": "Создание предварительной версии продукта для тестирования"
        },
        {
            "question": "Какой из этих терминов связан с пользовательским интерфейсом?",
            "options": [
                "UI/UX",
                "API",
                "SQL",
                "HTTP"
            ],
            "answer": "UI/UX"
        },
        {
            "question": "Что такое векторная графика?",
            "options": [
                "Изображения, основанные на математических формулах",
                "Фотографии высокого разрешения",
                "3D модели",
                "Видео форматы"
            ],
            "answer": "Изображения, основанные на математических формулах"
        },
        {
            "question": "Какой формат файла обычно используется для сохранения векторной графики?",
            "options": [
                "JPEG",
                "PNG",
                "SVG",
                "GIF"
            ],
            "answer": "SVG"
        },
        {
            "question": "Что такое макет?",
            "options": [
                "План дизайна страницы",
                "Финальный продукт",
                "Программный код",
                "Пользовательское соглашение"
            ],
            "answer": "План дизайна страницы"
        },
        {
            "question": "Какой термин описывает интуитивность и удобство использования интерфейса?",
            "options": [
                "Юзабилити",
                "Доступность",
                "Скорость",
                "Безопасность"
            ],
            "answer": "Юзабилити"
        }
    ],
    "Web Интенсив с 0 до PRO": [
        {
            "question": "Что такое HTML?",
            "options": [
                "Язык разметки для создания веб-страниц",
                "Язык программирования для серверов",
                "Система управления базами данных",
                "Фреймворк для веб-приложений"
            ],
            "answer": "Язык разметки для создания веб-страниц"
        },
        {
            "question": "Что такое CSS?",
            "options": [
                "Язык стилей для оформления веб-страниц",
                "Язык программирования",
                "База данных",
                "Серверное ПО"
            ],
            "answer": "Язык стилей для оформления веб-страниц"
        },
        {
            "question": "Что такое JavaScript?",
            "options": [
                "Язык программирования для динамики веб-страниц",
                "Язык разметки",
                "Стиль оформления",
                "Серверный язык"
            ],
            "answer": "Язык программирования для динамики веб-страниц"
        },
        {
            "question": "Как называется фреймворк для JavaScript, используемый для создания пользовательских интерфейсов?",
            "options": [
                "React",
                "Django",
                "Laravel",
                "Flask"
            ],
            "answer": "React"
        },
        {
            "question": "Что такое API?",
            "options": [
                "Интерфейс для взаимодействия между программами",
                "Язык программирования",
                "Система управления контентом",
                "База данных"
            ],
            "answer": "Интерфейс для взаимодействия между программами"
        },
        {
            "question": "Какой тег используется для вставки изображения в HTML?",
            "options": [
                "<img>",
                "<div>",
                "<span>",
                "<a>"
            ],
            "answer": "<img>"
        },
        {
            "question": "Что такое responsive design?",
            "options": [
                "Дизайн, адаптирующийся под разные устройства",
                "Статичный дизайн",
                "Дизайн с использованием только HTML",
                "Метод оптимизации баз данных"
            ],
            "answer": "Дизайн, адаптирующийся под разные устройства"
        },
        {
            "question": "Какой язык обычно используется для серверной части веб-приложений?",
            "options": [
                "Python",
                "CSS",
                "HTML",
                "XML"
            ],
            "answer": "Python"
        },
        {
            "question": "Что такое Bootstrap?",
            "options": [
                "Фреймворк для создания адаптивных веб-сайтов",
                "Язык программирования",
                "База данных",
                "Система контроля версий"
            ],
            "answer": "Фреймворк для создания адаптивных веб-сайтов"
        },
        {
            "question": "Что такое DOM?",
            "options": [
                "Объектная модель документа, представляющая структуру веб-страницы",
                "Язык разметки",
                "Система управления базами данных",
                "Метод стилизации веб-страниц"
            ],
            "answer": "Объектная модель документа, представляющая структуру веб-страницы"
        }
    ],
    "Контент Креатор": [
        {
            "question": "Что такое контент?",
            "options": [
                "Информация, предоставляемая в цифровом виде",
                "Операционная система",
                "Программное обеспечение",
                "Веб-сервер"
            ],
            "answer": "Информация, предоставляемая в цифровом виде"
        },
        {
            "question": "Что такое SMM?",
            "options": [
                "Маркетинг в социальных сетях",
                "Система управления маркетингом",
                "Программирование на Java",
                "Офисный пакет"
            ],
            "answer": "Маркетинг в социальных сетях"
        },
        {
            "question": "Какой формат лучше всего подходит для видео-контента?",
            "options": [
                "MP4",
                "DOCX",
                "MP3",
                "JPEG"
            ],
            "answer": "MP4"
        },
        {
            "question": "Что такое вирусный контент?",
            "options": [
                "Контент, который быстро распространяется среди пользователей",
                "Опасный программный код",
                "Контент, созданный вирусами",
                "Низкокачественная информация"
            ],
            "answer": "Контент, который быстро распространяется среди пользователей"
        },
        {
            "question": "Какой из следующих инструментов часто используется для редактирования видео?",
            "options": [
                "Adobe Premiere Pro",
                "Microsoft Word",
                "Google Sheets",
                "Notepad"
            ],
            "answer": "Adobe Premiere Pro"
        },
        {
            "question": "Что такое блог?",
            "options": [
                "Онлайн-дневник или журнал",
                "Система управления базами данных",
                "Программа для редактирования фотографий",
                "Операционная система"
            ],
            "answer": "Онлайн-дневник или журнал"
        },
        {
            "question": "Что такое инфографика?",
            "options": [
                "Графическое представление информации",
                "Тип вируса",
                "Программное обеспечение для анализа данных",
                "Способ хранения данных"
            ],
            "answer": "Графическое представление информации"
        },
        {
            "question": "Какой социальной медиа-платформой часто пользуются для публикации коротких видео?",
            "options": [
                "TikTok",
                "LinkedIn",
                "Reddit",
                "GitHub"
            ],
            "answer": "TikTok"
        },
        {
            "question": "Что такое SEO?",
            "options": [
                "Оптимизация сайта для поисковых систем",
                "Способ создания видео",
                "Техника программирования",
                "Тип графического дизайна"
            ],
            "answer": "Оптимизация сайта для поисковых систем"
        },
        {
            "question": "Что является ключевым элементом успешного SMM?",
            "options": [
                "Активное взаимодействие с аудиторией",
                "Наличие сложного кода",
                "Высокая стоимость рекламы",
                "Отсутствие обратной связи"
            ],
            "answer": "Активное взаимодействие с аудиторией"
        }
    ],
    "Нейро Старт": [
        {
            "question": "Что такое нейросеть?",
            "options": [
                "Компьютерная программа",
                "Математическая модель",
                "Игровой алгоритм",
                "Программное обеспечение"
            ],
            "answer": "Математическая модель"
        },
        {
            "question": "Какой язык чаще всего используется для работы с нейросетями?",
            "options": [
                "Python",
                "JavaScript",
                "Java",
                "C#"
            ],
            "answer": "Python"
        },
        {
            "question": "Что такое машинное обучение?",
            "options": [
                "Метод обучения на данных",
                "Способ тренировки спортсменов",
                "Формула для вычислений",
                "Техника программирования"
            ],
            "answer": "Метод обучения на данных"
        },
        {
            "question": "Какой инструмент часто используют для создания нейросетей?",
            "options": [
                "TensorFlow",
                "Excel",
                "Photoshop",
                "PowerPoint"
            ],
            "answer": "TensorFlow"
        }
    ]
}

# -------------------------
# Обработчики записи на бесплатный пробный урок

async def handle_trial_registration_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["trial_data"] = {}
    await update.message.reply_text(
        "😊 Отлично! Давайте запишемся на бесплатный пробный урок.\n\nВведите, пожалуйста, ваш номер телефона:"
    )
    return TRIAL_PHONE

async def trial_phone_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone = update.message.text.strip()
    context.user_data["trial_data"]["phone"] = phone
    await update.message.reply_text("Спасибо! Теперь введите ваше имя:")
    return TRIAL_NAME

async def trial_name_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    context.user_data["trial_data"]["name"] = name
    await update.message.reply_text("Выберите курс, который вас интересует:", reply_markup=get_course_keyboard())
    return TRIAL_COURSE

async def trial_course_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    course = update.message.text.strip()
    valid_courses = ["Мастер ПК", "WOW Design & AI 2.0", "Web Интенсив с 0 до PRO", "Контент Креатор", "Нейро Старт"]
    if course not in valid_courses:
        await update.message.reply_text("Пожалуйста, выберите курс из предложенных вариантов.", reply_markup=get_course_keyboard())
        return TRIAL_COURSE
    context.user_data["trial_data"]["course"] = course
    descriptions = {
        "Мастер ПК": "Будешь с компьютером на 'ты' и познакомишься с офисными программами.",
        "WOW Design & AI 2.0": "Освоишь дизайн и начнешь свой путь в новой профессии.",
        "Web Интенсив с 0 до PRO": "Разработаешь свой сайт с нуля.",
        "Контент Креатор": "Пройдешь путь от новичка до профи в SMM.",
        "Нейро Старт": "Нейросети станут твоим личным ассистентом."
    }
    await update.message.reply_text(f"Вы выбрали курс: {course}\nОписание: {descriptions[course]}")
    await update.message.reply_text("Напишите дату, удобную для проведения пробного урока, или выберите вариант ниже:", reply_markup=get_schedule_choice_keyboard())
    return TRIAL_SCHEDULE_CHOICE

async def trial_schedule_choice_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text.strip()
    if choice == "Написать дату и время":
        await update.message.reply_text("Введите дату и время пробного урока (например, 2025-02-08 10:00):", reply_markup=ReplyKeyboardRemove())
        return TRIAL_DATE_TIME
    elif choice == "Напишите мне для согласования":
        context.user_data["trial_data"]["date_time"] = "Для согласования"
        return await trial_registration_confirmation(update, context)
    else:
        await update.message.reply_text("Пожалуйста, выберите один из вариантов.", reply_markup=get_schedule_choice_keyboard())
        return TRIAL_SCHEDULE_CHOICE

async def trial_date_time_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    date_time = update.message.text.strip()
    context.user_data["trial_data"]["date_time"] = date_time
    return await trial_registration_confirmation(update, context)

async def trial_registration_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    trial_info = context.user_data.get("trial_data", {})
    name = trial_info.get("name")
    phone = trial_info.get("phone")
    course = trial_info.get("course")
    date_time = trial_info.get("date_time")
    confirmation_message = (
        f"🎉 Спасибо, {name}! Вы успешно записаны на пробный урок по курсу «{course}» на время: {date_time}.\n"
        "Наш куратор скоро свяжется с вами для подтверждения."
    )
    await update.message.reply_text(confirmation_message, reply_markup=get_trial_quiz_keyboard())
    
    session = SessionLocal()
    teachers = session.query(Teacher).all()
    session.close()
    app = context.application
    notify_text = f"Новая заявка на пробный урок:\nИмя: {name}\nТелефон: {phone}\nКурс: {course}\nВремя: {date_time}"
    for teacher in teachers:
        try:
            await app.bot.send_message(chat_id=teacher.telegram_id, text=notify_text)
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления учителю {teacher.telegram_id}: {e}")
    return ConversationHandler.END

# -------------------------
# Обработчики опроса

async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    trial_info = context.user_data.get("trial_data")
    if not trial_info or "course" not in trial_info:
        await update.message.reply_text("Сначала, пожалуйста, запишитесь на пробный урок.")
        return ConversationHandler.END
    course = trial_info["course"]
    questions = quiz_data.get(course)
    if not questions:
        await update.message.reply_text("Опрос для выбранного курса пока не подготовлен.")
        return ConversationHandler.END
    context.user_data["quiz"] = {
        "questions": questions,
        "current": 0,
        "score": 0
    }
    await send_quiz_question(update, context)
    return QUIZ_QUESTION

async def send_quiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    quiz = context.user_data.get("quiz")
    questions = quiz.get("questions")
    current = quiz.get("current")
    if current < len(questions):
        q = questions[current]
        options = list(q["options"])
        random.shuffle(options)
        keyboard = ReplyKeyboardMarkup([[KeyboardButton(option)] for option in options],
                                       one_time_keyboard=True, resize_keyboard=True)
        question_text = f"Вопрос {current+1} из {len(questions)}:\n{q['question']}"
        await update.message.reply_text(question_text, reply_markup=keyboard)
    else:
        await finish_quiz(update, context)

async def quiz_answer_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    selected_option = update.message.text.strip()
    quiz = context.user_data.get("quiz")
    questions = quiz.get("questions")
    current = quiz.get("current")
    q = questions[current]
    if selected_option == q["answer"]:
        feedback = "✅ Правильно! Отличный ответ! 👍"
        quiz["score"] += 1
    else:
        explanation = q.get("explanation", "Это базовая информация по теме.")
        feedback = f"❌ Неверно. Правильный ответ: {q['answer']}.\nОбъяснение: {explanation}"
    await update.message.reply_text(feedback, reply_markup=ReplyKeyboardRemove())
    quiz["current"] += 1
    if quiz["current"] < len(questions):
        await send_quiz_question(update, context)
        return QUIZ_QUESTION
    else:
        return await finish_quiz(update, context)

async def finish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    quiz = context.user_data.get("quiz")
    score = quiz.get("score")
    total = len(quiz.get("questions"))
    percentage = int((score / total) * 100)
    if score >= 7:
        result_text = (
            f"Отлично! 🎉 Вы ответили правильно на {score} из {total} вопросов ({percentage}%). "
            "Ваши знания на высоте! Продолжайте в том же духе."
        )
    else:
        result_text = (
            f"Вы ответили правильно на {score} из {total} вопросов ({percentage}%). "
            "Не отчаивайтесь — всегда можно стать лучше. Мы готовы помочь вам на пути к успеху!"
        )
    await update.message.reply_text(result_text, reply_markup=ReplyKeyboardRemove())
    
    trial_info = context.user_data.get("trial_data", {})
    name = trial_info.get("name", "Неизвестно")
    course = trial_info.get("course", "Неизвестно")
    notify_text = f"Результаты опроса по курсу «{course}»\nУченик: {name}\nРезультат: {score} из {total}"
    
    session = SessionLocal()
    teachers = session.query(Teacher).all()
    session.close()
    app = context.application
    for teacher in teachers:
        try:
            await app.bot.send_message(chat_id=teacher.telegram_id, text=notify_text)
        except Exception as e:
            logger.error(f"Ошибка уведомления учителю {teacher.telegram_id}: {e}")
    context.user_data.pop("quiz", None)
    return ConversationHandler.END
