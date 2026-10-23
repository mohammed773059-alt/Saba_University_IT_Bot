import sqlite3
import datetime

DB_NAME = "library.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # جدول المواد الدراسية
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            semester INTEGER NOT NULL -- 1 للفصل الأول، 2 للفصل الثاني
        )
    ''')
    
    # جدول المحاضرات التابعة للمواد
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lectures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            title TEXT NOT NULL,
            FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
        )
    ''')
    
    # جدول محتويات المواد والمحاضرات والأقسام (ملفات، فيديوهات، روابط، إلخ)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            lecture_id INTEGER,
            section_type TEXT NOT NULL, -- lectures, videos, assignments, files, attachments
            title TEXT NOT NULL,
            file_type TEXT, -- pdf, video, image, text, link, document
            file_id TEXT,   -- Telegram file_id or external link/text
            description TEXT,
            is_global_attachment INTEGER DEFAULT 0, -- للملحقات العامة المشتركة
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE,
            FOREIGN KEY (lecture_id) REFERENCES lectures (id) ON DELETE CASCADE
        )
    ''')
    
    # جدول الأسئلة الطلابية
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject_id INTEGER,
            question_text TEXT NOT NULL,
            admin_reply TEXT,
            status TEXT DEFAULT 'قيد الانتظار',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE SET NULL
        )
    ''')
    
    # جدول التذكيرات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            reminder_time TEXT NOT NULL,
            status TEXT DEFAULT 'نشط'
        )
    ''')
    
    # جدول الجدول الدراسي
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT NOT NULL, -- photo, document, text
            file_id TEXT,
            text_content TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # إدراج المواد الأساسية افتراضياً إذا كانت قاعدة البيانات فارغة
    seed_default_subjects()

def seed_default_subjects():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM subjects")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # الفصل الأول
        sem1_subjects = [
            "مهارة اللغة العربية 101",
            "مهارة اللغة الإنجليزية 101",
            "التفاضل والتكامل",
            "فيزياء عامة للحوسبة",
            "مقدمة في الحوسبة",
            "مهارات الحاسوب"
        ]
        for sub in sem1_subjects:
            cursor.execute("INSERT INTO subjects (name, semester) VALUES (?, 1)", (sub,))
            
        # الفصل الثاني
        sem2_subjects = [
            "مهارة اللغة العربية 102",
            "مهارة اللغة الإنجليزية 102",
            "البرمجة وحل المسائل",
            "الرياضيات المتقطعة",
            "المنطق الرقمي وتنظيم الحاسوب",
            "مهارات عامة"
        ]
        for sub in sem2_subjects:
            cursor.execute("INSERT INTO subjects (name, semester) VALUES (?, 2)", (sub,))
            
        conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
