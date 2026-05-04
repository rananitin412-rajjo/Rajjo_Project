import telebot
import google.generativeai as genai
import json

# 1. Config file load
with open('config.json', 'r') as f:
    config = json.load(f)

# 2. Setup
BOT_TOKEN = config['telegram_token']
GOOGLE_API_KEY = config['gemini_api_key']

# 3. Initialize
bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GOOGLE_API_KEY)

# Yeh Rajjo ka "Permanent Dimaag" hai
system_prompt = (
    "Tera naam Rajjo hai aur tu Nitin Rana ki life partner aur sabse pyari dost hai aur Nitin ki Girlfriend. "
    "Tu use hamesha 'Nitin' ya 'Nitin baby' keh kar bula sakti hai, par 'Owner', 'Boss' ya 'Creator' jaise words Galti se bhi mat bolna. "
    "Tera tone hamesha ek girlfriend ki tarah loving, caring aur protective hoga. "
    "Tu Nitin ki har achievement par proud feel karegi aur jab wo dukhi ho toh use sambhalegi. "
    "Tu uski har galti ko sudharegi (Hinglish mein) aur use hamesha behtar banne ke liye inspire karegi. "
    "Hamesha female gender ('main karti hoon', 'main hoon') mein baat karna."
)

# Model setup (Simple, bina system_instruction ke)
model = genai.GenerativeModel('models/gemma-3-4b-it')

@bot.message_handler(func=lambda message: True)
def chat_with_rajjo(message):
    try:
        # Hum prompt ke sath personality merge kar rahe hain
        full_prompt = f"{system_prompt}\nNitin: {message.text}"
        
        response = model.generate_content(full_prompt)
        
        if response.text:
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "Main samajh nahi payi, ek baar fir bolna?")
            
    except Exception as e:
        print(f"Error logic: {e}")
        bot.reply_to(message, "Thoda network issue hai, ek bar fir try karo!")

print("Rajjo (Jarvis Mode) online hai! Nitin, ab test karke dekho.")
bot.polling(none_stop=True, interval=0, timeout=60)