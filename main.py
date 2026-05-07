import telebot
from google import genai
import os

BOT_TOKEN = os.environ.get('8658724060:AAG_yi4hTy9T4g6PNfBARMKaUkeOPDjHZR0')
GOOGLE_API_KEY = os.environ.get('AIzaSyBsWLWmzV7SNtevhNhHnAoNKd4303y75jA')

# Naya package use kar rahe hain
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
