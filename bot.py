import os
import telebot
from telebot import types
from dotenv import load_dotenv
import database

# تحميل متغيرات البيئة
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

if not TOKEN:
    raise ValueError("⚠️ يرجى التأكد من تعيين متغير البيئة TELEGRAM_BOT_TOKEN في ملف .env")

bot = telebot.TeleBot(TOKEN)

# تهيئة قاعدة البيانات عند بدء التشغيل
database.init_db()

# حالات المديرين المؤقتة لإضافة المحتوى خطوة بخطوة
admin_states = {}

# رسالة الترحيب
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
    bot.send_message(
        message.chat.id,
        WELCOME_MESSAGE,
        reply_markup=main_reply_keyboard(is_admin)
    )

@bot.message_handler(func=lambda message: message.text == "👨‍💻 مطور البوت")
def developer_info(message):
    dev_text = (
        "👨‍💻 **مطور البوت**\n"
        "الاسم: المهندس/ محمد الظاهر\n"
        "رقم التواصل: 718117501\n"
        "الجامعة: جامعة إقليم سبأ\n"
        "القسم: تكنولوجيا المعلومات (IT) — المستوى الأول (النظام الموازي)"
    )
    bot.send_message(message.chat.id, dev_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📚 المواد الدراسية")
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
    bot.edit_message_text(
        f"📚 مواد **{sem_name}**:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
def show_subject_sections(call):
    sub_id = int(call.data.split("_")[1])
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📝 المحاضرات", callback_data=f"sec_{sub_id}_lectures"),
        types.InlineKeyboardButton("🎥 فيديوهات الشرح", callback_data=f"sec_{sub_id}_videos"),
        types.InlineKeyboardButton("✍️ التكاليف والواجبات", callback_data=f"sec_{sub_id}_assignments"),
        types.InlineKeyboardButton("📂 الملفات", callback_data=f"sec_{sub_id}_files"),
        types.InlineKeyboardButton("📎 الملحقات", callback_data=f"sec_{sub_id}_attachments")
    )
    # استرجاع اسم المادة للرجوع الصحيح
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT semester FROM subjects WHERE id = ?", (sub_id,))
    row = cursor.fetchone()
    conn.close()
    sem = row['semester'] if row else 1
    
    markup.add(types.InlineKeyboardButton("🔙 رجوع للمواد", callback_data=f"sem_{sem}"))
    
    bot.edit_message_text(
        "📂 **اختر القسم المطلوب للمادة:**",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

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
        # عرض محتويات الأقسام الأخرى (فيديوهات، ملفات، تكاليف، ملحقات خاصة بالمادة)
        show_content_list(call.message, sub_id, None, section_type)

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
    
    bot.edit_message_text(
        f"📝 **{lecture['title']}**\nاختر العنصر لعرضه:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

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
    
    if item['file_type'] == 'pdf' or item['file_type'] == 'document':
        bot.send_document(chat_id, item['file_id'], caption=f"📄 {item['title']}{desc}")
    elif item['file_type'] == 'video':
        bot.send_video(chat_id, item['file_id'], caption=f"🎥 {item['title']}{desc}")
    elif item['file_type'] == 'image':
        bot.send_photo(chat_id, item['file_id'], caption=f"🖼️ {item['title']}{desc}")
    elif item['file_type'] == 'link':
        bot.send_message(chat_id, f"🔗 **{item['title']}**\n{item['file_id']}{desc}", parse_mode="Markdown")
    elif item['file_type'] == 'text':
        bot.send_message(chat_id, f"📝 **{item['title']}**\n\n{item['file_id']}{desc}", parse_mode="Markdown")

def show_content_list(message, sub_id, lec_id, section_type):
    conn = database.get_connection()
    cursor = conn.cursor()
    if lec_id:
        cursor.execute("SELECT * FROM contents WHERE lecture_id = ? AND section_type = ?", (lec_id, section_type))
    else:
        cursor.execute("SELECT * FROM contents WHERE subject_id = ? AND section_type = ? AND (lecture_id IS NULL OR lecture_id = '')", (sub_id, section_type))
    items = cursor.fetchall()
    conn.close()
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for item in items:
        markup.add(types.InlineKeyboardButton(f"📌 {item['title']}", callback_data=f"item_{item['id']}"))
        
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data=f"sub_{sub_id}"))
    
    bot.edit_message_text(
        f"📂 محتويات القسم:",
        message.chat.id,
        message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# نظام الملحقات العامة والخاصة
@bot.message_handler(func=lambda message: message.text == "📎 الملحقات")
def global_attachments(message):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contents WHERE section_type = 'attachments'")
    attachments = cursor.fetchall()
    conn.close()
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for att in attachments:
        markup.add(types.InlineKeyboardButton(f"📎 {att['title']}", callback_data=f"item_{att['id']}"))
        
    if not attachments:
        bot.send_message(message.chat.id, "لا توجد ملحقات مضافة حالياً.")
    else:
        bot.send_message(message.chat.id, "📎 **قائمة الملحقات المتاحة:**", reply_markup=markup, parse_mode="Markdown")

# زر الجدول الدراسي
@bot.message_handler(func=lambda message: message.text == "📅 الجدول الدراسي")
def show_schedule(message):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schedule LIMIT 1")
    sched = cursor.fetchone()
    conn.close()
    
    if not sched:
        bot.send_message(message.chat.id, "📅 عذراً، الجدول الدراسي غير مضاف حالياً من قبل الإدارة.")
        return
        
    if sched['content_type'] == 'photo':
        bot.send_photo(message.chat.id, sched['file_id'], caption="📅 الجدول الدراسي المعتمد")
    elif sched['content_type'] == 'document':
        bot.send_document(message.chat.id, sched['file_id'], caption="📅 الجدول الدراسي المعتمد")
    else:
        bot.send_message(message.chat.id, f"📅 **الجدول الدراسي:**\n\n{sched['text_content']}", parse_mode="Markdown")

# خدمة طرح سؤال
@bot.message_handler(func=lambda message: message.text == "❓ طرح سؤال")
def ask_question_start(message):
    msg = bot.send_message(message.chat.id, "❓ أرسل سؤالك الآن وسيتم تحويله إلى إدارة البوت:")
    bot.register_next_step_handler(msg, save_student_question)

def save_student_question(message):
    user_id = message.from_user.id
    q_text = message.text
    
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO questions (user_id, question_text) VALUES (?, ?)", (user_id, q_text))
    conn.commit()
    conn.close()
    
    bot.send_message(message.chat.id, "✅ تم إرسال سؤالك بنجاح. يمكنك متابعة حالة الرد من زر '📨 متابعة السؤال'.")

@bot.message_handler(func=lambda message: message.text == "📨 متابعة السؤال")
def follow_up_questions(message):
    user_id = message.from_user.id
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE user_id = ?", (user_id,))
    questions = cursor.fetchall()
    conn.close()
    
    if not questions:
        bot.send_message(message.chat.id, "📭 ليس لديك أي أسئلة مرسلة.")
        return
        
    text = "📨 **أسئلتك وحالاتها:**\n\n"
    for q in questions:
        reply_status = f"رد الإدارة: {q['admin_reply']}" if q['admin_reply'] else "لم يتم الرد بعد"
        text += f"🔹 السؤال: {q['question_text']}\n📌 الحالة: {q['status']}\n💬 {reply_status}\n------------------\n"
        
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# خدمة التذكيرات
@bot.message_handler(func=lambda message: message.text == "⏰ التذكيرات")
def reminders_menu(message):
    user_id = message.from_user.id
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reminders WHERE user_id = ?", (user_id,))
    rems = cursor.fetchall()
    conn.close()
    
    text = "⏰ **تذكيراتك الشخصية:**\n\n"
    for r in rems:
        text += f"📌 {r['title']} - {r['reminder_time']}\n"
        
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ إضافة تذكير جديد", callback_data="add_reminder"))
    
    bot.send_message(message.chat.id, text if rems else "⏰ ليس لديك أي تذكيرات نشطة.", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "add_reminder")
def prompt_reminder(call):
    msg = bot.send_message(call.message.chat.id, "أرسل عنوان التذكير مع الوقت (مثال: تسليم الواجب غداً الساعة 10):")
    bot.register_next_step_handler(msg, save_reminder_step)

def save_reminder_step(message):
    user_id = message.from_user.id
    text = message.text
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO reminders (user_id, title, reminder_time) VALUES (?, ?, ?)", (user_id, text, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ تم حفظ التذكير بنجاح.")

# لوحة الإدارة الآمنة
@bot.message_handler(func=lambda message: message.text == "⚙️ لوحة الإدارة")
def admin_panel(message):
    if message.from_user.id != ADMIN_USER_ID:
        bot.send_message(message.chat.id, "⚠️ عذراً، هذه اللوحة مخصصة للمدير فقط.")
        return
        
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ إضافة محتوى", callback_data="adm_add_content"),
        types.InlineKeyboardButton("📚 إضافة مادة دراسية", callback_data="adm_add_subject"),
        types.InlineKeyboardButton("📅 تحديث الجدول الدراسي", callback_data="adm_update_schedule"),
        types.InlineKeyboardButton("❓ إدارة الأسئلة", callback_data="adm_manage_questions")
    )
    bot.send_message(message.chat.id, "⚙️ **لوحة التحكم الخاصة بالمدير:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "adm_add_subject")
def adm_add_subject_prompt(call):
    if call.from_user.id != ADMIN_USER_ID:
        return
    msg = bot.send_message(call.message.chat.id, "أرسل اسم المادة ورقم الفصل متبوعين بشرطة سفلية (مثال: `برمجة متقدمة_2`):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, adm_save_subject)

def adm_save_subject(message):
    try:
        parts = message.text.split("_")
        name = parts[0]
        sem = int(parts[1])
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO subjects (name, semester) VALUES (?, ?)", (name, sem))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ تم إضافة المادة ({name}) للفصل الدراسي ({sem}) بنجاح.")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ حدث خطأ في الصيغة. يرجى المحاولة مرة أخرى بالشكل الصحيح.")

@bot.callback_query_handler(func=lambda call: call.data == "adm_update_schedule")
def adm_update_schedule_prompt(call):
    if call.from_user.id != ADMIN_USER_ID:
        return
    msg = bot.send_message(call.message.chat.id, "أرسل صورة الجدول الدراسي أو ملفه الآن:")
    bot.register_next_step_handler(msg, adm_save_schedule)

def adm_save_schedule(message):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedule")
    
    if message.photo:
        file_id = message.photo[-1].file_id
        cursor.execute("INSERT INTO schedule (content_type, file_id) VALUES ('photo', ?)", (file_id,))
    elif message.document:
        file_id = message.document.file_id
        cursor.execute("INSERT INTO schedule (content_type, file_id) VALUES ('document', ?)", (file_id,))
    else:
        text = message.text
        cursor.execute("INSERT INTO schedule (content_type, text_content) VALUES ('text', ?)", (text,))
        
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ تم تحديث الجدول الدراسي بنجاح.")

@bot.callback_query_handler(func=lambda call: call.data == "adm_manage_questions")
def adm_manage_questions(call):
    if call.from_user.id != ADMIN_USER_ID:
        return
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE status = 'قيد الانتظار'")
    questions = cursor.fetchall()
    conn.close()
    
    if not questions:
        bot.send_message(call.message.chat.id, "📭 لا توجد أسئلة معلقة.")
        return
        
    for q in questions:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💬 الرد على السؤال", callback_data=f"reply_q_{q['id']}"))
        bot.send_message(call.message.chat.id, f"❓ سؤال (ID: {q['id']}):\n{q['question_text']}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_q_"))
def reply_to_question_prompt(call):
    if call.from_user.id != ADMIN_USER_ID:
        return
    q_id = call.data.split("_")[2]
    msg = bot.send_message(call.message.chat.id, "أرسل نص الإجابة على هذا السؤال:")
    bot.register_next_step_handler(msg, save_admin_reply, q_id)

def save_admin_reply(message, q_id):
    reply_text = message.text
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE questions SET admin_reply = ?, status = 'تم الرد' WHERE id = ?", (reply_text, q_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ تم إرسال الرد بنجاح وتحديث حالة السؤال.")

if __name__ == "__main__":
    print("🤖 البوت يعمل الآن بنجاح...")
    bot.infinity_polling()
