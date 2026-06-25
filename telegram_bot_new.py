# telegram_bot_new.py - ربات جدید با توکن جدید

import telebot
import sqlite3
import os
import time
import jdatetime

# ===== توکن جدید =====
TOKEN = "8848190789:AAETgpHaD3rx2tELf9G2IumYNljMdms28mw"
bot = telebot.TeleBot(TOKEN)

# ===== دیتابیس =====
DB_PATH = "fund.db"

def get_db():
    """دریافت اتصال به دیتابیس"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ خطا در اتصال به دیتابیس: {e}")
        return None

# ===== کیبوردها =====
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

# ===== ذخیره کد عضویت کاربران =====
user_member_ids = {}

# ============================================================
# ===== هندلر /start =====
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
        "🤖 **به ربات صندوق قرض الحسنه ۱۴ معصوم خوش آمدید!**\n\n"
        "📌 لطفاً **کد عضویت** خود را وارد کنید.",
        reply_markup=telebot.types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_code)

# ============================================================
# ===== دریافت کد عضویت =====
# ============================================================
def process_code(message):
    user_id = message.from_user.id
    code = message.text.strip()
    
    try:
        conn = get_db()
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
                f"❌ کد عضویت {code} یافت نشد!",
                reply_markup=telebot.types.ReplyKeyboardRemove()
            )
            msg = bot.reply_to(message, "📝 لطفاً دوباره کد خود را وارد کنید:")
            bot.register_next_step_handler(msg, process_code)
            
    except Exception as e:
        print(f"❌ خطا: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}")

# ============================================================
# ===== مانده حساب =====
# ============================================================
@bot.message_handler(func=lambda m: m.text == "2️⃣ مانده حساب" or m.text == "2")
def balance_handler(message):
    user_id = message.from_user.id
    
    if user_id not in user_member_ids:
        bot.reply_to(message, "❌ ابتدا کد عضویت خود را وارد کنید!", reply_markup=get_main_keyboard())
        return
    
    try:
        code = user_member_ids[user_id]
        conn = get_db()
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
            
            bot.reply_to(message, text, reply_markup=get_main_keyboard())
        else:
            bot.reply_to(message, "❌ عضو یافت نشد!", reply_markup=get_main_keyboard())
            
    except Exception as e:
        print(f"❌ خطا: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}")

# ============================================================
# ===== پیام‌های نامشخص =====
# ============================================================
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
    print("🤖 ربات جدید صندوق قرض‌الحسنه ۱۴ معصوم")
    print("📱 شناسه: @" + "NEW_BOT_USERNAME")
    print("✅ در حال اجرا...")
    print("=" * 60)
    
    # بررسی دیتابیس
    if os.path.exists(DB_PATH):
        print(f"✅ فایل دیتابیس {DB_PATH} پیدا شد")
    else:
        print(f"⚠️ فایل دیتابیس {DB_PATH} پیدا نشد!")
    
    # پاک کردن webhook
    try:
        bot.remove_webhook()
        print("✅ Webhook پاک شد")
    except Exception as e:
        print(f"⚠️ خطا: {e}")
    
    # شروع
    print("🚀 منتظر پیام‌ها...")
    bot.polling(none_stop=True, interval=3)
