import telebot
import google.generativeai as genai
import os

# Render ke environment variables se keys uthana
# Nitin baby, dhyaan rakhna ki Render settings mein keys ke naam exact yahi hon
BOT_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GOOGLE_API_KEY = os.environ.get('GEMINI_API_KEY')

# Bot aur AI configure karna
bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash-latest')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # User ka message AI ko bhejna
        response = model.generate_content(message.text)
        # AI ka reply user ko bhejna
        bot.reply_to(message, response.text)
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Sorry Nitin baby, thodi dikkat ho rahi hai. Keys check karo!")

print("Rajjo is online...")
bot.polling()
