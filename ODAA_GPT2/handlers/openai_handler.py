import openai
from ODAA_GPT2 import config  # импортируем наш конфигурационный файл
from telegram import Update
from telegram.ext import ContextTypes

async def openai_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Составляем текст запроса из аргументов команды
    user_query = " ".join(context.args)
    if not user_query:
        await update.message.reply_text(
            "Пожалуйста, введите ваш вопрос после команды /ask.\nНапример: /ask Как создать презентацию в PowerPoint?"
        )
        return

    # Устанавливаем API-ключ для OpenAI
    openai.api_key = config.OPENAI_API_KEY

    try:
        # Отправляем запрос к модели GPT-3.5 Turbo с использованием нового асинхронного метода
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_query}],
            temperature=0.7,
        )
        answer = response["choices"][0]["message"]["content"]
        await update.message.reply_text(answer)
    except Exception as e:
        await update.message.reply_text("Произошла ошибка при получении ответа от OpenAI.")
        print("Ошибка при запросе к OpenAI:", e)
