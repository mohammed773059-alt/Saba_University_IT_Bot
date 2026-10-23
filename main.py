import os
import sqlite3
import logging
import telebot
from flask import Flask
from threading import Thread
from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

# =========================
# إعدادات البوت
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_USER_ID")
DB_FILE = "library.db"

logging.basicConfig(level=logging.INFO)

if not TOKEN:
    raise RuntimeError("أضف TELEGRAM_BOT_TOKEN في إعدادات Render.")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# =========================
# خادم Render
# =========================

@app.route("/")
def home():
    return "Saba University IT Bot is running!"

def run_server():
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )

# =========================
# قاعدة البيانات
# =========================

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                semester TEXT NOT NULL,
                subject TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                file_id TEXT,
                content_type TEXT,
                text_content TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT DEFAULT '',
                status TEXT DEFAULT 'قيد المراجعة'
            )
        """)

        conn.commit()

init_db()

# =========================
# المواد الدراسية
# =========================

SEMESTERS = {
    "الفصل الدراسي الأول": [
        "مهارة اللغة العربية 101",
        "مهارة اللغة الإنجليزية 101",
        "التفاضل والتكامل",
        "فيزياء عامة للحوسبة",
        "مقدمة في الحوسبة",
        "مهارات الحاسوب"
    ],
    "الفصل الدراسي الثاني": [
        "مهارة اللغة العربية 102",
        "مهارة اللغة الإنجليزية 102",
        "البرمجة وحل المسائل",
        "الرياضيات المتقطعة",
        "المنطق الرقمي وتنظيم الحاسوب",
        "مهارات عامة"
    ]
}

CATEGORIES = [
    "المحاضرات",
    "فيديو شرح",
    "التكاليف",
    "ملفات",
    "ملحقات"
]

MAIN_BUTTONS = [
    "📚 المواد الدراسية",
    "📎 الملحقات",
    "📅 الجدول الدراسي",
    "❓ طرح سؤال",
    "📨 متابعة السؤال",
    "⏰ التذكيرات",
    "👨‍💻 مطور البوت"
]

# =========================
# لوحة الأزرار الرئيسية
# =========================

def main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for button in MAIN_BUTTONS:
        keyboard.add(KeyboardButton(button))
    return keyboard

# =========================
# أدوات عرض المحتوى
# =========================

def subject_keyboard(semester):
    keyboard = InlineKeyboardMarkup(row_width=1)

    for subject in SEMESTERS[semester]:
        keyboard.add(
            InlineKeyboardButton(
                subject,
                callback_data=f"subject|{semester}|{subject}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("🔙 رجوع", callback_data="back_semesters")
    )
    return keyboard


def category_keyboard(semester, subject):
    keyboard = InlineKeyboardMarkup(row_width=1)

    for category in CATEGORIES:
        keyboard.add(
            InlineKeyboardButton(
                category,
                callback_data=f"category|{semester}|{subject}|{category}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("🔙 رجوع للمواد", callback_data="back_subjects")
    )
    return keyboard


def content_keyboard(semester, subject, category):
    keyboard = InlineKeyboardMarkup(row_width=1)

    with sqlite3.connect(DB_FILE) as conn:
        rows = conn.execute("""
            SELECT id, title
            FROM content
            WHERE semester=? AND subject=? AND category=?
            ORDER BY id DESC
        """, (semester, subject, category)).fetchall()

    for item_id, title in rows:
        keyboard.add(
            InlineKeyboardButton(
                title,
                callback_data=f"item|{item_id}"
            )
        )

    keyboard.add(
        InlineKeyboardButton(
            "🔙 رجوع للأقسام",
            callback_data=f"subject|{semester}|{subject}"
        )
    )
    return keyboard

# =========================
# بدء البوت
# =========================

@bot.message_handler(commands=["start"])
def start(message):
    text = (
        "🎓 بوت طلاب تكنولوجيا المعلومات\n"
        "جامعة إقليم سبأ\n"
        "المستوى الأول — النظام الموازي\n\n"
        "أهلًا وسهلًا بك في مكتبة الطلاب التعليمية 📚\n"
        "اختر الخدمة التي تريدها من القائمة."
    )
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_keyboard()
    )

# =========================
# التعامل مع القائمة الرئيسية
# =========================

@bot.message_handler(func=lambda message: message.text in MAIN_BUTTONS)
def main_menu(message):
    chat_id = message.chat.id
    text = message.text

    if text == "📚 المواد الدراسية":
        keyboard = InlineKeyboardMarkup(row_width=1)
        for semester in SEMESTERS:
            keyboard.add(
                InlineKeyboardButton(
                    semester,
                    callback_data=f"semester|{semester}"
                )
            )
        bot.send_message(chat_id, "اختر الفصل الدراسي:", reply_markup=keyboard)

    elif text == "📎 الملحقات":
        bot.send_message(
            chat_id,
            "📎 اختر المادة أولًا لعرض ملحقاتها من داخل أقسام المادة."
        )

    elif text == "📅 الجدول الدراسي":
        bot.send_message(chat_id, "📅 لم تتم إضافة الجدول الدراسي بعد.")

    elif text == "❓ طرح سؤال":
        msg = bot.send_message(chat_id, "اكتب سؤالك الدراسي في رسالة واحدة:")
        bot.register_next_step_handler(msg, save_question)

    elif text == "📨 متابعة السؤال":
        show_questions(message)

    elif text == "⏰ التذكيرات":
        bot.send_message(chat_id, "⏰ خدمة التذكيرات سيتم إعدادها لاحقًا.")

    elif text == "👨‍💻 مطور البوت":
        bot.send_message(
            chat_id,
            "👨‍💻 مطور البوت\n"
            "الاسم: المهندس محمد الظاهر\n"
            "رقم التواصل: 718117501\n"
            "🎓 جامعة إقليم سبأ\n"
            "قسم تكنولوجيا المعلومات (IT) — موازي"
        )

# =========================
# عرض المواد والأقسام
# =========================

@bot.callback_query_handler(func=lambda call: call.data.startswith("semester|"))
def choose_semester(call):
    semester = call.data.split("|", 1)[1]
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "📚 اختر المادة الدراسية:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=subject_keyboard(semester)
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("subject|"))
def choose_subject(call):
    parts = call.data.split("|", 2)

    if len(parts) != 3:
        bot.answer_callback_query(call.id)
        return

    semester, subject = parts[1], parts[2]

    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"📘 {subject}\n\nاختر القسم المطلوب:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=category_keyboard(semester, subject)
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("category|"))
def choose_category(call):
    parts = call.data.split("|", 3)

    if len(parts) != 4:
        bot.answer_callback_query(call.id)
        return

    semester, subject, category = parts[1], parts[2], parts[3]

    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"📚 {subject}\n📂 {category}\n\nاختر المحتوى:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=content_keyboard(semester, subject, category)
    )


@bot.callback_query_handler(func=lambda call: call.data == "back_semesters")
def back_semesters(call):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for semester in SEMESTERS:
        keyboard.add(
            InlineKeyboardButton(
                semester,
                callback_data=f"semester|{semester}"
            )
        )

    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "اختر الفصل الدراسي:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data == "back_subjects")
def back_subjects(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "اختر الفصل الدراسي أولًا من القائمة الرئيسية.",
        call.message.chat.id,
        call.message.message_id
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("item|"))
def open_item(call):
    item_id = call.data.split("|", 1)[1]

    with sqlite3.connect(DB_FILE) as conn:
        row = conn.execute("""
            SELECT title, file_id, content_type, text_content
            FROM content WHERE id=?
        """, (item_id,)).fetchone()

    bot.answer_callback_query(call.id)

    if not row:
        bot.send_message(call.message.chat.id, "المحتوى غير موجود.")
        return

    title, file_id, content_type, text_content = row
    chat_id = call.message.chat.id

    if file_id and content_type:
        if content_type == "document":
            bot.send_document(chat_id, file_id, caption=title)
        elif content_type == "video":
            bot.send_video(chat_id, file_id, caption=title)
        elif content_type == "photo":
            bot.send_photo(chat_id, file_id, caption=title)
        elif content_type == "audio":
            bot.send_audio(chat_id, file_id, caption=title)
        else:
            bot.send_message(chat_id, f"{title}\n\n{text_content or ''}")
    else:
        bot.send_message(chat_id, f"{title}\n\n{text_content or ''}")

# =========================
# الأسئلة
# =========================

def save_question(message):
    question = (message.text or "").strip()

    if not question or question.startswith("/"):
        bot.send_message(
            message.chat.id,
            "لم يتم حفظ السؤال. اضغط «❓ طرح سؤال» وحاول مرة أخرى.",
            reply_markup=main_keyboard()
        )
        return

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("""
            INSERT INTO questions (user_id, question)
            VALUES (?, ?)
        """, (message.from_user.id, question))
        question_id = cursor.lastrowid
        conn.commit()

    bot.send_message(
        message.chat.id,
        f"✅ تم تسجيل سؤالك بنجاح.\nرقم السؤال: {question_id}",
        reply_markup=main_keyboard()
    )

    if ADMIN_ID:
        try:
            bot.send_message(
                int(ADMIN_ID),
                f"❓ سؤال جديد رقم {question_id}\n"
                f"من المستخدم: {message.from_user.id}\n\n"
                f"{question}"
            )
        except Exception:
            logging.exception("تعذر إرسال السؤال للمشرف")

def show_questions(message):
    with sqlite3.connect(DB_FILE) as conn:
        rows = conn.execute("""
            SELECT id, question, answer, status
            FROM questions
            WHERE user_id=?
            ORDER BY id DESC LIMIT 10
        """, (message.from_user.id,)).fetchall()

    if not rows:
        bot.send_message(message.chat.id, "ليس لديك أسئلة مسجلة حتى الآن.")
        return

    for question_id, question, answer, status in rows:
        bot.send_message(
            message.chat.id,
            f"📨 السؤال رقم: {question_id}\n"
            f"السؤال: {question}\n"
            f"الحالة: {status}\n"
            f"الرد: {answer or 'لم تتم الإجابة بعد'}"
        )

# =========================
# إدارة المشرف
# =========================

@bot.message_handler(commands=["admin"])
def admin_help(message):
    if not ADMIN_ID or str(message.from_user.id) != str(ADMIN_ID):
        bot.reply_to(message, "⛔ هذه الخدمة للمشرف فقط.")
        return

    bot.reply_to(
        message,
        "لوحة المشرف الأساسية:\n"
        "سيتم استكمال إضافة المحتوى وإدارته في الخطوة التالية."
    )

# =========================
# تشغيل البوت
# =========================

if __name__ == "__main__":
    Thread(target=run_server, daemon=True).start()
    logging.info("Starting Saba University IT Bot")
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)