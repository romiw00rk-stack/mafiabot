```python
import os
import sqlite3
from threading import Thread
from flask import Flask
import telebot
from telebot import types

# --- Flask for Render ---
app = Flask('')
@app.route('/')
def home(): 
    return "Bot is alive!"

def run():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# --- Database System ---
def init_db():
    conn = sqlite3.connect("mafia.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            gender TEXT DEFAULT 'نامشخص',
            coins INTEGER DEFAULT 100,
            xp INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0
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
                     (user_id, username, 'نامشخص', 100, 0, 0, 0))
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

# --- Bot Setup ---
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

# --- Profile Section ---
@bot.message_handler(func=lambda message: message.text == "👤 پروفایل")
def show_profile(message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    user_data = get_or_create_user(user_id, username)
    
    name, gender, coins, xp, wins, losses = user_data[1], user_data[2], user_data[3], user_data[4], user_data[5], user_data[6]
    total_games = wins + losses
    win_rate = int((wins / total_games) * 100) if total_games > 0 else 0
    level = "شهروند مبتدی 👤" if xp < 100 else "کارآگاه زبده 🔍" if xp < 500 else "پدرخوانده 🕶️"
        
    profile_text = f"""
👤 *پروفایل کاربری شما*
━━━━━━━━━━━━━━━━━━
🏷️ *نام:* {name}
🚻 *جنسیت:* {gender}
🆔 *شناسه:* `{user_id}`
🎖️ *سطح:* {level}

📊 *آمار بازی‌ها:*

🎮 کل بازی‌ها: {total_games}
🏆 تعداد برد: {wins} ({win_rate}٪)
❌ تعداد باخت: {losses}

💰 *دارایی‌ها:*
🪙 سکه: {coins}
🌟 امتیاز (XP): {xp}
━━━━━━━━━━━━━━━━━━
"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_name = types.InlineKeyboardButton("تغییر نام ✏️", callback_data="edit_name")
    btn_gender = types.InlineKeyboardButton("تغییر جنسیت ⚧️", callback_data="edit_gender")
    btn_close = types.InlineKeyboardButton("بستن ❌", callback_data="close_profile")
    markup.add(btn_name, btn_gender)
    markup.add(btn_close)
    
    bot.reply_to(message, profile_text, parse_mode="Markdown", reply_markup=markup)

# --- Callback Handlers ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    
    if call.data == "close_profile":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "بسته شد.")
        
    elif call.data == "edit_name":
        bot.answer_callback_query(call.id, "لطفاً نام جدید خود را بفرستید:")
        msg = bot.send_message(call.message.chat.id, "✍️ نام جدید خود را بنویسید و ارسال کنید:")
        bot.register_next_step_handler(msg, save_new_name)
        
    elif call.data == "edit_gender":
        markup = types.InlineKeyboardMarkup()
        btn_boy = types.InlineKeyboardButton("پسر 👦", callback_data="set_boy")
        btn_girl = types.InlineKeyboardButton("دختر 👧", callback_data="set_girl")
        markup.add(btn_boy, btn_girl)
        bot.edit_message_text("لطفاً جنسیت خود را انتخاب کنید:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "set_boy":
        update_user_data(user_id, "gender", "پسر 👦")
        bot.answer_callback_query(call.id, "جنسیت با موفقیت تغییر کرد ✅")
        bot.send_message(call.message.chat.id, "پروفایل شما آپدیت شد. برای مشاهده مجدد دکمه پروفایل را بزنید.")
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif call.data == "set_girl":
        update_user_data(user_id, "gender", "دختر 👧")
        bot.answer_callback_query(call.id, "جنسیت با موفقیت تغییر کرد ✅")
        bot.send_message(call.message.chat.id, "پروفایل شما آپدیت شد. برای مشاهده مجدد دکمه پروفایل را بزنید.")
        bot.delete_message(call.message.chat.id, call.message.message_id)

def save_new_name(message):
    user_id = message.from_user.id
    new_name = message.text
    update_user_data(user_id, "username", new_name)
    bot.send_message(message.chat.id, f"✅ نام شما با موفقیت به {new_name} تغییر یافت.")
    show_profile(message)

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, f"بخش «{message.text}» به زودی فعال می‌شود.", reply_markup=get_main_keyboard())

if __name__ == "__main__":
    init_db()
    keep_alive()
    print("Bot is starting...")
    bot.infinity_polling()
```



