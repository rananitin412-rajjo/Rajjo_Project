# telegram_bot.py

import time
import threading
import os
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

from config import TELEGRAM_TOKEN
from market_data import get_btc_market_data, get_gold_price

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
COMMAND_CHECK_INTERVAL = 15
MOVE_ALERT_COOLDOWN = 3600

last_update_id = None
last_move_alert_time = {"BTC": 0, "GOLD": 0}


# ---- Render ke liye silent HTTP server (sirf "no open ports" error avoid karne ke liye) ----

class SilentHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Rajjo bot is alive")

    def log_message(self, format, *args):
        pass  # terminal ko spam se bachane ke liye


def start_keep_alive_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SilentHandler)
    server.serve_forever()


# ---- Bot ka actual logic (pehle jaisa hi) ----

def send_message(chat_id, text):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text}
        )
    except Exception as e:
        print(f"Telegram send error: {e}")


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
            text = message.get("text", "").strip()

            save_chat_id(chat_id)

            if text.startswith("/alert"):
                parts = text.split()
                if len(parts) == 3:
                    asset = parts[1].upper()
                    try:
                        level = float(parts[2])
                        add_price_alert(asset, level)
                        send_message(
                            chat_id,
                            f"Theek hai Rana! {asset} ke {level} level pe pahunchte hi bata dungi. ✅"
                        )
                    except ValueError:
                        send_message(chat_id, "Format sahi nahi hai. Try: /alert BTC 65000")
                else:
                    send_message(chat_id, "Format: /alert BTC 65000 (ya /alert GOLD 4100)")

            elif text.lower() in ["/start", "hi", "hello"]:
                send_message(
                    chat_id,
                    "Hi Rana! Main Rajjo hoon, ab main market pe nazar rakhungi aur "
                    "koi bada move ya tumhara set kiya hua level aane par bata dungi. 💹\n\n"
                    "Alert set karne ke liye: /alert BTC 65000"
                )

    except Exception as e:
        print(f"Command check error: {e}")


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
    create_alert_tables()

    # Keep-alive server ko alag thread mein chalao
    threading.Thread(target=start_keep_alive_server, daemon=True).start()

    print("Rajjo market-monitoring bot shuru ho gaya hai...")

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