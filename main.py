import os
import time
import sqlite3
from threading import Thread
from flask import Flask
import telebot
from telebot import types

# وارد کردن تنظیمات و دیتابیس
import config
import database

app = Flask('')
@app.route('/')
def home(): return "Bot is alive!"

def run():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# مقداردهی اولیه دیتابیس
database.init_db()

bot = telebot.TeleBot(config.TOKEN)

game_rooms = {
    "زودیاک": {"players": [], "min_players": 8},
    "شب مافیا": {"players": [], "min_players": 8},
    "پدرخوانده": {"players": [], "min_players": 8},
    "کلاسیک پیشرفته": {"players": [], "min_players": 8}
}

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🕹️ شروع بازی آنلاین"))
    markup.row(types.KeyboardButton("⚡ چالش"), types.KeyboardButton("🎭 سناریو"))
    markup.row(types.KeyboardButton("👤 پروفایل"), types.KeyboardButton("🌟 امتیازات"), types.KeyboardButton("❤️ دوستان"))
    markup.row(types.KeyboardButton("🔦 سایر"), types.KeyboardButton("📞 پشتیبانی"), types.KeyboardButton("💳 حساب"))
    return markup

@bot.message_handler(commands=['start'])

def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    database.get_or_create_user(user_id, username)
    bot.send_message(message.chat.id, "🃏 به ربات مدیریت بازی مافیا خوش آمدید!", parse_mode="Markdown", reply_markup=get_main_keyboard())

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == config.ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("📊 آمار کلی", "💰 مدیریت سکه")
        markup.row("👥 وضعیت اتاق‌ها", "📢 پیام همگانی")
        markup.row("❌ خروج از پنل")
        bot.send_message(message.chat.id, "🛠️ به پنل مدیریت خوش آمدید، رامی جان. چه دستوری دارید؟", reply_markup=markup)
    else:
        bot.reply_to(message, "❌ شما دسترسی لازم برای ورود به این بخش را ندارید.")

@bot.message_handler(func=lambda message: message.from_user.id == config.ADMIN_ID and message.text == "📊 آمار کلی")
def admin_stats(message):
    conn = sqlite3.connect("mafia.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    conn.close()
    bot.send_message(message.chat.id, f"📈 تعداد کل کاربران ثبت شده در ربات:\n`{total_users}` نفر", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "👤 پروفایل")
def show_profile(message):
    user = database.get_or_create_user(message.from_user.id, message.from_user.first_name)
    # user = (id, username, gender, balance, wins, losses)
    profile_text = (f"─── ⋆ 🃏 ⋆ ───\n✨ پروفایل بازیکن\n────────────────\n👤 نام: {user[1]}\n💰 موجودی: {user[3]} سکه\n🏆 برد: {user[4]} | ❌ باخت: {user[5]}\n────────────────")
    bot.reply_to(message, profile_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "💳 حساب")
def account_info(message):
    text = (f"💳 برای شارژ حساب، مبلغ مورد نظر را به شماره زیر واریز کنید:\n\n"
            f"🔢 شماره کارت: `{config.CARD_NUMBER}`\n"
            f"👤 نام صاحب حساب: {config.CARD_NAME}\n\n"
            f"پس از واریز، رسید را به {config.SUPPORT_USERNAME} ارسال کنید.")
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📞 پشتیبانی")
def support_info(message):
    bot.reply_to(message, f"💬 پشتیبانی ربات: {config.SUPPORT_USERNAME}")

# شروع ربات
keep_alive()
bot.infinity_polling()
