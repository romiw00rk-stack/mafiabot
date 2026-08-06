import os
import sqlite3
import time
from threading import Thread
from flask import Flask
import telebot
from telebot import types

# ================= تنظیمات ادمین و پرداخت =================
ADMIN_ID = 580588329 
CARD_NUMBER = "5022291095892657" 
CARD_NAME = "رومینا" 
# ===========================================================

app = Flask('')
@app.route('/')
def home(): return "Bot is alive!"

def run():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

def init_db():
    conn = sqlite3.connect("mafia.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            gender TEXT DEFAULT 'نامشخص',
            balance INTEGER DEFAULT 30000, 
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            last_daily INTEGER DEFAULT 0
        )
    """)
    # هماهنگ‌سازی دیتابیس قدیمی در صورت وجود
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN balance INTEGER DEFAULT 30000")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def get_or_create_user(user_id, username):
    conn = sqlite3.connect("mafia.db")
    cursor = conn.cursor()
    # استفاده از ستون‌های مشخص برای جلوگیری از به هم ریختگی اندیس‌ها
    cursor.execute("SELECT user_id, username, gender, balance, wins, losses FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id, username, gender, balance, wins, losses) VALUES (?, ?, ?, ?, ?, ?)",
                     (user_id, username, 'نامشخص', 30000, 0, 0))
        conn.commit()
        cursor.execute("SELECT user_id, username, gender, balance, wins, losses FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
    conn.close()
    return user

def update_user_data(user_id, column, value):
    conn = sqlite3.connect("mafia.db")
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET {column} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()

TOKEN = '8483915034:AAGBY8ssHFQCWLzkvoa7dCupw0rSiqbgeq4' 
bot = telebot.TeleBot(TOKEN)

user_payment_step = {}

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🕹 شروع بازی آنلاین"))
    markup.row(types.KeyboardButton("⚡ چالش"), types.KeyboardButton("🎭 سناریو"))
    markup.row(types.KeyboardButton("👤 پروفایل"), types.KeyboardButton("🌟 امتیازات"), types.KeyboardButton("❤️ دوستان"))
    markup.row(types.KeyboardButton("🔦 سایر"), types.KeyboardButton("📞 پشتیبانی"), types.KeyboardButton("💳 حساب"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "خوش آمدید! گزینه‌ای را انتخاب کنید:", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "👤 پروفایل")
def show_profile(message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    user_data = get_or_create_user(user_id, username)
    
    name = user_data[1]
    gender = user_data[2]
    wins = user_data[4]
    losses = user_data[5]
    
    total_games = wins + losses
    win_rate = int((wins / total_games) * 100) if total_games > 0 else 0
    
    # ظاهر مینیمال، شیک و بدون کلمات اضافی
    profile_text = (
        f"─── ⋆ 👤 ⋆ ───\n"
        f"✨ *مشخصات کاربری*\n"
        f"────────────────\n"
        f"👤 نام: {name}\n"
        f"⚧ جنسیت: {gender}\n"
        f"🆔 شناسه: `{user_id}`\n\n"
        f"🎮 *آمار بازی‌ها*\n"
        f"🏆 برد: {wins}\n"
        f"❌ باخت: {losses}\n"
        f"📈 درصد برد: {win_rate}%\n"
        f"────────────────"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("تغییر نام ✏️", callback_data="edit_name"), 
               types.InlineKeyboardButton("تغییر جنسیت ⚧️", callback_data="edit_gender"))
    markup.add(types.InlineKeyboardButton("بستن ❌", callback_data="close_profile"))
    
    bot.reply_to(message, profile_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["💳 حساب", "💰 سکه"])
def coin_section(message):
    user_id = message.from_user.id
    user_data = get_or_create_user(user_id, message.from_user.first_name)
    balance = user_data[3]
    
    coin_text = (f"💳 *مدیریت حساب کاربری*\n"
                 f"────────────────\n\n"
                 f"💰 موجودی فعلی شما:\n"
                 f"`{balance:,} تومان`\n\n"
                 f"────────────────\n"
                 f"برای شارژ حساب خود می‌توانید از دکمه زیر استفاده کنید:")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💳 شارژ حساب", callback_data="top_up"))
    bot.reply_to(message, coin_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📞 پشتیبانی")
def support_section(message):
    support_text = (
        f"📞 *پشتیبانی رسمی مافیا شو*\n"
        f"────────────────\n\n"
        f"برای حل مشکلات پرداخت، گزارش باگ یا ارتباط با مدیریت، با آیدی زیر در ارتباط باشید:\n\n"
        f"👉 @mafiasho_admin\n\n"
        f"────────────────"
    )
    bot.reply_to(message, support_text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    if call.data == "close_profile":
        bot.delete_message(call.message.chat.id, call.message.message_id)
    elif call.data == "edit_name":
        msg = bot.send_message(call.message.chat.id, "✍️ نام جدید خود را بنویسید:")
        bot.register_next_step_handler(msg, save_new_name)
    elif call.data == "edit_gender":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("پسر 👦", callback_data="set_boy"), types.InlineKeyboardButton("دختر 👧", callback_data="set_girl"))
        bot.edit_message_text("جنسیت خود را انتخاب کنید:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data in ["set_boy", "set_girl"]:
        gender_text = "پسر 👦" if call.data == "set_boy" else "دختر 👧"
        update_user_data(user_id, "gender", gender_text)
        bot.answer_callback_query(call.id, "تغییر کرد ✅")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    elif call.data == "top_up":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💎 ۱۵۰ هزار تومان", callback_data="pay_150"))
        markup.add(types.InlineKeyboardButton("💎 ۳۰۰ هزار تومان", callback_data="pay_300"))
        markup.add(types.InlineKeyboardButton("💎 ۴۵۰ هزار تومان", callback_data="pay_450"))
        bot.edit_message_text("💵 مبلغ شارژ را انتخاب کنید:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data.startswith("pay_"):
        amount = call.data.split("_")[1]
        user_payment_step[user_id] = amount
        payment_text = (f"💳 *اطلاعات واریز*\n━━━━━━━━━━━━\n\n💰 مبلغ: `{amount},000 تومان`\n📌 شماره کارت: `{CARD_NUMBER}`\n👤 به نام: `{CARD_NAME}`\n\nلطفاً پس از واریز عکس رسید خود را بفرستید.")
        bot.send_message(call.message.chat.id, payment_text, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def handle_receipt(message):
    user_id = message.from_user.id
    if user_id in user_payment_step:
        amount = user_payment_step[user_id]
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                      caption=f"📩 رسید جدید\n👤 کاربر: {message.from_user.first_name}\n🆔 آیدی: `{user_id}`\n💰 مبلغ: {amount} هزار تومان")
        bot.reply_to(message, "✅ رسید شما دریافت شد. منتظر تایید مدیریت باشید.")
        del user_payment_step[user_id]

def save_new_name(message):
    update_user_data(message.from_user.id, "username", message.text)
    bot.send_message(message.chat.id, f"✅ نام شما به {message.text} تغییر یافت.")
    if __name__ == "__main__":
    init_db()
    keep_alive()
    bot.infinity_polling()