# memory.py

import sqlite3

DATABASE_NAME = "rajjo_memory.db"


def create_database():
    """Create the memory database if it doesn't exist."""

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        key TEXT UNIQUE,
        value TEXT
    )
""")

    conn.commit()
    conn.close()


def save_memory(category, key, value):

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO memory(category, key, value)
        VALUES (?, ?, ?)
        """,
        (category, key, value)
    )

    conn.commit()
    conn.close()


def load_memory(key):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT value FROM memory
        WHERE key = ?
        """,
        (key,)
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]

    return None


def get_all_memories():

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category, key, value
        FROM memory
    """)

    result = cursor.fetchall()
    conn.close()

    return result