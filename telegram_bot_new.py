# telegram_bot_new.py - نسخه نهایی با Flask

import telebot
import sqlite3
import os
import time
import jdatetime
from flask import Flask
import threading

# ===== توکن =====
TOKEN = "8848190789:AAETgpHaD3rx2tELf9G2IumYNljMdms28mw"
bot = telebot.TeleBot(TOKEN)

# ===== وب سرور برای Render =====
app = Flask(__name__)

@app.route('/')
def home():
    return "ربات فعال است", 200

def run_web():
    app.run(host='0.0.0.0', port=10000)

# ===== دیتابیس =====
DB_PATH = "fund.db"

def get_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ خطا: {e}")
        return None

# ===== کیبورد =====
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
    return markup

user_member_ids = {}

# ============================================================
# ===== start =====
# ============================================================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id in user_member_ids:
        bot.reply_to(message, "خوش برگشتی!", reply_markup=get_main_keyboard())
        return
    msg = bot.reply_to(message, "کد عضويت خود را وارد کنيد:")
    bot.register_next_step_handler(msg, process_code)

# ============================================================
# ===== کد عضویت =====
# ============================================================
def process_code(message):
    user_id = message.from_user.id
    code = message.text.strip()
    try:
        conn = get_db()
        if not conn:
            bot.reply_to(message, "❌ خطا در دیتابیس!")
            return
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM members WHERE id = ? AND is_active = 1", (code,))
        member = cursor.fetchone()
        conn.close()
        if member:
            user_member_ids[user_id] = code
            bot.reply_to(message, f"✅ کد {code} تایید شد!", reply_markup=get_main_keyboard())
        else:
            bot.reply_to(message, "❌ کد اشتباه است!")
            msg = bot.reply_to(message, "دوباره کد را وارد کنيد:")
            bot.register_next_step_handler(msg, process_code)
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")

# ============================================================
# ===== مانده حساب =====
# ============================================================
@bot.message_handler(func=lambda m: m.text == "2️⃣ مانده حساب" or m.text == "2")
def balance_handler(message):
    user_id = message.from_user.id
    if user_id not in user_member_ids:
        bot.reply_to(message, "ابتدا کد عضويت خود را وارد کنيد!", reply_markup=get_main_keyboard())
        return
    try:
        code = user_member_ids[user_id]
        conn = get_db()
        if not conn:
            bot.reply_to(message, "❌ خطا در دیتابیس!")
            return
        cursor = conn.cursor()
        cursor.execute("SELECT name, initial_accumulated FROM members WHERE id = ?", (code,))
        member = cursor.fetchone()
        conn.close()
        if member:
            today = jdatetime.date.today()
            month_name = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                         "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"][today.month - 1]
            text = f"📊 مانده حساب شما\n\n"
            text += f"نام: {member['name']}\n"
            text += f"تاریخ: {today.strftime('%Y/%m/%d')} ({month_name})\n\n"
            text += f"💰 انباشته: {member['initial_accumulated']:,} ریال\n"
            bot.reply_to(message, text, reply_markup=get_main_keyboard())
        else:
            bot.reply_to(message, "❌ عضو یافت نشد!", reply_markup=get_main_keyboard())
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")

# ============================================================
# ===== پیام‌های دیگر =====
# ============================================================
@bot.message_handler(func=lambda m: m.text == "1️⃣ ثبت واریزی" or m.text == "1")
def register_start(message):
    bot.reply_to(message, "📝 در حال توسعه...", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: m.text == "3️⃣ درخواست وام" or m.text == "3")
def loan_start(message):
    bot.reply_to(message, "💰 در حال توسعه...", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: m.text == "4️⃣ وضعیت وام" or m.text == "4")
def loan_status_handler(message):
    bot.reply_to(message, "📊 در حال توسعه...", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: m.text == "5️⃣ راهنمای کامل" or m.text == "5")
def help_handler(message):
    bot.reply_to(message, "📖 راهنما به زودی...", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: True)
def unknown_handler(message):
    user_id = message.from_user.id
    if user_id not in user_member_ids:
        bot.reply_to(message, "ابتدا کد عضويت خود را وارد کنيد!", reply_markup=get_main_keyboard())
        return
    bot.reply_to(message, "❌ گزینه نامعتبر!", reply_markup=get_main_keyboard())

# ============================================================
# ===== اجرا =====
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 ربات جدید صندوق قرض‌الحسنه ۱۴ معصوم")
    print("✅ در حال اجرا...")
    print("=" * 60)
    
    if os.path.exists(DB_PATH):
        print(f"✅ دیتابیس پیدا شد")
    else:
        print(f"⚠️ دیتابیس پیدا نشد!")
    
    try:
        bot.remove_webhook()
        print("✅ Webhook پاک شد")
    except:
        pass
    
    # اجرای وب سرور
    print("🚀 وب سرور روی پورت 10000...")
    threading.Thread(target=run_web, daemon=True).start()
    
    print("🚀 ربات در حال اجرا...")
    bot.polling(none_stop=True, interval=3)
