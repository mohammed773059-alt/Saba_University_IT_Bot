import os
import threading
from flask import Flask
import telebot
from dotenv import load_dotenv

import database
import handlers_student
import handlers_admin

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("⚠️ TELEGRAM_BOT_TOKEN مفقود في متغيرات البيئة!")

bot = telebot.TeleBot(TOKEN)
database.init_db()

# تسجيل معالجات الطلاب والإدارة
handlers_student.register_student_handlers(bot)
handlers_admin.register_admin_handlers(bot)

app = Flask(__name__)

@app.route('/')
def home():
    return "Saba University IT Bot is active and running successfully!"

def run_telegram_bot():
    print("🤖 البوت يعمل الآن بنجاح...")
    # مسح أي تواصل ويب هوك سابق لضمان عمل الأزرار بشكل فوري
    bot.remove_webhook()
    bot.infinity_polling(none_stop=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    
    # تشغيل البوت في الخلفية
    bot_thread = threading.Thread(target=run_telegram_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # تشغيل خادم الويب لـ Render
    app.run(host="0.0.0.0", port=port)
