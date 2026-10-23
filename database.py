import sqlite3

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
            semester INTEGER NOT NULL
        )
    ''')
    
    # جدول المحاضرات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lectures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            title TEXT NOT NULL,
            FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
        )
    ''')
    
    # جدول محتويات المادة أو المحاضرة أو الملحقات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            lecture_id INTEGER,
            section_type TEXT NOT NULL,
            title TEXT NOT NULL,
            file_type TEXT,
            file_id TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE,
            FOREIGN KEY (lecture_id) REFERENCES lectures (id) ON DELETE CASCADE
        )
    ''')
    
    # جدول الأسئلة
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            admin_reply TEXT,
            status TEXT DEFAULT 'قيد الانتظار',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول التذكيرات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            reminder_time TEXT NOT NULL,
            status TEXT DEFAULT 'نشط'
        )
    ''')
    
    # جدول الجدول الدراسي
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT NOT NULL,
            file_id TEXT,
            text_content TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    seed_default_subjects()

def seed_default_subjects():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM subjects")
    if cursor.fetchone()[0] == 0:
        sem1 = ["مهارة اللغة العربية 101", "مهارة اللغة الإنجليزية 101", "التفاضل والتكامل", "فيزياء عامة للحوسبة", "مقدمة في الحوسبة", "مهارات الحاسوب"]
        for s in sem1:
            cursor.execute("INSERT INTO subjects (name, semester) VALUES (?, 1)", (s,))
            
        sem2 = ["مهارة اللغة العربية 102", "مهارة اللغة الإنجليزية 102", "البرمجة وحل المسائل", "الرياضيات المتقطعة", "المنطق الرقمي وتنظيم الحاسوب", "مهارات عامة"]
        for s in sem2:
            cursor.execute("INSERT INTO subjects (name, semester) VALUES (?, 2)", (s,))
        conn.commit()
    conn.close()