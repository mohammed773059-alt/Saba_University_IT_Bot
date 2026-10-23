from telebot import types

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

def semesters_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📘 الفصل الدراسي الأول", callback_data="sem_1"),
        types.InlineKeyboardButton("📘 الفصل الدراسي الثاني", callback_data="sem_2")
    )
    return markup

def subject_sections_keyboard(sub_id, sem):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📝 المحاضرات", callback_data=f"sec_{sub_id}_lectures"),
        types.InlineKeyboardButton("🎥 فيديوهات الشرح", callback_data=f"sec_{sub_id}_videos"),
        types.InlineKeyboardButton("✍️ التكاليف والواجبات", callback_data=f"sec_{sub_id}_assignments"),
        types.InlineKeyboardButton("📂 الملفات", callback_data=f"sec_{sub_id}_files"),
        types.InlineKeyboardButton("📎 الملحقات", callback_data=f"sec_{sub_id}_attachments")
    )
    markup.add(types.InlineKeyboardButton("🔙 رجوع للمواد", callback_data=f"sem_{sem}"))
    return markup
