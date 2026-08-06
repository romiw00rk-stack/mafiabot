import os
from threading import Thread
from flask import Flask
import telebot
from telebot import types

app = Flask('')
@app.route('/')
def home(): return "Bot is alive!"

def run():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

TOKEN = '8483915034:AAGBY8ssHFQCWLzkvoa7dCupw0rSiqbgeq4' 
bot = telebot.TeleBot(TOKEN)

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🕹 شروع بازی آنلاین"))
    markup.row(types.KeyboardButton("⚡ چالش"), types.KeyboardButton("🎭 سناریو"), types.KeyboardButton("👥 دوستانه"))
    markup.row(types.KeyboardButton("👤 پروفایل"), types.KeyboardButton("🌟 امتیازات"), types.KeyboardButton("❤️ دوستان"))
    markup.row(types.KeyboardButton("🔦 سایر"), types.KeyboardButton("📣 مزایده"), types.KeyboardButton("💰 سکه"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "خوش آمدید! گزینه‌ای را انتخاب کنید:", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, f"بخش «{message.text}» به زودی فعال می‌شود.", reply_markup=get_main_keyboard())

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
