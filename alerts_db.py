# alerts_db.py

import sqlite3
from datetime import datetime

DATABASE_NAME = "rajjo_memory.db"


def create_alert_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset TEXT,
        price REAL,
        timestamp TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_alerts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset TEXT,
        level REAL,
        triggered INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS telegram_config(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_price_snapshot(asset, price):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO price_history (asset, price, timestamp) VALUES (?, ?, ?)",
        (asset, price, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_price_minutes_ago(asset, minutes):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT price, timestamp FROM price_history WHERE asset = ? ORDER BY id DESC",
        (asset,)
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None

    target_time = datetime.now().timestamp() - (minutes * 60)
    best = None
    best_diff = None
    for price, ts in rows:
        t = datetime.fromisoformat(ts).timestamp()
        diff = abs(t - target_time)
        if best_diff is None or diff < best_diff:
            best_diff = diff
            best = price

    return best


def add_price_alert(asset, level):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO price_alerts (asset, level, triggered) VALUES (?, ?, 0)",
        (asset, level)
    )
    conn.commit()
    conn.close()


def get_active_alerts():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, asset, level FROM price_alerts WHERE triggered = 0")
    rows = cursor.fetchall()
    conn.close()
    return rows


def mark_alert_triggered(alert_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE price_alerts SET triggered = 1 WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()


def save_chat_id(chat_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM telegram_config")
    cursor.execute("INSERT INTO telegram_config (chat_id) VALUES (?)", (str(chat_id),))
    conn.commit()
    conn.close()


def get_chat_id():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM telegram_config LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None