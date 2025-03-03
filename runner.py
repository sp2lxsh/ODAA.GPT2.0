import os
import threading
from flask import Flask
from ODAA_GPT2.main import main  # Импортируем функцию main() из вашего пакета

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running", 200

def run_web():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    # Запускаем Flask-сервер в отдельном потоке
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    
    # Запускаем бота в главном потоке
    main()
