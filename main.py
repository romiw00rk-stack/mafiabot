import os
import sqlite3
import time
from threading import Thread
from flask import Flask
import telebot
from telebot import types

# ================= تنظیمات ادمین و پرداخت =================
ADMIN_ID = 00000000  # <--- ⚠️ حتما آیدی عددی تلگرامت را اینجا بنویس (مثلا 12345678)
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
    conn = sqlite3.connect("mafia. la_db" if os.environ.get("PRODUCTION") else "mafia.db")
    conn = sqlite3.connect("mafia.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            gender TEXT DEFAULT 'نامشخص',
            coins INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            last_daily INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_or_create_user(user_id, username):
    conn = sqlite3.connect("mafia.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id, username, gender, coins, xp, wins, losses) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (user_id, username, 'نامشخص', 0, 0, 0, 0))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
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

# ذخیره وضعیت پرداخت کاربران
user_payment_step = {}

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

@bot.message_handler(func=lambda message: message.text == "👤 پروفایل")
def show_profile(message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    user_data = get_or_create_user(user_id, username)
    name, gender, coins, xp, wins, losses = user_data[1], user_data[2], user_data[3], user_data[4], user_data[5], user_data[6]
    total_games = wins + losses
    win_rate = int((wins / total_games) * 100) if total_games > 0 else 0
    level = "شهروند مبتدی 👤" if xp < 100 else "کارآگاه زبده 🔍" if xp < 500 else "پدرخوانده 🕶️"
    profile_text = f"👤 *پروفایل شما*\n━━━━━━━━━━━━\n🏷️ نام: {name}\n🚻 جنسیت: {gender}\n🆔 شناسه: `{user_id}`\n🎖️ سطح: {level}\n\n📊 آمار:\n🎮 کل بازی‌ها: {total_games}\n🏆 برد: {wins} ({win_rate}%)\n❌ باخت: {losses}\n\n💰 دارایی:\n🪙 سکه: {coins}\n🌟 امتیاز: {xp}\n━━━━━━━━━━━━"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("تغییر نام ✏️", callback_data="edit_name"), types.InlineKeyboardButton("تغییر جنسیت ⚧️", callback_data="edit_gender"))
    markup.add(types.InlineKeyboardButton("بستن ❌", callback_data="close_profile"))
    bot.reply_to(message, profile_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "💰 سکه")
def coin_section(message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    user_data = get_or_create_user(user_id, username)
    coins = user_data[3]
    
    # نمایش موجودی با استایل حرفه‌ای
    coin_text = (f"💰 *بخش مدیریت سکه‌ها*\n"
                 f"━━━━━━━━━━━━\n\n"
                 f"🪙 موجودی فعلی شما:\n`{coins} سکه`\n\n"
                 f"━━━━━━━━━━━━")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💳 شارژ حساب (خرید سکه)", callback_data="top_up"))
    bot.reply_to(message, coin_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    if call.data == "close_profile":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "بسته شد.")
    elif call.data == "edit_name":
        bot.answer_callback_query(call.id, "نام جدید را بفرستید")
        msg = bot.send_message(call.message.chat.id, "✍️ نام جدید خود را بنویسید:")
        bot.register_next_step_handler(msg, save_new_name)
    elif call.data == "edit_gender":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("پسر 👦", callback_data="set_boy"), types.InlineKeyboardButton("دختر 👧", callback_data="set_girl"))
        bot.edit_message_text("جنسیت خود را انتخاب کنید:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data == "set_boy":
        update_user_data(user_id, "gender", "پسر 👦")
        bot.answer_callback_query(call.id, "تغییر کرد ✅")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    elif call.data == "set_girl":
        update_user_data(user_id, "gender", "دختر 👧")
        bot.answer_callback_query(call.id, "تغییر کرد ✅")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    
    # --- شروع پروسه شارژ حساب حرفه‌ای ---
    elif call.data == "top_up":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💎 ۱۵۰ هزار تومان", callback_data="pay_150"))
        markup.add(types.InlineKeyboardButton("💎 ۳۰۰ هزار تومان", callback_data="pay_300"))
        markup.add(types.InlineKeyboardButton("💎 ۴۵۰ هزار تومان", callback_data="pay_450"))
        bot.edit_message_text("💵 لطفاً مبلغ مورد نظر برای شارژ حساب را انتخاب کنید:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        
    elif call.data.startswith("pay_"):
        amount = call.data.split("_")[1]
        user_payment_step[user_id] = amount # ذخیره مبلغ برای تایید نهایی
        
        payment_text = (f"💳 *درخواست شارژ حساب*\n"
                       f"━━━━━━━━━━━━\n\n"
                       f"💰 مبلغ انتخابی: `{amount},000 تومان`\n\n"
                       f"📌 شماره کارت جهت واریز:\n`{CARD_NUMBER}`\n"
                       f"👤 به نام: `{CARD_NAME}`\n\n"
                       f"━━━━━━━━━━━━\n"
                       f"⚠️ *مرحله نهایی:*\n"
                       f"لطفاً پس از انجام تراکنش، *عکس رسید* را همین‌جا ارسال کنید تا پس از بررسی توسط مدیریت، حساب شما شارژ شود. ✅")
        
        bot.answer_callback_query(call.id, "اطلاعات پرداخت")
        bot.send_message(call.message.chat.id, payment_text, parse_mode="Markdown")

# هندلر دریافت عکس رسید (بسیار مهم)
@bot.message_handler(content_types=['photo'])
def handle_receipt(message):
    user_id = message.from_user.id
    if user_id in user_payment_step:
        amount = user_payment_step[user_id]
        
        # ارسال رسید به ادمین (رومینا)
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                      caption=f"🔔 *رسید پرداخت جدید دریافت شد!*\n\n👤 کاربر: {message.from_user.first_name}\n🆔 آیدی: `{user_id}`\n💰 مبلغ درخواستی: {amount},000 تومان", 
                      parse_mode="Markdown")
        
        bot.reply_to(message, "✅ *رسید شما با موفقیت ارسال شد.*\n\n⏳ در حال حاضر مدیریت در حال بررسی رسید شماست. به محض تایید، سکه‌ها به حساب شما اضافه خواهد شد. متشکریم! 🙏", parse_mode="Markdown")
        
        # پاک کردن وضعیت پرداخت برای جلوگیری از ارسال رسیدهای تکراری
        del user_payment_step[user_id]

def save_new_name(message):
    update_user_data(message.from_user.id, "username", message.text)
    bot.send_message(message.chat.id, f"✅ نام شما به {message.text} تغییر یافت.")
    show_profile(message)

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, f"بخش «{message.text}» به زودی فعال می‌شود.", reply_markup=get_main_keyboard())

if __name__ == "__main__":
    init_db()
    keep_alive()
    bot.infinity_polling()