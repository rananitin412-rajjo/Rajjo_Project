# notes.py

import sqlite3
from datetime import datetime

DATABASE_NAME = "rajjo_memory.db"


def create_notes_table():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT,
        date_added TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_note(content):
    if len(content) > 2000:
        content = content[:2000] + "... (baaki text truncate ho gaya, bahut lamba tha)"

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO notes (content, date_added) VALUES (?, ?)",
        (content, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )

    conn.commit()
    conn.close()


def get_all_notes():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT content, date_added FROM notes ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    return rows


def format_notes_snapshot():
    notes = get_all_notes()

    if not notes:
        return ""

    text = "PERMANENTLY SAVED NOTES (Rana ne explicitly yaad rakhne bola tha):\n"

    for content, date in notes:
        text += f"- [{date}] {content}\n"

    return text