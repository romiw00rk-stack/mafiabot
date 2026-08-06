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
SUPPORT_USERNAME = "@mafiasho_admin"
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
    conn = sqlite3.connect("mafia. la")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            gender TEXT DEFAULT 'نامشخص',
            balance INTEGER DEFAULT 30, 
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
    cursor.execute("SELECT user_id, username, gender, balance, wins, losses FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id, username, gender, balance, wins, losses) VALUES (?, ?, ?, ?, ?, ?)",
                     (user_id, username, 'نامشخص', 30, 0, 0))
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

# دیتابیس موقت برای مدیریت اتاق‌های انتظار
game_rooms = {
    "زودیاک": {"players": [], "min_players": 8},
    "شب مافیا": {"players": [], "min_players": 8},
    "پدرخوانده": {"players": [], "min_players": 8},
    "کلاسیک پیشرفته": {"players": [], "min_players": 8}
}

user_payment_step = {}
user_report_step = {}

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

@bot.message_handler(func=lambda message: message.text == "🕹 شروع بازی آنلاین")
def game_selection(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("🌌 زودیاک", callback_data="join_زودیاک"),
        types.InlineKeyboardButton("🌑 شب مافیا", callback_data="join_شب مافیا"),
        types.InlineKeyboardButton("🎩 پدرخوانده", callback_data="join_پدرخوانده"),
        types.InlineKeyboardButton("🏆 کلاسیک پیشرفته", callback_data="join_کلاسیک پیشرفته")
    ]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "🎯 *مدل بازی مورد نظر خود را انتخاب کنید:*\n(با انتخاب هر بازی، وارد اتاق انتظار می‌شوید)", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("join_"))
def join_game(call):
    game_name = call.data.split("_")[1]
    user = call.from_user
    
    if user.first_name not in game_rooms[game_name]["players"]:
        game_rooms[game_name]["players"].append(user.first_name)
        
        # ساخت لیست بازیکنان به صورت جذاب
        players_list = "\n".join([f"🔹 {p}" for p in game_rooms[game_name]["players"]])
        count = len(game_rooms[game_name]["players"])
        
        text = (f"🎮 *اتاق انتظار: {game_name}*\n"
                f"────────────────\n"
                f"👥 بازیکنان حاضر:\n{players_list}\n"
                f"────────────────\n"
                f"⏳ تعداد: {count} / {game_rooms[game_name]['min_players']}")
        
        if count >= game_rooms[game_name]["min_players"]:
            bot.edit_message_text(f"🚀 *تعداد بازیکنان تکمیل شد!*\nبازی {game_name} همین حالا استارت می‌زند.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            # اینجا در آینده تابع استارت بازی قرار می‌گیرد
        else:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            bot.answer_callback_query(call.id, "وارد اتاق انتظار شدید ✅")
    else:
        bot.answer_callback_query(call.id, "شما قبلاً در این اتاق ثبت‌نام کرده‌اید! ⚠️")

# --- سایر بخش‌ها (پروفایل، حساب، پشتیبانی) دقیقا مانند نسخه قبل است ---
@bot.message_handler(func=lambda message: message.text == "👤 پروفایل")
def show_profile(message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    user_data = get_or_create_user(user_id, username)
    name, gender, wins, losses = user_data[1], user_data[2], user_data[4], user_data[5]
    total_games = wins + losses
    win_rate = int((wins / total_games) * 100) if total_games > 0 else 0
    profile_text = (f"─── ⋆ 👤 ⋆ ───\n✨ *مشخصات کاربری*\n────────────────\n👤 نام: {name}\n⚧ جنسیت: {gender}\n🆔 شناسه: `{user_id}`\n\n🎮 *آمار بازی‌ها*\n🏆 برد: {wins}\n❌ باخت: {losses}\n📈 درصد برد: {win_rate}%\n────────────────")
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("تغییر نام ✏️", callback_data="edit_name"), types.InlineKeyboardButton("تغییر جنسیت ⚧️", callback_data="edit_gender"))
    markup.add(types.InlineKeyboardButton("بستن ❌", callback_data="close_profile"))
    bot.reply_to(message, profile_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "💳 حساب")
def coin_section(message):
    user_id = message.from_user.id
    user_data = get_or_create_user(user_id, message.from_user.first_name)
    balance = user_data[3]
    coin_text = (f"💳 *مدیریت حساب کاربری*\n────────────────\n\n💰 موجودی فعلی شما:\n`{balance} سکه`\n\n────────────────\nهر بازی ۳۰ سکه هزینه دارد.")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💳 شارژ حساب", callback_data="top_up"))
    bot.reply_to(message, coin_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📞 پشتیبانی")
def support_section(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📩 ارسال گزارش", callback_data="send_report"))
    markup.add(types.InlineKeyboardButton("👨‍💻 ارتباط با ادمین", callback_data="contact_admin"))
    support_text = "🛠 *بخش پشتیبانی*\n────────────────\nلطفاً گزینه مورد نظر خود را انتخاب کنید:"
    bot.reply_to(message, support_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "❤️ دوستان")
def friends_section(message):
    bot.reply_to(message, "👥 شما در حال حاضر هیچ دوستی ندارید.")

@bot.message_handler(func=lambda message: message.text == "🌟 امتیازات")
def ranking_section(message):
    bot.reply_to(message, "🏆 *رده‌بندی کلی*\n────────────────\nدر حال حاضر لیست امتیازات در حال به‌روزرسانی است.")

@bot.callback_query_handler(func=lambda call: not call.data.startswith("join_"))
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
    elif call.data == "contact_admin":
        bot.answer_callback_query(call.id, "در حال انتقال...")
        bot.send_message(call.message.chat.id, f"برای ارتباط با مدیریت کلیک کنید:\n{SUPPORT_USERNAME}")
    elif call.data == "send_report":
        user_report_step[user_id] = True
        msg = bot.send_message(call.message.chat.id, "📝 لطفاً گزارش یا مشکل خود را بنویسید و ارسال کنید:")
        bot.register_next_step_handler(msg, process_report)
    elif call.data == "top_up":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💎 ۱۶۰ هزار تومان", callback_data="pay_160"))
        markup.add(types.InlineKeyboardButton("💎 ۳۴۰ هزار تومان", callback_data="pay_340"))
        markup.add(types.InlineKeyboardButton("💎 ۵۵۰ هزار تومان", callback_data="pay_550"))
        bot.edit_message_text("💵 مبلغ شارژ را انتخاب کنید:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data.startswith("pay_"):
        amount = call.data.split("_")[1]
        user_payment_step[user_id] = amount
        payment_text = (f"💳 *اطلاعات واریز*\n━━━━━━━━━━━━\n\n💰 مبلغ: `{amount},000 تومان`\n📌 شماره کارت: `{CARD_NUMBER}`\n👤 به نام: `{CARD_NAME}`\n\nلطفاً عکس رسید را بفرستید.")
        bot.send_message(call.message.chat.id, payment_text, parse_mode="Markdown")

def process_report(message):
    user_id = message.from_user.id
    if user_id in user_report_step:
        report_text = (f"📩 *گزارش جدید*\n────────────────\n"
                       f"👤 کاربر: {message.from_user.first_name}\n"
                       f"🆔 آیدی: `{user_id}`\n"
                       f"📝 متن گزارش:\n{message.text}")
        bot.send_message(ADMIN_ID, report_text, parse_mode="Markdown")
        bot.reply_to(message, "✅ گزارش شما با موفقیت برای مدیریت ارسال شد. متشکریم.")
        del user_report_step[user_id]

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