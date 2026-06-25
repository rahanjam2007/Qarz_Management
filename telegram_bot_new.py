import telebot
import sqlite3
import os
import re
import jdatetime
from flask import Flask
from datetime import datetime
import threading

TOKEN = "8848190789:AAETgPhA03rX2tELF9G2IumYN1jMds28mw"
bot = telebot.TeleBot(TOKEN)

# ---
# وب سرور
app = Flask(__name__)

@app.route('/')
def home():
    return "200, ربات فعال است"

def run_web():
    app.run(host='0.0.0.0', port=10000)

# ===== دیتابیس =====
DB_PATH = os.path.join(os.path.dirname(__file__), "fund_new.db")

print(f"✅ ربات به دیتابیس متصل شد: {DB_PATH}")

def get_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ خطا در اتصال به دیتابیس: {e}")
        return None

# ---
# تابع تشخیص ماه مالی
def get_financial_month_from_date(date_str):
    try:
        if not date_str:
            return None

        date_str = str(date_str).strip()
        date_str = re.sub(r'[^0-9/\-]', '', date_str)

        if '/' in date_str:
            parts = date_str.split('/')
        elif '-' in date_str:
            parts = date_str.split('-')
        else:
            return None

        if len(parts) != 3:
            return None

        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])

        MONTH_NAMES = {
            1: "فروردین", 2: "اردیبهشت", 3: "خرداد",
            4: "تیر", 5: "مرداد", 6: "شهریور",
            7: "مهر", 8: "آبان", 9: "آذر",
            10: "دی", 11: "بهمن", 12: "اسفند"
        }

        if day >= 25:
            target_month = month
        elif day <= 15:
            if month == 1:
                target_month = 12
            else:
                target_month = month - 1
        else:
            if month == 12:
                target_month = 1
            else:
                target_month = month + 1

        return MONTH_NAMES.get(target_month)

    except Exception as e:
        print(f"❌ خطا در تشخیص ماه: {e}")
        return None

def format_rial(amount):
    return f"{amount:,}"

# ===== دستورات ربات =====
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "سلام! به ربات صندوق قرض‌الحسنه ۱۴ معصوم خوش آمدید.\n\nبرای ثبت واریزی، لطفاً اطلاعات را به صورت زیر وارد کنید:\n\n`مبلغ کل, مبلغ اشتراک, مبلغ قسط`\n\nمثال:\n`15000000, 5000000, 10000000`")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # پردازش متن پیام
        text = message.text.strip()
        parts = text.split(',')

        if len(parts) != 3:
            bot.reply_to(message, "❌ فرمت اشتباه! لطفاً به این شکل وارد کنید:\n\n`مبلغ کل, مبلغ اشتراک, مبلغ قسط`\n\nمثال:\n`15000000, 5000000, 10000000`")
            return

        total = int(parts[0].strip())
        subscription = int(parts[1].strip())
        installment = int(parts[2].strip())

        if total < subscription + installment:
            bot.reply_to(message, "❌ مجموع اشتراک و قسط نمی‌تواند از مبلغ کل بیشتر باشد!")
            return

        # پیدا کردن کاربر
        user_id = message.from_user.id
        username = message.from_user.username or "بدون نام"

        conn = get_db()
        if not conn:
            bot.reply_to(message, "❌ خطا در اتصال به دیتابیس!")
            return

        cursor = conn.cursor()

        # پیدا کردن عضو با تلگرام آیدی
        cursor.execute("SELECT id, name FROM members WHERE telegram_id = ?", (user_id,))
        member = cursor.fetchone()

        if not member:
            # اگر عضو پیدا نشد، با نام کاربری ثبت کن
            cursor.execute("SELECT id, name FROM members WHERE name = ?", (username,))
            member = cursor.fetchone()

        if not member:
            bot.reply_to(message, f"❌ کاربری با نام {username} یافت نشد!\nلطفاً ابتدا در سیستم ثبت‌نام کنید.")
            conn.close()
            return

        member_id = member['id']
        member_name = member['name']

        # تاریخ امروز
        today = jdatetime.date.today()
        date_str = today.strftime("%Y/%m/%d")

        # تشخیص ماه مالی
        financial_month = get_financial_month_from_date(date_str)

        # ثبت تراکنش
        cursor.execute("""
            INSERT INTO transactions (member_id, date, amount_total, amount_subscription, amount_installment, confirmed, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (member_id, date_str, total, subscription, installment, 0, 'bot'))

        conn.commit()
        conn.close()

        # پاسخ به کاربر
        response = f"✅ **واریزی با موفقیت ثبت شد!**\n\n"
        response += f"👤 عضو: {member_name}\n"
        response += f"📅 تاریخ: {date_str}\n"
        if financial_month:
            response += f"📌 ماه مالی: **{financial_month}**\n"
        response += f"💰 مبلغ کل: {format_rial(total)} ریال\n"
        response += f"📊 اشتراک: {format_rial(subscription)} ریال\n"
        response += f"💳 قسط: {format_rial(installment)} ریال\n\n"
        response += f"⏳ **وضعیت:** در انتظار تأیید مدیر"

        bot.reply_to(message, response, parse_mode='Markdown')

    except ValueError:
        bot.reply_to(message, "❌ لطفاً اعداد را به درستی وارد کنید!")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {str(e)}")

# ===== اجرا =====
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 ربات کامل صندوق قرض‌الحسنه ۱۴ معصوم")
    print(f"📱 شناسه: @masum_sandogh14_bot")
    print("✅ در حال اجرا...")
    print("=" * 60)

    # چک کردن دیتابیس
    db_path = DB_PATH
    if os.path.exists(db_path):
        print(f"✅ دیتابیس پیدا شد: {db_path}")
    else:
        print(f"⚠️ دیتابیس در {db_path} پیدا نشد!")

    # پاک کردن Webhook
    try:
        bot.remove_webhook()
        print("✅ Webhook پاک شد")
    except:
        pass

    # اجرای وب سرور در ترد جداگانه
    thread = threading.Thread(target=run_web)
    thread.daemon = True
    thread.start()
    print("🚀 وب سرور روی پورت 10000...")

    # اجرای ربات
    print("🚀 ربات در حال اجرا...")
    bot.polling(none_stop=True, interval=0)
