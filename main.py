import os
import time
import sqlite3
from threading import Thread
from flask import Flask
import telebot
from telebot import types

# وارد کردن تنظیمات و دیتابیس از فایل‌های جدید
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
used_rooms = []

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    if not database.get_user(user_id):
        conn = sqlite3.connect("mafia.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
        conn.close()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_game = types.KeyboardButton("🕹️ شروع بازی آنلاین")
    btn_profile = types.KeyboardButton("👤 پروفایل")
    btn_wallet = types.KeyboardButton("💰 کیف پول")
    btn_topup = types.KeyboardButton("💳 شارژ حساب")
    markup.add(btn_game, btn_profile)
    markup.add(btn_wallet, btn_topup)

    bot.send_message(message.chat.id, "🃏 به ربات مدیریت بازی مافیا خوش آمدید!\n\nلطفاً از منوی پایین استفاده کنید:", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "💰 کیف پول")
def wallet(message):
    user = database.get_user(message.from_user.id)
    if user:
        bot.reply_to(message, f"💰 موجودی شما: {user[3]} سکه", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "💳 شارژ حساب")
def topup(message):
    text = (f"💳 برای شارژ حساب، مبلغ مورد نظر را به شماره زیر واریز کنید:\n\n"
            f"🔢 شماره کارت: `{config.CARD_NUMBER}`\n"
            f"👤 نام صاحب حساب: {config.CARD_NAME}\n\n"
            f"پس از واریز، رسید را به {config.SUPPORT_USERNAME} ارسال کنید.")
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "👤 پروفایل")
def show_profile(message):
    user_id = message.from_user.id
    u_data = database.get_user(user_id)
    if not u_data: return
    name, gender, wins, losses, warns, ban_until = u_data[1], u_data[2], u_data[4], u_data[5], u_data[6], u_data[7]
    status = "🟢 فعال و آماده بازی"
    if ban_until and ban_until > time.time():
        status = "🚫 در بازداشتگاه است (بن ۲۴ ساعته)"
    elif warns > 0:
        status = f"⚠️ در معرض خطر ( {warns} اخطار دارد)"

    profile_text = (f"─── ⋆ 🃏 ⋆ ───\n✨ پروفایل بازیکن\n────────────────\n👤 نام: {name}\n🛡️ وضعیت: {status}\n────────────────\n🏆 برد: {wins} | ❌ باخت: {losses}\n🌟 رنک: {'لجند 👑' if wins > 20 else 'مبتدی 🌱'}\n────────────────")
    bot.reply_to(message, profile_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🕹️ شروع بازی آنلاین")
def game_selection(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton("🌌 زودیاک", callback_data="join_زودیاک"),
               types.InlineKeyboardButton("🌑 شب مافیا", callback_data="join_شب مافیا"),
               types.InlineKeyboardButton("🎩 پدرخوانده", callback_data="join_پدرخوانده"),
               types.InlineKeyboardButton("🏆 کلاسیک پیشرفته", callback_data="join_کلاسیک پیشرفته")]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "🎯 مدل بازی مورد نظر خود را انتخاب کنید:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("join_"))
def join_game(call):
    game_name = call.data.split("_")[1]
    user = call.from_user
    u_data = database.get_user(user.id)
    if u_data and u_data[7] and u_data[7] > time.time():
        bot.answer_callback_query(call.id, "❌ تو فعلاً توی زندانی!", show_alert=True)
        return
    if user.first_name not in game_rooms[game_name]["players"]:
        game_rooms[game_name]["players"].append(user.first_name)
        count = len(game_rooms[game_name]["players"])
        players_list = "\n".join([f"🔹 {p}" for p in game_rooms[game_name]["players"]])
        text = (f"🎮 اتاق انتظار: {game_name}\n────────────────\n👥 بازیکنان حاضر:\n{players_list}\n────────────────\n⏳ تعداد: {count} / 8")
        if count >= 8:
            available_rooms = [r for r in config.ROOM_LINKS if r not in used_rooms]
            if available_rooms:
                room_link = available_rooms[0]
                used_rooms.append(room_link)
                bot.edit_message_text(f"🚀 تعداد بازیکنان تکمیل شد!\n\n🎮 بازی {game_name} استارت خورد.\n\n👇 فقط ۸ نفر منتخب مجاز به ورود هستند:\n{room_link}", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
                game_rooms[game_name]["players"] = []
            else:
                bot.send_message(call.message.chat.id, "❌ تمام اتاق‌های گیم پر هستند.")
        else:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            bot.answer_callback_query(call.id, "وارد اتاق شدید ✅")
    else:
        bot.answer_callback_query(call.id, "شما قبلاً ثبت‌نام کرده‌اید! ⚠️")

@bot.message_handler(commands=['reset_room'])
def reset_room(message):
    if message.from_user.id == config.ADMIN_ID:
        global used_rooms
        used_rooms = [] 
        bot.send_message(message.chat.id, "✅ تمام اتاق‌های گیم ریست شدند.")

@bot.message_handler(func=lambda message: True)
def anti_toxic(message):
    user_id = message.from_user.id
    text = message.text.lower() if message.text else ""
    if any(word in text for word in config.BAD_WORDS):
        user = database.get_user(user_id)
        if user:
            warns = user[6] if user[6] else 0
            warns += 1
            database.update_user_data(user_id, "warnings", warns)
            if warns < 3:

                bot.reply_to(message, f"⚠️ {message.fromuser.first_name} عزیز!\nبی‌ادبی ممنوع است.\n🔴 اخطار {warns} از ۳", parse_mode="Markdown")
            else:
                ban_time = int(time.time()) + (24 * 3600)
                database.update_user_data(user_id, "ban_until", ban_time)
                try:
                    bot.ban_chat_member(message.chat.id, user_id)
                    bot.send_message(message.chat.id, f"🚫 کاربر {message.from_user.first_name} به دلیل تخلف، ۲۴ ساعت به زندان منتقل شد! ⛓️")
                except: pass
                database.update_user_data(user_id, "warnings", 0)

if _name == "__main__":
    keep_alive()
    bot.infinity_polling()
