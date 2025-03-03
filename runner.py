import os
import threading
import asyncio
from flask import Flask
from ODAA_GPT2.main import main  # Импортируем функцию main() из вашего пакета

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running", 200

def run_web():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

def run_bot():
    # Создаём новый event loop для этого потока и устанавливаем его как текущий
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    main()  # Запускаем бота; main() вызывает application.run_polling()

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    run_web()
