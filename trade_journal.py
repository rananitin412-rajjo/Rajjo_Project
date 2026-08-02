# trade_journal.py

import sqlite3
from datetime import datetime

DATABASE_NAME = "rajjo_memory.db"


def create_journal_table():
    """Trade journal table banata hai agar exist nahi karti."""

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset TEXT,
        direction TEXT,
        entry_price REAL,
        stop_loss REAL,
        target REAL,
        reasoning TEXT,
        status TEXT,
        outcome TEXT,
        date_added TEXT
    )
    """)

    conn.commit()
    conn.close()


def add_trade(asset, direction, entry_price, stop_loss, target, reasoning):
    """Nayi trade journal mein add karta hai, status 'open' se."""

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO trades
        (asset, direction, entry_price, stop_loss, target, reasoning, status, outcome, date_added)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            asset, direction, entry_price, stop_loss, target, reasoning,
            "open", "", datetime.now().strftime("%Y-%m-%d %H:%M")
        )
    )

    conn.commit()
    trade_id = cursor.lastrowid
    conn.close()

    return trade_id


def close_trade(trade_id, outcome):
    """Trade ko close mark karta hai (outcome = 'win', 'loss', ya koi note)."""

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE trades
        SET status = 'closed', outcome = ?
        WHERE id = ?
        """,
        (outcome, trade_id)
    )

    conn.commit()
    conn.close()


def get_all_trades():
    """Saari trades return karta hai, latest pehle."""

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, asset, direction, entry_price, stop_loss, target,
               reasoning, status, outcome, date_added
        FROM trades
        ORDER BY id DESC
    """)

    result = cursor.fetchall()
    conn.close()

    return result


def get_journal_summary():
    """Trade history ko readable text mein format karta hai LLM ke liye."""

    trades = get_all_trades()

    if not trades:
        return "Abhi tak koi trade journal mein record nahi hui hai."

    summary = "RANA KI TRADE JOURNAL (recent trades):\n\n"

    for t in trades[:10]:
        trade_id, asset, direction, entry, sl, target, reasoning, status, outcome, date = t
        summary += (
            f"#{trade_id} [{date}] {asset} {direction.upper()} "
            f"| Entry: {entry} | SL: {sl} | Target: {target} "
            f"| Status: {status}"
        )
        if outcome:
            summary += f" | Outcome: {outcome}"
        summary += f"\n   Reasoning: {reasoning}\n\n"

    return summary


def get_open_trades():
    """Sirf open trades return karta hai, matching ke liye."""

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, asset, direction, entry_price, stop_loss, target
        FROM trades
        WHERE status = 'open'
        ORDER BY id DESC
    """)

    result = cursor.fetchall()
    conn.close()

    return result