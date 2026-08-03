# telegram_bot.py

import time
import threading
import os
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

from config import TELEGRAM_TOKEN
from llm import ask_llm, ask_llm_with_image
from personality import SYSTEM_PROMPT
from trading_knowledge import TRADING_KNOWLEDGE

from memory import (
    create_database,
    save_memory,
    get_all_memories
)

from memory_ai import extract_all
from market_data import get_btc_market_data, get_gold_price, get_market_snapshot

from trade_journal import (
    create_journal_table,
    add_trade,
    close_trade,
    get_journal_summary,
    get_open_trades
)

from alerts_db import (
    create_alert_tables,
    save_price_snapshot,
    get_price_minutes_ago,
    add_price_alert,
    get_active_alerts,
    mark_alert_triggered,
    save_chat_id,
    get_chat_id
)


TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

MOVE_THRESHOLD_PERCENT = 2.0
ROLLING_WINDOW_MINUTES = 30
PRICE_CHECK_INTERVAL = 120
COMMAND_CHECK_INTERVAL = 5
MOVE_ALERT_COOLDOWN = 3600

last_update_id = None
last_move_alert_time = {"BTC": 0, "GOLD": 0}

# Poori conversation history yahan rakhते hain (jaise app.py mein session_state karta tha)
conversation_history = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT + "\n\n" + TRADING_KNOWLEDGE
    }
]


# ---- Render ke liye silent HTTP server ----

class SilentHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Rajjo bot is alive")

    def log_message(self, format, *args):
        pass


def start_keep_alive_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SilentHandler)
    server.serve_forever()


# ---- Telegram helpers ----

def send_message(chat_id, text):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text}
        )
    except Exception as e:
        print(f"Telegram send error: {e}")


def download_telegram_photo(file_id):
    """Telegram se photo download karta hai, raw bytes return karta hai."""
    try:
        file_info = requests.get(
            f"{TELEGRAM_API}/getFile", params={"file_id": file_id}, timeout=10
        ).json()

        file_path = file_info["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"

        image_response = requests.get(file_url, timeout=15)
        return image_response.content

    except Exception as e:
        print(f"Photo download error: {e}")
        return None


# ---- Core reply logic (shared by text aur image) ----

def build_context_and_reply(user_text, image_bytes=None):

    global conversation_history

    conversation_history.append({"role": "user", "content": user_text or "[Image bheji]"})

    open_trades = get_open_trades()
    extracted = extract_all(user_text or "chart image", open_trades)

    memory = extracted.get("memory")
    if memory:
        save_memory(memory.get("category"), memory.get("key"), memory.get("value"))

    new_trade = extracted.get("new_trade")
    if new_trade:
        add_trade(
            new_trade.get("asset"), new_trade.get("direction"),
            new_trade.get("entry_price"), new_trade.get("stop_loss"),
            new_trade.get("target"), new_trade.get("reasoning")
        )

    close_info = extracted.get("close_trade")
    if close_info:
        close_trade(close_info.get("trade_id"), close_info.get("outcome"))

    memory_text = ""
    for category, key, value in get_all_memories():
        memory_text += f"[{category}] {key}: {value}\n"

    market_text = get_market_snapshot()
    journal_text = get_journal_summary()

    live_context = {
        "role": "system",
        "content": (
            "Yeh Rana ke baare mein stored memory hai. Sirf tab use karo jab relevant ho.\n\n"
            f"{memory_text}\n\n"
            "Yeh abhi ke live market prices hain. Agar Rana price ya market ke "
            "baare mein pooche to inhi actual numbers ka use karo.\n\n"
            f"{market_text}\n\n"
            "Yeh Rana ki trade journal hai.\n\n"
            f"{journal_text}"
        )
    }

    messages_for_this_call = conversation_history + [live_context]

    if image_bytes:
        reply = ask_llm_with_image(messages_for_this_call, image_bytes, "image/jpeg")
    else:
        reply = ask_llm(messages_for_this_call)

    conversation_history.append({"role": "assistant", "content": reply})

    # History bahut lambi na ho jaaye, isliye last 20 messages hi rakhte hain (system chhod ke)
    if len(conversation_history) > 21:
        conversation_history[:] = [conversation_history[0]] + conversation_history[-20:]

    return reply


# ---- Commands aur messages check karna ----

def check_commands():
    global last_update_id

    try:
        params = {"timeout": 5}
        if last_update_id:
            params["offset"] = last_update_id + 1

        response = requests.get(f"{TELEGRAM_API}/getUpdates", params=params, timeout=10)
        data = response.json()

        for update in data.get("result", []):
            last_update_id = update["update_id"]

            message = update.get("message")
            if not message:
                continue

            chat_id = message["chat"]["id"]
            save_chat_id(chat_id)

            text = message.get("text", "").strip() if message.get("text") else ""
            photo = message.get("photo")
            caption = message.get("caption", "").strip() if message.get("caption") else ""

            # --- Alert command ---
            if text.startswith("/alert"):
                parts = text.split()
                if len(parts) == 3:
                    asset = parts[1].upper()
                    try:
                        level = float(parts[2])
                        add_price_alert(asset, level)
                        send_message(chat_id, f"Theek hai Rana! {asset} ke {level} level pe pahunchte hi bata dungi. ✅")
                    except ValueError:
                        send_message(chat_id, "Format sahi nahi hai. Try: /alert BTC 65000")
                else:
                    send_message(chat_id, "Format: /alert BTC 65000 (ya /alert GOLD 4100)")
                continue

            # --- Start command ---
            if text.lower() == "/start":
                send_message(
                    chat_id,
                    "Hi Rana! Main Rajjo hoon. Ab tum mujhse normal baat bhi kar sakte ho, "
                    "chart bhej sakte ho, aur main market pe nazar bhi rakhungi. 💹\n\n"
                    "Alert set karne ke liye: /alert BTC 65000"
                )
                continue

            # --- Photo (chart image) ---
            if photo:
                send_message(chat_id, "Dekh rahi hoon... ⏳")
                largest_photo = photo[-1]
                image_bytes = download_telegram_photo(largest_photo["file_id"])

                if image_bytes:
                    reply = build_context_and_reply(caption, image_bytes)
                    send_message(chat_id, reply)
                else:
                    send_message(chat_id, "Image download nahi ho payi, dobara try karo Rana.")
                continue

            # --- Normal text message (full conversation) ---
            if text:
                reply = build_context_and_reply(text)
                send_message(chat_id, reply)

    except Exception as e:
        print(f"Command check error: {e}")


# ---- Background price monitoring (jaisa pehle tha) ----

def check_price_moves(chat_id):

    btc = get_btc_market_data()
    gold = get_gold_price()

    now = time.time()

    if btc:
        save_price_snapshot("BTC", btc["price"])
        old_price = get_price_minutes_ago("BTC", ROLLING_WINDOW_MINUTES)
        if old_price:
            change_percent = ((btc["price"] - old_price) / old_price) * 100
            if abs(change_percent) >= MOVE_THRESHOLD_PERCENT:
                if now - last_move_alert_time["BTC"] > MOVE_ALERT_COOLDOWN:
                    direction = "upar 📈" if change_percent > 0 else "neeche 📉"
                    send_message(
                        chat_id,
                        f"Rana! BTC pichle {ROLLING_WINDOW_MINUTES} minute mein "
                        f"{abs(change_percent):.2f}% {direction} move ho chuka hai. "
                        f"Abhi price: ${btc['price']:,.2f}. Check kar lo! ⚡"
                    )
                    last_move_alert_time["BTC"] = now

    if gold:
        save_price_snapshot("GOLD", gold)
        old_price = get_price_minutes_ago("GOLD", ROLLING_WINDOW_MINUTES)
        if old_price:
            change_percent = ((gold - old_price) / old_price) * 100
            if abs(change_percent) >= MOVE_THRESHOLD_PERCENT:
                if now - last_move_alert_time["GOLD"] > MOVE_ALERT_COOLDOWN:
                    direction = "upar 📈" if change_percent > 0 else "neeche 📉"
                    send_message(
                        chat_id,
                        f"Rana! Gold pichle {ROLLING_WINDOW_MINUTES} minute mein "
                        f"{abs(change_percent):.2f}% {direction} move ho chuka hai. "
                        f"Abhi price: ${gold:,.2f}. Check kar lo! ⚡"
                    )
                    last_move_alert_time["GOLD"] = now

    current_prices = {}
    if btc:
        current_prices["BTC"] = btc["price"]
    if gold:
        current_prices["GOLD"] = gold

    for alert_id, asset, level in get_active_alerts():
        if asset in current_prices:
            price = current_prices[asset]
            if abs(price - level) / level <= 0.001:
                send_message(
                    chat_id,
                    f"Rana! {asset} apne set kiye hue level {level} ke paas pahunch gaya hai. "
                    f"Abhi price: ${price:,.2f} 🎯"
                )
                mark_alert_triggered(alert_id)


def main():
    create_database()
    create_journal_table()
    create_alert_tables()

    threading.Thread(target=start_keep_alive_server, daemon=True).start()

    print("Rajjo (full conversation + monitoring) shuru ho gaya hai...")

    last_price_check = 0

    while True:
        check_commands()

        chat_id = get_chat_id()

        if chat_id and (time.time() - last_price_check) >= PRICE_CHECK_INTERVAL:
            check_price_moves(chat_id)
            last_price_check = time.time()

        time.sleep(COMMAND_CHECK_INTERVAL)


if __name__ == "__main__":
    main()