import os
from telebot import types
import database
import keyboards

ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

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

def register_student_handlers(bot):

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        is_admin = (message.from_user.id == ADMIN_USER_ID)
        bot.send_message(message.chat.id, WELCOME_MESSAGE, reply_markup=keyboards.main_reply_keyboard(is_admin))

    @bot.message_handler(func=lambda m: m.text == "👨‍💻 مطور البوت")
    def dev_info(message):
        bot.send_message(message.chat.id, "👨‍💻 **مطور البوت:** المهندس/ محمد الظاهر\n📱 للتواصل: 718117501\n🏛️ جامعة إقليم سبأ - IT (موازي)", parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text == "📚 المواد الدراسية")
    def choose_semester(message):
        bot.send_message(message.chat.id, "📅 **اختر الفصل الدراسي:**", reply_markup=keyboards.semesters_keyboard(), parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("sem_"))
    def show_subjects(call):
        semester = int(call.data.split("_")[1])
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM subjects WHERE semester = ? ORDER BY id ASC", (semester,))
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
        bot.edit_message_text("📅 **اختر الفصل الدراسي:**", call.message.chat.id, call.message.message_id, reply_markup=keyboards.semesters_keyboard(), parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
    def show_subject_sections(call):
        sub_id = int(call.data.split("_")[1])
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT semester FROM subjects WHERE id = ?", (sub_id,))
        row = cursor.fetchone()
        conn.close()
        sem = row['semester'] if row else 1
        
        bot.edit_message_text("📂 **اختر القسم المطلوب للمادة:**", call.message.chat.id, call.message.message_id, reply_markup=keyboards.subject_sections_keyboard(sub_id, sem), parse_mode="Markdown")

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
            
            if not lectures:
                bot.answer_callback_query(call.id, "لا توجد محاضرات مضافة لهذه المادة بعد.", show_alert=True)
                return
                
            bot.edit_message_text("📚 **المحاضرات المتاحة:**", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contents WHERE subject_id = ? AND section_type = ? AND (lecture_id IS NULL)", (sub_id, section_type))
            items = cursor.fetchall()
            conn.close()
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            for item in items:
                markup.add(types.InlineKeyboardButton(f"📌 {item['title']} ({item['file_type']})", callback_data=f"item_{item['id']}"))
            markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data=f"sub_{sub_id}"))
            
            if not items:
                bot.answer_callback_query(call.id, "لا توجد عناصر مضافة في هذا القسم حالياً.", show_alert=True)
                return
                
            bot.edit_message_text("📂 **محتويات القسم:**", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

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
        
        sub_id = lecture['subject_id'] if lecture else 0
        markup.add(types.InlineKeyboardButton("🔙 رجوع للمحاضرات", callback_data=f"sec_{sub_id}_lectures"))
        
        if not contents:
            bot.answer_callback_query(call.id, "لا توجد ملفات مرفقة لهذه المحاضرة بعد.", show_alert=True)
            return
            
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
