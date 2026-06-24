# telegram_bot_render.py - نسخه ساده و مستقل برای Render با SQLite

import telebot
import sqlite3
import jdatetime
import os
import json
import time
from datetime import datetime

TOKEN = "8705261999:AAF34fID3LoF0_yiXVGKiwyStWNtb6zUIwo"
bot = telebot.TeleBot(TOKEN)

user_member_ids = {}

# ===== اتصال به دیتابیس SQLite (فایل fund.db) =====
DB_PATH = "fund.db"

def get_db_connection():
    """دریافت اتصال به دیتابیس"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================
# ===== کیبوردها =====
# ============================================================
def get_main_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        telebot.types.KeyboardButton("1️⃣ ثبت واریزی"),
        telebot.types.KeyboardButton("2️⃣ مانده حساب")
    )
    markup.add(
        telebot.types.KeyboardButton("3️⃣ درخواست وام"),
        telebot.types.KeyboardButton("4️⃣ وضعیت وام")
    )
    markup.add(
        telebot.types.KeyboardButton("5️⃣ راهنمای کامل")
    )
    markup.add(telebot.types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
    return markup

def get_back_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
    return markup

def get_cancel_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("❌ لغو"))
    return markup

# ============================================================
# ===== هندلرها =====
# ============================================================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id in user_member_ids:
        bot.reply_to(message, f"👋 خوش برگشتید!", reply_markup=get_main_keyboard())
        return
    
    msg = bot.reply_to(
        message,
        "🤖 **به ربات خوش آمدید!**\n📌 لطفاً کد عضویت خود را وارد کنید:",
        reply_markup=get_cancel_keyboard()
    )
    bot.register_next_step_handler(msg, process_code)

def process_code(message):
    user_id = message.from_user.id
    code = message.text.strip()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE id = ? AND is_active = 1", (code,))
        member = cursor.fetchone()
        conn.close()
        
        if member:
            user_member_ids[user_id] = code
            bot.reply_to(message, f"✅ کد عضویت {code} تأیید شد!", reply_markup=get_main_keyboard())
        else:
            bot.reply_to(message, "❌ کد عضویت یافت نشد!", reply_markup=get_cancel_keyboard())
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {str(e)}")

@bot.message_handler(func=lambda m: m.text == "🔙 بازگشت به منوی اصلی")
def back_to_main(message):
    bot.reply_to(message, "🔙 به منوی اصلی بازگشتید.", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: m.text == "1️⃣ ثبت واریزی" or m.text == "1")
def register_start(message):
    bot.reply_to(message, "📝 ثبت واریزی جدید\n\nاین بخش فعال است.", reply_markup=get_back_keyboard())

@bot.message_handler(func=lambda m: m.text == "2️⃣ مانده حساب" or m.text == "2")
def balance_handler(message):
    bot.reply_to(message, "📊 مانده حساب\n\nدر حال به‌روزرسانی...", reply_markup=get_back_keyboard())

@bot.message_handler(func=lambda m: m.text == "3️⃣ درخواست وام" or m.text == "3")
def loan_start(message):
    bot.reply_to(message, "💰 درخواست وام\n\nاین بخش فعال است.", reply_markup=get_back_keyboard())

@bot.message_handler(func=lambda m: m.text == "4️⃣ وضعیت وام" or m.text == "4")
def loan_status_handler(message):
    bot.reply_to(message, "📊 وضعیت وام\n\nدر حال به‌روزرسانی...", reply_markup=get_back_keyboard())

@bot.message_handler(func=lambda m: m.text == "5️⃣ راهنمای کامل" or m.text == "5")
def help_handler(message):
    text = "📖 راهنمای ربات\n1️⃣ ثبت واریزی\n2️⃣ مانده حساب\n3️⃣ درخواست وام\n4️⃣ وضعیت وام"
    bot.reply_to(message, text, reply_markup=get_back_keyboard())

@bot.message_handler(func=lambda m: True)
def unknown_handler(message):
    bot.reply_to(message, "❌ گزینه نامعتبر!", reply_markup=get_main_keyboard())

# ============================================================
# ===== اجرا =====
# ============================================================
if __name__ == "__main__":
    print("🤖 ربات در حال اجرا...")
    try:
        bot.remove_webhook()
    except:
        pass
    bot.polling(none_stop=True, interval=3)
