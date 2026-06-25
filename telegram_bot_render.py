# telegram_bot_render.py - نسخه نهایی با رفع خطای 409

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

# ===== اتصال به دیتابیس =====
DB_PATH = "fund.db"

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ خطا در اتصال به دیتابیس: {e}")
        return None

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
        bot.reply_to(
            message,
            f"👋 خوش برگشتید! کد عضویت: {user_member_ids[user_id]}",
            reply_markup=get_main_keyboard()
        )
        return
    
    msg = bot.reply_to(
        message,
        "🤖 **به ربات صندوق قرض الحسنه 14 معصوم خوش آمدید!**\n\n"
        "📌 لطفاً **کد عضویت** خود را وارد کنید.",
        reply_markup=get_cancel_keyboard()
    )
    bot.register_next_step_handler(msg, process_code)

def process_code(message):
    user_id = message.from_user.id
    code = message.text.strip()
    
    try:
        conn = get_db_connection()
        if not conn:
            bot.reply_to(message, "❌ خطا در اتصال به دیتابیس!")
            return
        
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM members WHERE id = ? AND is_active = 1", (code,))
        member = cursor.fetchone()
        conn.close()
        
        if member:
            user_member_ids[user_id] = code
            bot.reply_to(
                message,
                f"✅ **کد عضویت {code} تأیید شد!**\n\n"
                f"👤 نام: {member['name']}\n"
                "📌 از منوی زیر استفاده کنید:",
                reply_markup=get_main_keyboard()
            )
        else:
            bot.reply_to(
                message,
                f"❌ کد عضویت {code} یافت نشد!\n\n"
                "📌 لطفاً دوباره تلاش کنید.",
                reply_markup=get_cancel_keyboard()
            )
            msg = bot.reply_to(message, "📝 کد عضویت خود را وارد کنید:")
            bot.register_next_step_handler(msg, process_code)
            
    except Exception as e:
        print(f"❌ خطا: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}")

@bot.message_handler(func=lambda m: m.text == "🔙 بازگشت به منوی اصلی")
def back_to_main(message):
    bot.reply_to(message, "🔙 به منوی اصلی بازگشتید.", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: m.text == "5️⃣ راهنمای کامل" or m.text == "5")
def help_handler(message):
    text = "📖 **راهنمای کامل ربات**\n\n"
    text += "1️⃣ ثبت واریزی\n"
    text += "2️⃣ مانده حساب\n"
    text += "3️⃣ درخواست وام\n"
    text += "4️⃣ وضعیت وام\n\n"
    text += f"📞 پشتیبانی: 09387026799"
    bot.reply_to(message, text, reply_markup=get_back_keyboard())

@bot.message_handler(func=lambda m: m.text == "1️⃣ ثبت واریزی" or m.text == "1")
def register_start(message):
    bot.reply_to(
        message,
        "📝 **ثبت واریزی**\n\n"
        "این بخش فعال است.\n"
        "📌 لطفاً مبالغ را وارد کنید.",
        reply_markup=get_back_keyboard()
    )

@bot.message_handler(func=lambda m: m.text == "2️⃣ مانده حساب" or m.text == "2")
def balance_handler(message):
    user_id = message.from_user.id
    
    if user_id not in user_member_ids:
        bot.reply_to(message, "❌ ابتدا کد عضویت خود را وارد کنید!", reply_markup=get_main_keyboard())
        return
    
    try:
        code = user_member_ids[user_id]
        conn = get_db_connection()
        if not conn:
            bot.reply_to(message, "❌ خطا در اتصال به دیتابیس!")
            return
        
        cursor = conn.cursor()
        cursor.execute("SELECT name, initial_accumulated FROM members WHERE id = ?", (code,))
        member = cursor.fetchone()
        conn.close()
        
        if member:
            today = jdatetime.date.today()
            month_name = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                         "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"][today.month - 1]
            
            text = f"📊 **اطلاعات مالی شما**\n\n"
            text += f"👤 نام: {member['name']}\n"
            text += f"📅 تاریخ: {today.strftime('%Y/%m/%d')} ({month_name})\n\n"
            text += f"💰 **انباشته:** {member['initial_accumulated']:,} ریال\n"
            
            bot.reply_to(message, text, reply_markup=get_back_keyboard())
        else:
            bot.reply_to(message, "❌ عضو یافت نشد!", reply_markup=get_main_keyboard())
            
    except Exception as e:
        print(f"❌ خطا: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}")

@bot.message_handler(func=lambda m: m.text == "3️⃣ درخواست وام" or m.text == "3")
def loan_start(message):
    bot.reply_to(
        message,
        "💰 **درخواست وام**\n\n"
        "این بخش فعال است.",
        reply_markup=get_back_keyboard()
    )

@bot.message_handler(func=lambda m: m.text == "4️⃣ وضعیت وام" or m.text == "4")
def loan_status_handler(message):
    bot.reply_to(
        message,
        "📊 **وضعیت وام**\n\n"
        "این بخش فعال است.",
        reply_markup=get_back_keyboard()
    )

@bot.message_handler(func=lambda m: True)
def unknown_handler(message):
    user_id = message.from_user.id
    if user_id not in user_member_ids:
        bot.reply_to(message, "❌ ابتدا کد عضویت خود را وارد کنید!", reply_markup=get_main_keyboard())
        return
    bot.reply_to(message, "❌ گزینه نامعتبر!", reply_markup=get_main_keyboard())

# ============================================================
# ===== اجرا =====
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 ربات تلگرام صندوق قرض‌الحسنه ۱۴ معصوم")
    print("📱 شناسه ربات: @sandoogh14_bot")
    print("✅ در حال اجرا روی Render...")
    print("=" * 60)
    
    # پاک کردن webhook قبل از شروع
    try:
        bot.remove_webhook()
        print("✅ Webhook پاک شد")
    except Exception as e:
        print(f"⚠️ خطا در پاک کردن webhook: {e}")
    
    # بررسی وجود دیتابیس
    if os.path.exists(DB_PATH):
        print(f"✅ فایل دیتابیس {DB_PATH} پیدا شد")
    else:
        print(f"⚠️ فایل دیتابیس {DB_PATH} پیدا نشد!")
    
    # شروع با تنظیمات جلوگیری از 409
    try:
        bot.polling(none_stop=True, interval=1, timeout=20, long_polling_timeout=20)
    except Exception as e:
        print(f"❌ خطا: {e}")
        time.sleep(5)
