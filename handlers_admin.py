import os
from telebot import types
import database

ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
admin_add_states = {}

def register_admin_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "⚙️ لوحة الإدارة")
    def admin_panel(message):
        if message.from_user.id != ADMIN_USER_ID:
            bot.send_message(message.chat.id, "⚠️ عذراً، هذه اللوحة للمدير فقط.")
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ إضافة محتوى", callback_data="adm_add"),
            types.InlineKeyboardButton("📅 تحديث الجدول", callback_data="adm_sched"),
            types.InlineKeyboardButton("❓ إدارة الأسئلة", callback_data="adm_qst")
        )
        bot.send_message(message.chat.id, "⚙️ **لوحة التحكم الإدارية:**", reply_markup=markup, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data == "adm_add")
    def adm_add_start(call):
        if call.from_user.id != ADMIN_USER_ID: return
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM subjects ORDER BY id ASC")
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
        
        bot.send_message(message.chat.id, "✅ تم حفظ المحتوى بنجاح ودون استبدال المحتويات السابقة!")

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
            cursor.execute("INSERT INTO schedule (content_type, text_content) VALUES ('text', ?)", (message.text,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ تم تحديث الجدول الدراسي بنجاح.")

    @bot.callback_query_handler(func=lambda call: call.data == "adm_qst")
    def adm_qst_manage(call):
        if call.from_user.id != ADMIN_USER_ID: return
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM questions WHERE status = 'قيد الانتظار'")
        qs = cursor.fetchall()
        conn.close()
        
        if not qs:
            bot.send_message(call.message.chat.id, "📭 لا توجد أسئلة معلقة.")
            return
        for q in qs:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("💬 رد على السؤال", callback_data=f"qreply_{q['id']}"))
            bot.send_message(call.message.chat.id, f"❓ {q['question_text']}", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("qreply_"))
    def q_reply_prompt(call):
        if call.from_user.id != ADMIN_USER_ID: return
        q_id = call.data.split("_")[1]
        msg = bot.send_message(call.message.chat.id, "أرسل نص الرد:")
        bot.register_next_step_handler(msg, save_q_reply, q_id)

    def save_q_reply(message, q_id):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE questions SET admin_reply = ?, status = 'تم الرد' WHERE id = ?", (message.text, q_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ تم إرسال الرد وتحديث السؤال.")
