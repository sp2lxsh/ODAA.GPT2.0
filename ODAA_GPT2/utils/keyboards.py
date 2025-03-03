from telegram import KeyboardButton, ReplyKeyboardMarkup

def get_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("Участник школы и студии")],
        [KeyboardButton("Ученик")],
        [KeyboardButton("Записаться на бесплатный пробный урок")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_teacher_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("Панель управления")],
        [KeyboardButton("Сделать объявление")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_student_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("Мой урок")],
        [KeyboardButton("Мое домашнее задание")],
        [KeyboardButton("Прикрепить домашнее задание")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_trial_quiz_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("Пройти опрос")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_course_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("Мастер ПК")],
        [KeyboardButton("WOW Design & AI 2.0")],
        [KeyboardButton("Web Интенсив с 0 до PRO")],
        [KeyboardButton("Контент Креатор")],
        [KeyboardButton("Нейро Старт")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_schedule_choice_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("Написать дату и время")],
        [KeyboardButton("Напишите мне для согласования")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
