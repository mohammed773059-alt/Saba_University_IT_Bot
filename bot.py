import os
import telebot
from telebot import types
from dotenv import load_dotenv
import database
from flask import Flask
import threading

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

if not TOKEN:
    raise ValueError("⚠️ TELEGRAM_BOT_TOKEN مفقود في متغيرات البيئة!")

bot = telebot.TeleBot(TOKEN)
database.init_db()

# قاموس لتتبع حالات إضافة المحتوى الإداري خطوة بخطوة
admin_add_states = {}

WELCOME_MESSAGE = """
🎓 بوت طلاب تكنولوجيا المعلومات
🏛️ جامعة إقليم سبأ
💻 قسم تكنولوجيا المعلومات (IT)
📚 المستوى الأول — النظام الموازي

أهلًا وسهلًا بك في مكتبة الطلاب التعليمية.

📖 يمكنك من خلال البوت الوصول إلى المواد الدراسية والمحاضرات والفيديوهات والملفات والملحقات والتكاليف والواجبات، والاستفادة من خدمات الطلاب الأخرى.

اختر الخدمة التي تريدها من القائمة الرئيسية.

👨‍💻 مطور البوت
الاسم: المهندس/ محمد الظاهر
📱 رقم التواصل: 718117501
🎓 جامعة إقليم سبأ
💻 قسم تكنولوجيا المعلومات (IT) — النظام الموازي
"""

def main_reply_keyboard(is_admin=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📚 المواد الدراسية"),
        types.KeyboardButton("📎 الملحقات")
    )
    markup.add(
        types.KeyboardButton("📅 الجدول الدراسي"),
        types.KeyboardButton("❓ طرح سؤال")
    )
    markup.add(
        types.KeyboardButton("📨 متابعة السؤال"),
        types.KeyboardButton("⏰ التذكيرات")
    )
    markup.add(types.KeyboardButton("👨‍💻 مطور البوت"))
    if is_admin:
        markup.add(types.KeyboardButton("⚙️ لوحة الإدارة"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    is_admin = (message.from_user.id == ADMIN_USER_ID)
    bot.send_message(message.chat.id, WELCOME_MESSAGE, reply_markup=main_reply_keyboard(is_admin))

@bot.message_handler(func=lambda m: m.text == "👨‍💻 مطور البوت")
def dev_info(message):
    bot.send_message(message.chat.id, "👨‍💻 **مطور البوت:** المهندس/ محمد الظاهر\n📱 للتواصل: 718117501\n🏛️ جامعة إقليم سبأ - IT (موازي)", parse_mode="Markdown")

# --- المواد والفصول الدراسية ---
@bot.message_handler(func=lambda m: m.text == "📚 المواد الدراسية")
def choose_semester(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📘 الفصل الدراسي الأول", callback_data="sem_1"),
        types.InlineKeyboardButton("📘 الفصل الدراسي الثاني", callback_data="sem_2")
    )
    bot.send_message(message.chat.id, "📅 **اختر الفصل الدراسي:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("sem_"))
def show_subjects(call):
    semester = int(call.data.split("_")[1])
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM subjects WHERE semester = ?", (semester,))
    subjects = cursor.fetchall()
    conn.close()
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for sub in subjects:
        markup.add(types.InlineKeyboardButton(f"📖 {sub['name']}", callback_data=f"sub_{sub['id']}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع للفصول", callback_data="back_to_semesters"))
    
    sem_name = "الفصل الدراسي الأول" if semester == 1 else "الفصل الدراسي الثاني"
    bot.edit_message_text(f"📚 مواد **{sem_name}**:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_semesters")
def back_to_semesters(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📘 الفصل الدراسي الأول", callback_data="sem_1"),
        types.InlineKeyboardButton("📘 الفصل الدراسي الثاني", callback_data="sem_2")
    )
    bot.edit_message_text("📅 **اختر الفصل الدراسي:**", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
def show_subject_sections(call):
    sub_id = int(call.data.split("_")[1])
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT semester FROM subjects WHERE id = ?", (sub_id,))
    row = cursor.fetchone()
    conn.close()
    sem = row['semester'] if row else 1
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📝 المحاضرات", callback_data=f"sec_{sub_id}_lectures"),
        types.InlineKeyboardButton("🎥 فيديوهات الشرح", callback_data=f"sec_{sub_id}_videos"),
        types.InlineKeyboardButton("✍️ التكاليف والواجبات", callback_data=f"sec_{sub_id}_assignments"),
        types.InlineKeyboardButton("📂 الملفات", callback_data=f"sec_{sub_id}_files"),
        types.InlineKeyboardButton("📎 الملحقات", callback_data=f"sec_{sub_id}_attachments")
    )
    markup.add(types.InlineKeyboardButton("🔙 رجوع للمواد", callback_data=f"sem_{sem}"))
    
    bot.edit_message_text("📂 **اختر القسم المطلوب:**", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("sec_"))
def handle_sections(call):
    parts = call.data.split("_")
    sub_id = int(parts[1])
    section_type = parts[2]
    
    if section_type == "lectures":
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM lectures WHERE subject_id = ?", (sub_id,))
        lectures = cursor.fetchall()
        conn.close()
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for lec in lectures:
            markup.add(types.InlineKeyboardButton(f"📝 {lec['title']}", callback_data=f"lec_{lec['id']}"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع لأقسام المادة", callback_data=f"sub_{sub_id}"))
        bot.edit_message_text("📚 **المحاضرات المتاحة:**", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    else:
        show_general_section_contents(call.message, sub_id, section_type)

def show_general_section_contents(message, sub_id, section_type):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contents WHERE subject_id = ? AND section_type = ? AND (lecture_id IS NULL)", (sub_id, section_type))
    items = cursor.fetchall()
    conn.close()
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for item in items:
        markup.add(types.InlineKeyboardButton(f"📌 {item['title']} ({item['file_type']})", callback_data=f"item_{item['id']}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data=f"sub_{sub_id}"))
    
    bot.edit_message_text("📂 **محتويات القسم:**", message.chat.id, message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("lec_"))
def show_lecture_contents(call):
    lec_id = int(call.data.split("_")[1])
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lectures WHERE id = ?", (lec_id,))
    lecture = cursor.fetchone()
    cursor.execute("SELECT * FROM contents WHERE lecture_id = ?", (lec_id,))
    contents = cursor.fetchall()
    conn.close()
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for item in contents:
        markup.add(types.InlineKeyboardButton(f"📌 {item['title']} ({item['file_type']})", callback_data=f"item_{item['id']}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع للمحاضرات", callback_data=f"sec_{lecture['subject_id']}_lectures"))
    
    bot.edit_message_text(f"📝 **{lecture['title']}**\nاختر العنصر:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("item_"))
def send_content_item(call):
    item_id = int(call.data.split("_")[1])
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contents WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    conn.close()
    
    if not item:
        bot.answer_callback_query(call.id, "العنصر غير موجود.")
        return
        
    chat_id = call.message.chat.id
    desc = f"\n\n{item['description']}" if item['description'] else ""
    
    if item['file_type'] in ['pdf', 'document']:
        bot.send_document(chat_id, item['file_id'], caption=f"📄 {item['title']}{desc}")
    elif item['file_type'] == 'video':
        bot.send_video(chat_id, item['file_id'], caption=f"🎥 {item['title']}{desc}")
    elif item['file_type'] == 'image':
        bot.send_photo(chat_id, item['file_id'], caption=f"🖼️ {item['title']}{desc}")
    elif item['file_type'] == 'link':
        bot.send_message(chat_id, f"🔗 **{item['title']}**\n{item['file_id']}{desc}", parse_mode="Markdown")
    elif item['file_type'] == 'text':
        bot.send_message(chat_id, f"📝 **{item['title']}**\n\n{item['file_id']}{desc}", parse_mode="Markdown")

# --- الملحقات المشتركة ---
@bot.message_handler(func=lambda m: m.text == "📎 الملحقات")
def global_attachments_menu(message):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contents WHERE section_type = 'attachments'")
    attachments = cursor.fetchall()
    conn.close()
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for att in attachments:
        markup.add(types.InlineKeyboardButton(f"📎 {att['title']}", callback_data=f"item_{att['id']}"))
        
    if not attachments:
        bot.send_message(message.chat.id, "📎 لا توجد ملحقات عامة مضافة حالياً.")
    else:
        bot.send_message(message.chat.id, "📎 **قائمة الملحقات العامة:**", reply_markup=markup, parse_mode="Markdown")

# --- الخدمات الطلابية الأخرى ---
@bot.message_handler(func=lambda m: m.text == "📅 الجدول الدراسي")
def show_schedule(message):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schedule LIMIT 1")
    sched = cursor.fetchone()
    conn.close()
    
    if not sched:
        bot.send_message(message.chat.id, "📅 الجدول الدراسي غير مضاف حالياً من الإدارة.")
        return
    if sched['content_type'] == 'photo':
        bot.send_photo(message.chat.id, sched['file_id'], caption="📅 الجدول الدراسي المعتمد")
    elif sched['content_type'] == 'document':
        bot.send_document(message.chat.id, sched['file_id'], caption="📅 الجدول الدراسي المعتمد")
    else:
        bot.send_message(message.chat.id, f"📅 **الجدول الدراسي:**\n\n{sched['text_content']}", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "❓ طرح سؤال")
def ask_question(message):
    msg = bot.send_message(message.chat.id, "❓ أرسل سؤالك الآن ليرسله البوت إلى الإدارة:")
    bot.register_next_step_handler(msg, save_question)

def save_question(message):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO questions (user_id, question_text) VALUES (?, ?)", (message.from_user.id, message.text))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ تم إرسال سؤالك بنجاح للإدارة.")

@bot.message_handler(func=lambda m: m.text == "📨 متابعة السؤال")
def follow_questions(message):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE user_id = ?", (message.from_user.id,))
    questions = cursor.fetchall()
    conn.close()
    
    if not questions:
        bot.send_message(message.chat.id, "📭 ليس لديك أي أسئلة مسجلة.")
        return
    text = "📨 **حالة أسئلتك:**\n\n"
    for q in questions:
        rep = f"الرد: {q['admin_reply']}" if q['admin_reply'] else "قيد الانتظار"
        text += f"🔹 السؤال: {q['question_text']}\n📌 الحالة: {q['status']}\n💬 {rep}\n------------------\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "⏰ التذكيرات")
def reminders_main(message):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reminders WHERE user_id = ?", (message.from_user.id,))
    rems = cursor.fetchall()
    conn.close()
    
    text = "⏰ **تذكيراتك الشخصية:**\n\n"
    for r in rems:
        text += f"📌 {r['title']} ({r['reminder_time']})\n"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ إضافة تذكير", callback_data="add_rem"))
    bot.send_message(message.chat.id, text if rems else "⏰ ليس لديك تذكيرات نشطة.", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "add_rem")
def add_rem_prompt(call):
    msg = bot.send_message(call.message.chat.id, "أرسل عنوان التذكير مع الوقت:")
    bot.register_next_step_handler(msg, save_rem)

def save_rem(message):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO reminders (user_id, title, reminder_time) VALUES (?, ?, ?)", 
                   (message.from_user.id, message.text, "قريباً"))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ تم حفظ التذكير.")

# --- لوحة الإدارة الآمنة بالكامل ---
@bot.message_handler(func=lambda m: m.text == "⚙️ لوحة الإدارة")
def admin_panel(message):
    if message.from_user.id != ADMIN_USER_ID:
        bot.send_message(message.chat.id, "⚠️ عذراً، هذه اللوحة للمدير فقط.")
        return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ إضافة محتوى", callback_data="adm_add"),
        types.InlineKeyboardButton("🗑️ حذف محتوى/مادة", callback_data="adm_del"),
        types.InlineKeyboardButton("📅 تحديث الجدول", callback_data="adm_sched"),
        types.InlineKeyboardButton("❓ إدارة الأسئلة", callback_data="adm_qst")
    )
    bot.send_message(message.chat.id, "⚙️ **لوحة التحكم الإدارية:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "adm_add")
def adm_add_start(call):
    if call.from_user.id != ADMIN_USER_ID: return
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM subjects")
    subs = cursor.fetchall()
    conn.close()
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for s in subs:
        markup.add(types.InlineKeyboardButton(s['name'], callback_data=f"astart_sub_{s['id']}"))
    bot.edit_message_text("اختر المادة لإضافة المحتوى:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("astart_sub_"))
def adm_select_section(call):
    sub_id = int(call.data.split("_")[2])
    admin_add_states[call.from_user.id] = {"sub_id": sub_id}
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📝 المحاضرات", callback_data="asec_lectures"),
        types.InlineKeyboardButton("🎥 فيديوهات الشرح", callback_data="asec_videos"),
        types.InlineKeyboardButton("✍️ التكاليف", callback_data="asec_assignments"),
        types.InlineKeyboardButton("📂 الملفات", callback_data="asec_files"),
        types.InlineKeyboardButton("📎 الملحقات", callback_data="asec_attachments")
    )
    bot.edit_message_text("اختر القسم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("asec_"))
def adm_select_sec_type(call):
    sec_type = call.data.split("_")[1]
    uid = call.from_user.id
    admin_add_states[uid]["section_type"] = sec_type
    
    if sec_type == "lectures":
        # عرض المحاضرات الحالية أو إنشاء جديدة
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM lectures WHERE subject_id = ?", (admin_add_states[uid]["sub_id"],))
        lecs = cursor.fetchall()
        conn.close()
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("➕ إنشاء محاضرة جديدة", callback_data="anew_lec"))
        for l in lecs:
            markup.add(types.InlineKeyboardButton(l['title'], callback_data=f"alec_{l['id']}"))
        bot.edit_message_text("اختر المحاضرة أو أنشئ محاضرة جديدة:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    else:
        msg = bot.send_message(call.message.chat.id, "أرسل عنوان المحتوى الجديد:")
        bot.register_next_step_handler(msg, adm_get_content_title)

@bot.callback_query_handler(func=lambda call: call.data == "anew_lec")
def new_lecture_prompt(call):
    msg = bot.send_message(call.message.chat.id, "أرسل اسم المحاضرة الجديدة (مثال: المحاضرة الأولى):")
    bot.register_next_step_handler(msg, save_new_lecture)

def save_new_lecture(message):
    uid = message.from_user.id
    sub_id = admin_add_states[uid]["sub_id"]
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO lectures (subject_id, title) VALUES (?, ?)", (sub_id, message.text))
    conn.commit()
    lec_id = cursor.lastrowid
    conn.close()
    
    admin_add_states[uid]["lecture_id"] = lec_id
    msg = bot.send_message(message.chat.id, "✅ تم إنشاء المحاضرة. الآن أرسل عنوان الملف/المحتوى:")
    bot.register_next_step_handler(msg, adm_get_content_title)

@bot.callback_query_handler(func=lambda call: call.data.startswith("alec_"))
def select_existing_lecture(call):
    lec_id = int(call.data.split("_")[1])
    uid = call.from_user.id
    admin_add_states[uid]["lecture_id"] = lec_id
    msg = bot.send_message(call.message.chat.id, "أرسل عنوان الملف أو العنصر الجديد للمحاضرة:")
    bot.register_next_step_handler(msg, adm_get_content_title)

def adm_get_content_title(message):
    uid = message.from_user.id
    admin_add_states[uid]["title"] = message.text
    msg = bot.send_message(message.chat.id, "الآن أرسل الملف (PDF، فيديو، صورة، مستند) أو الرابط/النص المطلوب حفظه:")
    bot.register_next_step_handler(msg, adm_save_final_content)

def adm_save_final_content(message):
    uid = message.from_user.id
    state = admin_add_states.get(uid, {})
    
    file_type = "text"
    file_id = message.text
    
    if message.document:
        file_type = "pdf" if message.document.mime_type == "application/pdf" else "document"
        file_id = message.document.file_id
    elif message.video:
        file_type = "video"
        file_id = message.video.file_id
    elif message.photo:
        file_type = "image"
        file_id = message.photo[-1].file_id
    elif message.text and message.text.startswith("http"):
        file_type = "link"
        file_id = message.text
        
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO contents (subject_id, lecture_id, section_type, title, file_type, file_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        state.get("sub_id"),
        state.get("lecture_id"),
        state.get("section_type", "files"),
        state.get("title", "ملف تعليمي"),
        file_type,
        file_id
    ))
    conn.commit()
    conn.close()
    
    bot.send_message(message.chat.id, "✅ تم حفظ المحتوى بنجاح دون استبدال المحتويات السابقة!")

@bot.callback_query_handler(func=lambda call: call.data == "adm_sched")
def adm_sched_prompt(call):
    if call.from_user.id != ADMIN_USER_ID: return
    msg = bot.send_message(call.message.chat.id, "أرسل صورة الجدول الدراسي أو ملفه الجديد:")
    bot.register_next_step_handler(msg, save_schedule_admin)

def save_schedule_admin(message):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedule")
    if message.photo:
        cursor.execute("INSERT INTO schedule (content_type, file_id) VALUES ('photo', ?)", (message.photo[-1].file_id,))
    elif message.document:
        cursor.execute("INSERT INTO schedule (content_type, file_id) VALUES ('document', ?)", (message.document.file_id,))
    else:
        cursor.execute("INSERT INTO schedule (content_type, text_content)