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
    conn = sqlite3.connect("mafia.db")
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
    conn = sqlite3. la
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

# ================= پنل مدیریت =================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("📊 آمار کلی", "💰 مدیریت سکه")
        markup.row("👥 وضعیت اتاق‌ها", "📢 پیام همگانی")
        markup.row("❌ خروج از پنل")
        bot.send_message(message.chat.id, "🛠 به پنل مدیریت خوش آمدید، رامی جان. چه دستوری دارید؟", reply_markup=markup)
    else:
        bot.reply_to(message, "❌ شما دسترسی لازم برای ورود به این بخش را ندارید.")

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and message.text == "📊 آمار کلی")
def admin_stats(message):
    conn = sqlite3.connect("mafia.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    conn.close()
    bot.send_message(message.chat.id, f"📈 تعداد کل کاربران ثبت شده در ربات:\n`{total_users}` نفر", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and message.text == "💰 مدیریت سکه")
def admin_coin_manage(message):
    bot.send_message(message.chat.id, "🆔 آیدی کاربر و مقدار سکه را به این صورت بفرستید:\n`آیدی مقدار` \nمثال: `12345678 100`", parse_mode="Markdown")
    bot.register_next_step_handler(message, set_coin_admin)

def set_coin_admin(message):
    try:
        uid, amount = message.text.split()
        update_user_data(int(uid), "balance", int(amount))
        bot.send_message(message.chat.id, f"✅ موجودی کاربر {uid} به {amount} سکه تغییر یافت.")
    except:
        bot.send_message(message.chat.id, "❌ فرمت اشتباه بود. لطفاً دوباره تلاش کنید.")

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and message.text == "👥 وضعیت اتاق‌ها")
def admin_rooms_status(message):
    status = "📋 *وضعیت اتاق‌های انتظار*\n────────────────\n"
    for game, data in game_rooms.items():
        status += f"🎮 {game}: {len(data['players'])} نفر\n"
    bot.send_message(message.chat.id, status, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and message.text == "📢 پیام همگانی")
def admin_broadcast(message):
    bot.send_message(message.chat.id, "📝 متن پیام خود را بنویسید تا برای همه ارسال شود:")
    bot.register_next_step_handler(message, send_broadcast)

def send_broadcast(message):
    conn = sqlite3.connect("mafia. la")
    conn = sqlite3.connect("mafia.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    count = 0
    for u in users:
        try:
            bot.send_message(u[0], f"📢 *پیام مدیریت*\n\n{message.text}", parse_mode="Markdown")
            count += 1
        except: pass
    bot.send_message(message.chat.id, f"✅ پیام برای {count} کاربر ارسال شد.")

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and message.text == "❌ خروج از پنل")
def admin_exit(message):
    bot.send_message(message.chat.id, "خروج از پنل مدیریت...", reply_markup=get_main_keyboard())

# ================= بخش‌های کاربر =================
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
    bot.send_message(message.chat.id, "🎯 *مدل بازی مورد نظر خود را انتخاب کنید:*", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("join_"))
def join_game(call):
    game_name = call.data.split("_")[1]
    user = call.from_user
    if user.first_name not in game_rooms[game_name]["players"]:
        game_rooms[game_name]["players"].append(user.first_name)
        players_list = "\n".join([f"🔹 {p}" for p in game_rooms[game_name]["players"]])
        count = len(game_rooms[game_name]["players"])
        text = (f"🎮 *اتاق انتظار: {game_name}*\n────────────────\n👥 بازیکنان حاضر:\n{players_list}\n────────────────\n⏳ تعداد: {count} / {game_rooms[game_name]['min_players']}")
        if count >= game_rooms[game_name]["min_players"]:
            bot.edit_message_text(f"🚀 *تعداد بازیکنان تکمیل شد!*\nبازی {game_name} استارت می‌زند.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            bot.answer_callback_query(call.id, "وارد اتاق شدید ✅")
    else:
        bot.answer_callback_query(call.id, "شما قبلاً ثبت‌نام کرده‌اید! ⚠️")

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
    markup = types.Inline uma
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📩 ارسال گزارش", callback_data="send_report"))
    markup.add(types.InlineKeyboardButton("👨‍💻 ارتباط با ادمین", callback_data="contact_admin"))
    bot.reply_to(message, "🛠 *بخش پشتیبانی*\n────────────────\nلطفاً گزینه مورد نظر را انتخاب کنید:", parse_mode="Markdown", reply_markup=markup)

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
        bot.send_message(call.message.chat.id, f"برای ارتباط با مدیریت کلیک کنید:\n{SUPPORT_USERNAME}")
    elif call.data == "send_report":
        user_report_step[user_id]