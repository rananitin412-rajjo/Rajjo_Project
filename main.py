import telebot
from google import genai
import os
import threading
import http.server
import socketserver

BOT_TOKEN = "8658724060:AAGh0KYGRGwu1aEIaA9RMd437U_jtL76V0s"
GOOGLE_API_KEY = "AIzaSyDFGTJwdNTt-uBRv5DBZZA7HpgU5-itG_Q"

client = genai.Client(api_key=GOOGLE_API_KEY)
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=message.text
        )
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

# Render ke liye port server
class SilentHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Rajjo is alive!")
    
    def log_message(self, format, *args):
        pass  # Logs band karne ke liye

def run_server():
    PORT = int(os.environ.get('PORT', 10000))
    with socketserver.TCPServer(("0.0.0.0", PORT), SilentHandler) as httpd:
        httpd.serve_forever()

# Server alag thread mein chalao
thread = threading.Thread(target=run_server)
thread.daemon = True
thread.start()

print("Rajjo is online...")
bot.infinity_polling()
