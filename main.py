import telebot
from google import genai
import os

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

print("Rajjo is online...")
bot.infinity_polling()
