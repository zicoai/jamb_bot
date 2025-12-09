import sqlite3
import os

DB_PATH = "bot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_progress
                 (user_id INTEGER PRIMARY KEY, asked_questions TEXT, correct INTEGER, total INTEGER)''')
    conn.commit()
    conn.close()

def get_progress(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT asked_questions, correct, total FROM user_progress WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"asked": set(row[0].split(",") if row[0] else []), "correct": row[1], "total": row[2]}
    return {"asked": set(), "correct": 0, "total": 0}

def update_progress(user_id, asked_set, correct, total):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    asked_str = ",".join(map(str, asked_set))
    c.execute("INSERT OR REPLACE INTO user_progress VALUES (?, ?, ?, ?)",
              (user_id, asked_str, correct, total))
    conn.commit()
    conn.close()