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
BAD_WORDS = ["کلمه۱", "کلمه۲", "کلمه۳"] # کلمات ممنوعه را اینجا بنویس
# ===========================================================

# لینک‌های ۱۰ اتاق گیم رامی جان
ROOM_LINKS = [
    "https://t.me/+HJ1A76sBGEAwYTdk", # اتاق ۱
    "https://t.me/+DWnJJcyBkmhhZTBk", # اتاق ۲
    "https://t.me/+X-r4xtXJaXpkMzJk", # اتاق ۳
    "https://t.me/+p1Estt71cU45NzBk", # اتاق ۴
    "https://t.me/+RLbTxBn7Bd9jOWM0", # اتاق ۵
    "https://t.me/+4xuDGo_zD7IxNDU0", # اتاق ۶
    "https://t.me/+P0yblouGcJphNjI0", # اتاق ۷
    "https://t.me/+e01UDD1ALU42ZjQ8", # اتاق ۸
    "https://t.me/+h1tTM4wvK0M1ZjU0", # اتاق ۹
    "https://t.me/+yBIzkezu7HA0MTA8"  # اتاق ۱۰
]
used_rooms = []

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
            warnings INTEGER DEFAULT 0,
            ban_until INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("mafia.db")
    cursor = conn.cursor()
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

game_rooms = {
    "زودیاک": {"players": [], "min_players": 8},
    "شب مافیا": {"players": [], "min_players": 8},
    "پدرخوانده": {"players": [], "min_players": 8},
    "کلاسیک پیشرفته": {"players": [], "min_players": 8}
}

# ================= ۱. دستور استارت (برای نمایش دکمه‌ها) =================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # ثبت‌نام کاربر در دیتابیس در صورت عدم وجود
    if not get_user(user_id):
        conn = sqlite3.connect("mafia.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
        conn.close()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_game = types.KeyboardButton("🕹 شروع بازی آنلاین")
    btn_profile = types.KeyboardButton("👤 پروفایل")
    markup.add(btn_game, btn_profile)
    
    bot.send_message(
        message.chat.id, 
        "🃏 *به ربات مدیریت بازی مافیا خوش آمدید!*\n\nبرای استفاده از ربات از دکمه‌های زیر استفاده کنید:", 
        parse_mode="Markdown", 
        reply_markup=markup
    )

# ================= ۲. دستور ادمین برای ریست کردن اتاق‌ها =================
@bot.message_handler(commands=['reset_room'])
def reset_room(message):
    if message.from_user.id == ADMIN_ID:
        global used_rooms
        used_rooms = [] 
        bot.send_message(message.chat.id, "✅ تمام اتاق‌های گیم ریست شدند و آماده بازی جدید هستند.")

# ================= ۳. دکمه شروع بازی آنلاین =================
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

# ================= ۴. دکمه پروفایل بازیکن =================
@bot.message_handler(func=lambda message: message.text == "👤 پروفایل")
def show_profile(message):
    user_id = message.from_user.id
    u_data = get_user(user_id)
    if not u_data: 
        bot.reply_to(message, "❌ ابتدا ربات را استارت کنید: /start")
        return
    
    name, gender, wins, losses, warns, ban_until = u_data[1], u_data[2], u_data[4], u_data[5], u_data[6], u_data[7]
    
    status = "🟢 فعال و آماده بازی"
    if ban_until and ban_until > time.time():
        status = "🚫 در بازداشتگاه است (بن ۲۴ ساعته)"
    elif warns > 0:
        status = f"⚠️ در معرض خطر ( {warns} اخطار دارد)"

    profile_text = (
        f"─── ⋆ 🃏 ⋆ ───\n"
        f"✨ *پروفایل بازیکن*\n"
        f"────────────────\n"
        f"👤 نام: {name}\n"
        f"⚧ جنسیت: {gender}\n"
        f"🆔 شناسه: `{user_id}`\n"
        f"🛡 وضعیت: {status}\n"
        f"────────────────\n"
        f"🏆 برد: {wins} | ❌ باخت: {losses}\n"
        f"🌟 رنک: {'لجند 👑' if wins > 20 else 'مبتدی 🌱'}\n"
        f"────────────────"
    )
    bot.reply_to(message, profile_text, parse_mode="Markdown")

# ================= ۵. سیستم ضد بی‌ادبی (انتهای لیست تا بقیه دکمه‌ها کار کنند) =================
@bot.message_handler(func=lambda message: True)
def anti_toxic(message):
    user_id = message.from_user.id
    text = message.text.lower() if message.text else ""
    
    if any(word in text for word in BAD_WORDS):
        user = get_user(user_id)
        if user:
            warns = user[6] if user[6] else 0
            warns += 1
            update_user_data(user_id, "warnings", warns)
            if warns < 3:
                bot.reply_to(message, f"⚠️ {message.from_user.first_name} عزیز!\nبی‌ادبی ممنوع است.\n🔴 اخطار {warns} از ۳", parse_mode="Markdown")
            else:
                ban_time = int(time.time()) + (24 * 3600)
                update_user_data(user_id, "ban_until", ban_time)
                try:
                    bot.ban_chat_member(message.chat.id, user_id)
                    bot.send_message(message.chat.id, f"🚫 کاربر {message.from_user.first_name} به دلیل تخلف، ۲۴ ساعت به زندان منتقل شد! ⛓️")
                except Exception as e:
                    bot.send_message(message.chat.id, f"⚠️ خطایی در بن کردن رخ داد. مطمئن شوید ربات در گروه ادمین است.")
                update_user_data(user_id, "warnings", 0)

# ================= سیستم هندلر دکمه‌های شیشه‌ای (Callback Query) =================
@bot.callback_query_handler(func=lambda call: call.data.startswith("join_"))
def join_game(call):
    game_name = call.data.split("_")[1]
    user = call.from_user
    user_id = user.id
    
    u_data = get_user(user_id)
    if u_data and u_data[7] and u_data[7] > time.time():
        bot.answer_callback_query(call.id, "❌ تو فعلاً توی زندانی! باید منتظر بمونی تا بن‌ت تموم شه.", show_alert=True)
        return

    if user.first_name not in game_rooms[game_name]["players"]:
        game_rooms[game_name]["players"].append(user.first_name)
        count = len(game_rooms[game_name]["players"])
        
        players_list = "\n".join([f"🔹 {p}" for p in game_rooms[game_name]["players"]])
        text = (f"🎮 *اتاق انتظار: {game_name}*\n────────────────\n👥 بازیکنان حاضر:\n{players_list}\n────────────────\n⏳ تعداد: {count} / 8")
        
        if count >= 8:
            available_rooms = [r for r in ROOM_LINKS if r not in used_rooms]
            if available_rooms:
                room_link = available_rooms[0]
                used_rooms.append(room_link)
                
                bot.edit_message_text(f"🚀 *تعداد بازیکنان تکمیل شد!*\n\n🎮 بازی {game_name} استارت خورد.\n\n👇 *فقط ۸ نفر منتخب* مجاز به ورود هستند:\n{room_link}\n\n⚠️ *نکته:* این لینک موقتی است و بعد از شروع بازی پاک می‌شود.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
                game_rooms[game_name]["players"] = []
            else:
                bot.send_message(call.message.chat.id, "❌ متأسفم، تمام اتاق‌های گیم پر هستند.")
        else:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            bot.answer_callback_query(call.id, "وارد اتاق شدید ✅")
    else:
        bot.answer_callback_query(call.id, "شما قبلاً ثبت‌نام کرده‌اید! ⚠️")

if __name__ == "__main__":
    init_db()
    keep_alive()
    bot.infinity_polling()