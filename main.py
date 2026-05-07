import telebot
from google import genai
import os

# SIRF TEST KE LIYE - baad mein hata denge
BOT_TOKEN = "8658724060:AAF16usqjm0vSw3Hun941-F3cJyDfnX2aR4"
GOOGLE_API_KEY = os.environ.get('AIzaSyBsWLWmzV7SNtevhNhHnAoNKd4303y75jA')

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
        print(f"Error: {e}")
        bot.reply_to(message, "Sorry Nitin baby, thodi dikkat ho rahi hai!")

print("Rajjo is online...")
bot.infinity_polling()
