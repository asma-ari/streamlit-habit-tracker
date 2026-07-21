"""
db.py
จัดการฐานข้อมูล SQLite สำหรับ Daily Habit Tracker (รองรับ Multi-user)
"""

import sqlite3
import hashlib
from datetime import date

DB_NAME = "habit_tracker.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    """เข้ารหัสรหัสผ่านด้วย SHA-256 เพื่อความปลอดภัย"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # ตารางเก็บข้อมูลผู้ใช้
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        
        # ตารางเก็บกิจกรรม (ผูกกับ user_id)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                emoji TEXT DEFAULT '✨',
                interval_days INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                weekdays TEXT DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # ตารางเก็บประวัติบันทึก/เช็คลิสต์ (ผูกกับ user_id)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                habit_id INTEGER,
                log_date TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                note TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (habit_id) REFERENCES habits (id) ON DELETE CASCADE
            )
        """)
        conn.commit()

# --- ระบบจัดการ User ---
def register_user(username, password):
    hashed = hash_password(password)
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
            conn.commit()
            return True, "สมัครสมาชิกสำเร็จ!"
    except sqlite3.IntegrityError:
        return False, "ชื่อผู้ใช้นี้ถูกใช้งานแล้ว กรุณาลองชื่ออื่น"

def login_user(username, password):
    hashed = hash_password(password)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users WHERE username = ? AND password = ?", (username, hashed))
        user = cursor.fetchone()
        if user:
            return dict(user)
        return None

# --- ระบบจัดการ Habits ---
def get_habits(user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM habits WHERE user_id = ? ORDER BY id DESC", (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def add_habit(user_id, name, emoji, interval_days, start_date, weekdays=""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO habits (user_id, name, emoji, interval_days, start_date, weekdays) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, name, emoji, interval_days, start_date.isoformat(), weekdays),
        )
        conn.commit()

def update_habit(habit_id, user_id, name, emoji, interval_days, start_date, weekdays=""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE habits SET name=?, emoji=?, interval_days=?, start_date=?, weekdays=? WHERE id=? AND user_id=?",
            (name, emoji, interval_days, start_date.isoformat(), weekdays, habit_id, user_id),
        )
        conn.commit()

def delete_habit(habit_id, user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM habits WHERE id = ? AND user_id = ?", (habit_id, user_id))
        cursor.execute("DELETE FROM habit_logs WHERE habit_id = ? AND user_id = ?", (habit_id, user_id))
        conn.commit()

# --- ระบบจัดการ Logs/Diary ---
def is_done_today(habit_id, user_id, log_date):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM habit_logs WHERE habit_id = ? AND user_id = ? AND log_date = ? AND completed = 1",
            (habit_id, user_id, log_date.isoformat()),
        )
        return cursor.fetchone()[0] > 0

def add_log(user_id, habit_id, log_date, note=None, completed=False):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO habit_logs (user_id, habit_id, log_date, completed, note) VALUES (?, ?, ?, ?, ?)",
            (user_id, habit_id, log_date.isoformat(), 1 if completed else 0, note),
        )
        conn.commit()

def get_all_logs(user_id, limit=500):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.id, l.log_date, l.completed, l.note, h.name as habit_name, h.emoji as habit_emoji
            FROM habit_logs l
            LEFT JOIN habits h ON l.habit_id = h.id
            WHERE l.user_id = ?
            ORDER BY l.log_date DESC, l.id DESC
            LIMIT ?
        """, (user_id, limit))
        return [dict(row) for row in cursor.fetchall()]

def get_logs_for_date(user_id, log_date):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM habit_logs WHERE user_id = ? AND log_date = ? ORDER BY id DESC",
            (user_id, log_date.isoformat())
        )
        return [dict(row) for row in cursor.fetchall()]

def delete_log(log_id, user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM habit_logs WHERE id = ? AND user_id = ?", (log_id, user_id))
        conn.commit()
