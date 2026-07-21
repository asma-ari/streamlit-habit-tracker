"""
db.py
จัดการฐานข้อมูล SQLite สำหรับแอป Habit Tracker
"""

import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).parent / "habit_tracker.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            emoji TEXT NOT NULL DEFAULT '✨',
            interval_days INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER,
            log_date TEXT NOT NULL,
            note TEXT,
            completed INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (habit_id) REFERENCES habits (id)
        )
        """
    )
    conn.commit()
    conn.close()


# ---------- Habits ----------

def add_habit(name: str, emoji: str, interval_days: int, start_date: date):
    conn = get_connection()
    conn.execute(
        "INSERT INTO habits (name, emoji, interval_days, start_date) VALUES (?, ?, ?, ?)",
        (name, emoji, interval_days, start_date.isoformat()),
    )
    conn.commit()
    conn.close()


def get_habits(active_only: bool = True):
    conn = get_connection()
    if active_only:
        rows = conn.execute("SELECT * FROM habits WHERE active = 1 ORDER BY id").fetchall()
    else:
        rows = conn.execute("SELECT * FROM habits ORDER BY id").fetchall()
    conn.close()
    return rows


def delete_habit(habit_id: int):
    conn = get_connection()
    conn.execute("UPDATE habits SET active = 0 WHERE id = ?", (habit_id,))
    conn.commit()
    conn.close()


# ---------- Logs ----------

def add_log(habit_id, log_date: date, note: str, completed: bool):
    conn = get_connection()
    conn.execute(
        "INSERT INTO logs (habit_id, log_date, note, completed) VALUES (?, ?, ?, ?)",
        (habit_id, log_date.isoformat(), note, int(completed)),
    )
    conn.commit()
    conn.close()


def get_logs_for_date(log_date: date):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM logs WHERE log_date = ? ORDER BY id DESC", (log_date.isoformat(),)
    ).fetchall()
    conn.close()
    return rows


def get_logs_for_month(year: int, month: int):
    conn = get_connection()
    month_str = f"{year:04d}-{month:02d}-%"
    rows = conn.execute(
        "SELECT * FROM logs WHERE log_date LIKE ? ORDER BY id DESC",
        (month_str,)
    ).fetchall()
    conn.close()
    return rows


def get_all_logs(limit: int = 100):
    conn = get_connection()
    rows = conn.execute(
        "SELECT logs.*, habits.name AS habit_name, habits.emoji AS habit_emoji "
        "FROM logs LEFT JOIN habits ON logs.habit_id = habits.id "
        "ORDER BY logs.log_date DESC, logs.id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return rows


def is_done_today(habit_id: int, log_date: date) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM logs WHERE habit_id = ? AND log_date = ? AND completed = 1",
        (habit_id, log_date.isoformat()),
    ).fetchone()
    conn.close()
    return row is not None


def delete_log(log_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM logs WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()

def update_habit(habit_id: int, name: str, emoji: str, interval_days: int, start_date: date):
    conn = get_connection()
    conn.execute(
        "UPDATE habits SET name = ?, emoji = ?, interval_days = ?, start_date = ? WHERE id = ?",
        (name, emoji, interval_days, start_date.isoformat(), habit_id),
    )
    conn.commit()
    conn.close()
