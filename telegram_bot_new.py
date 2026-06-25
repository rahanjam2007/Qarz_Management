# telegram_bot_new.py - نسخه نهایی با تشخیص ماه مالی

import telebot
import sqlite3
import os
import time
import jdatetime
from datetime import datetime
from flask import Flask
import threading
import re
import json
import sys

# ===== اضافه کردن مسیر پروژه برای import =====
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ===== توکن =====
TOKEN = "8848190789:AAETgpHaD3rx2tELf9G2IumYNljMdms28mw"
bot = telebot.TeleBot(TOKEN)

# ===== وب سرور =====
app = Flask(__name__)

@app.route('/')
def home():
    return "ربات فعال است", 200

def run_web():
    app.run(host='0.0.0.0', port=10000)

# ===== دیتابیس =====
DB_PATH = "fund_new.db"

def get_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ خطا: {e}")
        return None

# ===== تابع تشخیص ماه مالی =====
def get_financial_month_from_date(date_str):
    """تشخیص ماه مالی بر اساس تاریخ شمسی"""
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
        
        month = int(parts[1])
        day = int(parts[2])
        
        month_names = {
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
        
        return month_names.get(target_month)
        
    except:
        return None

def format_rial(value):
    return f"{value:,}"

def save_chat_id(phone, chat_id):
    if not phone:
        return
    data = {}
    if os.path.exists("user_chat_ids.json"):
        try:
            with open("user_chat_ids.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = {}
    data[str(phone)] = chat_id
    with open("user_chat_ids.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_chat_id(phone):
    if not phone:
        return None
    if os.path.exists("user_chat_ids.json"):
        try:
            with open("user_chat_ids.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(str(phone))
        except:
            return None
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

user_member_ids = {}
user_states = {}
user_temp_data = {}
SUPPORT_PHONE = "09387026799"

# ============================================================
# ===== هندلر بازگشت =====
# ============================================================
@bot.message_handler(func=lambda m: m.text == "🔙 بازگشت به منوی اصلی")
def back_to_main(message):
    user_id = message.from_user.id
    if user_id in user_states:
        user_states[user_id] = 'main'
    if user_id in user_temp_data:
        del user_temp_data[user_id]
    bot.reply_to(
        message,
        "🔙 به منوی اصلی بازگشتید.",
        reply_markup=get_main_keyboard()
    )

# ============================================================
# ===== start =====
# ============================================================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    chat_id = user_id
    
    try:
        if user_id in user_member_ids:
            user_states[user_id] = 'main'
            try:
                member_code = user_member_ids[user_id]
                conn = get_db()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT phone FROM members WHERE id = ?", (member_code,))
                    member = cursor.fetchone()
                    conn.close()
                    if member and member['phone']:
                        save_chat_id(member['phone'], chat_id)
            except:
                pass
            bot.reply_to(
                message,
                f"👋 خوش برگشتید! کد عضویت: {user_member_ids[user_id]}",
                reply_markup=get_main_keyboard()
            )
            return
        
        user_states[user_id] = 'get_code'
        msg = bot.reply_to(
            message,
            "🤖 **به ربات صندوق قرض الحسنه 14 معصوم خوش آمدید!**\n\n"
            "📌 لطفاً **کد عضویت** خود را وارد کنید.\n\n"
            "⚠️ اگر کد عضویت ندارید، با پشتیبانی تماس بگیرید:\n"
            f"📞 {SUPPORT_PHONE}",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, process_code)
    except Exception as e:
        print(f"❌ خطا: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}")

def process_code(message):
    user_id = message.from_user.id
    chat_id = user_id
    code = message.text.strip()
    
    try:
        member_id = int(code)
        conn = get_db()
        if not conn:
            bot.reply_to(message, "❌ خطا در دیتابیس!")
            return
        
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, phone FROM members WHERE id = ? AND is_active = 1", (member_id,))
        member = cursor.fetchone()
        conn.close()
        
        if member:
            user_member_ids[user_id] = code
            user_states[user_id] = 'main'
            
            phone = member['phone'] if member['phone'] else None
            if phone:
                save_chat_id(phone, chat_id)
            
            bot.reply_to(
                message,
                f"✅ **کد عضویت {code} تأیید شد!**\n\n"
                f"👤 نام: {member['name']}\n"
                f"📱 شماره همراه: {phone if phone else 'ثبت نشده'}\n\n"
                "📌 از منوی زیر استفاده کنید:",
                reply_markup=get_main_keyboard()
            )
        else:
            bot.reply_to(
                message,
                f"❌ کد عضویت {code} یافت نشد!",
                reply_markup=get_cancel_keyboard()
            )
            msg = bot.reply_to(message, "📝 لطفاً دوباره کد خود را وارد کنید:")
            bot.register_next_step_handler(msg, process_code)
            
    except ValueError:
        bot.reply_to(
            message,
            "❌ کد عضویت باید عدد باشد!",
            reply_markup=get_cancel_keyboard()
        )
        msg = bot.reply_to(message, "📝 کد عضویت خود را وارد کنید:")
        bot.register_next_step_handler(msg, process_code)
    except Exception as e:
        print(f"❌ خطا: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}")

# ============================================================
# ===== راهنما =====
# ============================================================
@bot.message_handler(func=lambda m: m.text == "5️⃣ راهنمای کامل" or m.text == "5")
def help_handler(message):
    text = "📖 **راهنمای کامل ربات**\n\n"
    text += "1️⃣ **ثبت واریزی**\n"
    text += "   مراحل: مبلغ کل، اشتراک، قسط\n\n"
    text += "2️⃣ **مانده حساب**\n"
    text += "   نمایش انباشته و مانده وام\n\n"
    text += "3️⃣ **درخواست وام**\n"
    text += "   مراحل: مبلغ وام، ارسال مدارک\n\n"
    text += "4️⃣ **وضعیت وام**\n"
    text += "   نمایش وضعیت وام فعلی\n\n"
    text += "📌 **نکات مهم:**\n"
    text += "• برای انصراف، دکمه 'لغو' را بزنید.\n"
    text += "• برای تکمیل درخواست وام، کلمه **'تكميل'** را وارد کنید.\n"
    text += f"📞 پشتیبانی: {SUPPORT_PHONE}"
    bot.reply_to(message, text, reply_markup=get_back_keyboard())

# ============================================================
# ===== ثبت واریزی =====
# ============================================================
@bot.message_handler(func=lambda m: m.text == "1️⃣ ثبت واریزی" or m.text == "1")
def register_start(message):
    user_id = message.from_user.id
    try:
        if user_id not in user_member_ids:
            bot.reply_to(message, "❌ ابتدا کد عضویت خود را وارد کنید!", reply_markup=get_main_keyboard())
            return
        
        user_temp_data[user_id] = {'step': 'total', 'total': 0, 'subscription': 0, 'installment': 0}
        user_states[user_id] = 'register'
        
        msg = bot.reply_to(
            message,
            "📝 **ثبت واریزی جدید**\n\n"
            "مرحله 1 از 3:\n"
            "لطفاً **مبلغ کل واریزی** را به ریال وارد کنید.\n\n"
            "مثال: 10000000\n\n"
            "➖ برای انصراف، دکمه 'لغو' را بزنید.",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, process_register_total)
    except Exception as e:
        print(f"❌ خطا: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}")

def process_register_total(message):
    user_id = message.from_user.id
    if message.text == "❌ لغو":
        user_states[user_id] = 'main'
        if user_id in user_temp_data:
            del user_temp_data[user_id]
        bot.reply_to(message, "✅ ثبت واریزی لغو شد.", reply_markup=get_main_keyboard())
        return
    
    try:
        total = int(message.text.replace(',', '').strip())
        if total <= 0:
            bot.reply_to(message, "❌ مبلغ باید بزرگتر از صفر باشد!", reply_markup=get_cancel_keyboard())
            return
        
        user_temp_data[user_id]['total'] = total
        user_temp_data[user_id]['step'] = 'subscription'
        
        msg = bot.reply_to(
            message,
            f"✅ مبلغ کل: {total:,} ریال\n\n"
            "مرحله 2 از 3:\n"
            "لطفاً **مبلغ حق اشتراک** را به ریال وارد کنید.\n\n"
            "مثال: 5000000\n\n"
            "➖ برای انصراف، دکمه 'لغو' را بزنید.",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, process_register_subscription)
    except:
        bot.reply_to(message, "❌ لطفاً عدد وارد کنید!", reply_markup=get_cancel_keyboard())

def process_register_subscription(message):
    user_id = message.from_user.id
    if message.text == "❌ لغو":
        user_states[user_id] = 'main'
        if user_id in user_temp_data:
            del user_temp_data[user_id]
        bot.reply_to(message, "✅ ثبت واریزی لغو شد.", reply_markup=get_main_keyboard())
        return
    
    try:
        subscription = int(message.text.replace(',', '').strip())
        total = user_temp_data[user_id]['total']
        
        if subscription < 0:
            bot.reply_to(message, "❌ مبلغ اشتراک نمی‌تواند منفی باشد!", reply_markup=get_cancel_keyboard())
            return
        if subscription > total:
            bot.reply_to(
                message,
                f"❌ مبلغ اشتراک ({subscription:,} ریال) از مبلغ کل ({total:,} ریال) بیشتر است!",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        user_temp_data[user_id]['subscription'] = subscription
        user_temp_data[user_id]['step'] = 'installment'
        
        remaining = total - subscription
        msg = bot.reply_to(
            message,
            f"✅ مبلغ کل: {total:,} ریال\n"
            f"✅ مبلغ اشتراک: {subscription:,} ریال\n"
            f"📌 باقیمانده: {remaining:,} ریال\n\n"
            "مرحله 3 از 3:\n"
            "لطفاً **مبلغ قسط پرداختی** را به ریال وارد کنید.\n\n"
            "مثال: 2000000\n"
            "(اگر قسطی پرداخت نمی‌کنید، عدد 0 را وارد کنید)\n\n"
            "➖ برای انصراف، دکمه 'لغو' را بزنید.",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, process_register_installment)
    except:
        bot.reply_to(message, "❌ لطفاً عدد وارد کنید!", reply_markup=get_cancel_keyboard())

def process_register_installment(message):
    user_id = message.from_user.id
    if message.text == "❌ لغو":
        user_states[user_id] = 'main'
        if user_id in user_temp_data:
            del user_temp_data[user_id]
        bot.reply_to(message, "✅ ثبت واریزی لغو شد.", reply_markup=get_main_keyboard())
        return
    
    try:
        installment = int(message.text.replace(',', '').strip())
        total = user_temp_data[user_id]['total']
        subscription = user_temp_data[user_id]['subscription']
        
        if installment < 0:
            bot.reply_to(message, "❌ مبلغ قسط نمی‌تواند منفی باشد!", reply_markup=get_cancel_keyboard())
            return
        
        if installment > (total - subscription):
            bot.reply_to(
                message, 
                f"❌ مبلغ قسط ({installment:,} ریال) از باقیمانده ({total - subscription:,} ریال) بیشتر است!\n\n"
                f"📌 لطفاً مبلغ کمتری وارد کنید.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        # ===== ثبت در دیتابیس =====
        member_code = user_member_ids[user_id]
        conn = get_db()
        if not conn:
            bot.reply_to(message, "❌ خطا در دیتابیس!", reply_markup=get_main_keyboard())
            return
        
        cursor = conn.cursor()
        date = jdatetime.date.today().strftime("%Y/%m/%d")
        
        # ===== تشخیص ماه مالی =====
        financial_month = get_financial_month_from_date(date)
        
        cursor.execute("""
            INSERT INTO transactions (member_id, date, amount_total, amount_subscription, amount_installment, confirmed, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (member_code, date, total, subscription, installment, 0, 'bot'))
        conn.commit()
        conn.close()
        
        # پاک کردن داده‌های موقت
        if user_id in user_temp_data:
            del user_temp_data[user_id]
        user_states[user_id] = 'main'
        
        # دریافت نام عضو
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM members WHERE id = ?", (member_code,))
        member = cursor.fetchone()
        conn.close()
        
        month_name = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                     "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"][jdatetime.date.today().month - 1]
        
        summary = f"✅ **واریزی با موفقیت ثبت شد!**\n\n"
        summary += f"👤 عضو: {member['name'] if member else 'نامشخص'}\n"
        summary += f"📅 تاریخ: {date} ({month_name})\n"
        if financial_month:
            summary += f"📌 ماه مالی: **{financial_month}**\n"
        summary += f"💰 مبلغ کل: {total:,} ریال\n"
        summary += f"📊 اشتراک: {subscription:,} ریال\n"
        summary += f"💳 قسط: {installment:,} ریال\n\n"
        summary += f"⏳ **وضعیت:** در انتظار تأیید مدیر\n\n"
        summary += f"🔙 برای بازگشت به منوی اصلی، دکمه زیر را بزنید."
        
        bot.reply_to(message, summary, reply_markup=get_back_keyboard())
        
    except ValueError:
        bot.reply_to(
            message, 
            "❌ لطفاً عدد وارد کنید!\n\n"
            "📌 مثال: 2000000\n"
            "📌 اگر قسطی پرداخت نمی‌کنید، عدد 0 را وارد کنید.",
            reply_markup=get_cancel_keyboard()
        )
    except Exception as e:
        print(f"❌ خطا: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}", reply_markup=get_back_keyboard())

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
        member_code = user_member_ids[user_id]
        conn = get_db()
        if not conn:
            bot.reply_to(message, "❌ خطا در دیتابیس!")
            return
        
        cursor = conn.cursor()
        cursor.execute("SELECT name, initial_accumulated FROM members WHERE id = ?", (member_code,))
        member = cursor.fetchone()
        
        cursor.execute("SELECT remaining_amount FROM loans WHERE member_id = ? AND status = 'active'", (member_code,))
        loan = cursor.fetchone()
        conn.close()
        
        if member:
            today = jdatetime.date.today()
            month_name = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                         "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"][today.month - 1]
            
            loan_remaining = loan['remaining_amount'] if loan else 0
            
            text = f"📊 **اطلاعات مالی شما**\n\n"
            text += f"👤 نام: {member['name']}\n"
            text += f"🆔 کد عضویت: {member_code}\n"
            text += f"📅 تاریخ: {today.strftime('%Y/%m/%d')} ({month_name})\n\n"
            text += f"💰 **انباشته:** {member['initial_accumulated']:,} ریال\n"
            text += f"💳 **مانده وام:** {loan_remaining:,} ریال\n\n"
            
            if loan_remaining > 0:
                text += "📌 وضعیت وام: **فعال**"
            else:
                text += "✅ وضعیت وام: **تسویه شده**"
            
            bot.reply_to(message, text, reply_markup=get_back_keyboard())
        else:
            bot.reply_to(message, "❌ عضو یافت نشد!", reply_markup=get_back_keyboard())
            
    except Exception as e:
        print(f"❌ خطا: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}", reply_markup=get_back_keyboard())

# ============================================================
# ===== درخواست وام =====
# ============================================================
@bot.message_handler(func=lambda m: m.text == "3️⃣ درخواست وام" or m.text == "3")
def loan_start(message):
    user_id = message.from_user.id
    try:
        if user_id not in user_member_ids:
            bot.reply_to(message, "❌ ابتدا کد عضویت خود را وارد کنید!", reply_markup=get_main_keyboard())
            return
        
        user_temp_data[user_id] = {'amount': 0, 'doc_path': None}
        user_states[user_id] = 'loan_amount'
        
        msg = bot.reply_to(
            message,
            "💰 **درخواست وام**\n\n"
            "مرحله 1 از 2:\n"
            "لطفاً **مبلغ وام** مورد نظر را به ریال وارد کنید.\n"
            "مثال: 50000000\n\n"
            "⚠️ حداقل مبلغ: 500,000 ریال\n"
            "⚠️ حداکثر مبلغ: 2 میلیارد ریال\n\n"
            "➖ برای انصراف، دکمه 'لغو' را بزنید.",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, process_loan_amount)
    except Exception as e:
        print(f"❌ خطا: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}")

def process_loan_amount(message):
    user_id = message.from_user.id
    if message.text == "❌ لغو":
        user_states[user_id] = 'main'
        if user_id in user_temp_data:
            del user_temp_data[user_id]
        bot.reply_to(message, "✅ درخواست وام لغو شد.", reply_markup=get_main_keyboard())
        return
    
    try:
        amount = int(message.text.replace(',', '').strip())
        if amount < 500000:
            bot.reply_to(message, "❌ حداقل مبلغ وام 500,000 ریال است.", reply_markup=get_cancel_keyboard())
            return
        if amount > 2000000000:
            bot.reply_to(message, "❌ حداکثر مبلغ وام 2 میلیارد ریال است.", reply_markup=get_cancel_keyboard())
            return
        
        user_temp_data[user_id]['amount'] = amount
        user_states[user_id] = 'loan_document'
        
        msg = bot.reply_to(
            message,
            f"✅ مبلغ وام: {amount:,} ریال\n\n"
            "مرحله 2 از 2:\n"
            "📎 **لطفاً مدارک خود را ارسال کنید** (تصویر یا PDF)\n"
            "📌 برای تکمیل بدون مدرک، کلمه **'تكميل'** را وارد کنید.\n\n"
            "➖ برای انصراف، دکمه 'لغو' را بزنید.",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, process_loan_document)
    except:
        bot.reply_to(message, "❌ لطفاً عدد وارد کنید!", reply_markup=get_cancel_keyboard())

def process_loan_document(message):
    user_id = message.from_user.id
    if message.text == "❌ لغو":
        user_states[user_id] = 'main'
        if user_id in user_temp_data:
            del user_temp_data[user_id]
        bot.reply_to(message, "✅ درخواست وام لغو شد.", reply_markup=get_main_keyboard())
        return
    
    # بررسی کلمه کلیدی "تکمیل"
    text = message.text.strip() if message.text else ""
    complete_words = ['تكميل', 'تکمیل', 'تكمیل', 'تکميل', 'complete', 'تمام', 'پایان']
    is_complete = any(w in text.replace('ي', 'ی').replace('ك', 'ک') for w in complete_words)
    
    if message.document or message.photo:
        # ذخیره فایل
        try:
            doc_folder = "documents"
            if not os.path.exists(doc_folder):
                os.makedirs(doc_folder)
            
            if message.document:
                file_info = bot.get_file(message.document.file_id)
                file_name = message.document.file_name
            else:
                file_info = bot.get_file(message.photo[-1].file_id)
                file_name = f"photo_{message.photo[-1].file_id[:8]}.jpg"
            
            downloaded_file = bot.download_file(file_info.file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{user_member_ids.get(user_id, 'unknown')}_{file_name}"
            file_path = os.path.join(doc_folder, safe_filename)
            with open(file_path, 'wb') as f:
                f.write(downloaded_file)
            
            if user_id in user_temp_data:
                if user_temp_data[user_id].get('doc_path'):
                    user_temp_data[user_id]['doc_path'] += f"|{file_path}"
                else:
                    user_temp_data[user_id]['doc_path'] = file_path
            
            bot.reply_to(
                message,
                f"✅ فایل '{file_name}' دریافت شد.\n"
                f"📌 برای تکمیل، 'تكميل' را وارد کنید.",
                reply_markup=get_cancel_keyboard()
            )
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {str(e)}", reply_markup=get_cancel_keyboard())
    elif is_complete:
        # تکمیل درخواست
        try:
            amount = user_temp_data[user_id]['amount']
            doc_path = user_temp_data[user_id].get('doc_path', '')
            
            member_code = user_member_ids[user_id]
            conn = get_db()
            if not conn:
                bot.reply_to(message, "❌ خطا در دیتابیس!", reply_markup=get_main_keyboard())
                return
            
            cursor = conn.cursor()
            today = jdatetime.date.today()
            year = str(today.year)
            cursor.execute("SELECT COUNT(*) FROM secretariat_requests")
            count = cursor.fetchone()[0] + 1
            secretariat_no = f"{year}-{str(count).zfill(4)}"
            
            cursor.execute("""
                INSERT INTO secretariat_requests (secretariat_no, member_id, amount, doc_path, request_date, source, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (secretariat_no, member_code, amount, doc_path, today.strftime("%Y/%m/%d"), 'bot', 'در انتظار'))
            conn.commit()
            conn.close()
            
            if user_id in user_temp_data:
                del user_temp_data[user_id]
            user_states[user_id] = 'main'
            
            month_name = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                         "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"][today.month - 1]
            
            summary = f"✅ **درخواست وام ثبت شد!**\n\n"
            summary += f"💰 مبلغ: {amount:,} ریال\n"
            summary += f"📅 تاریخ: {today.strftime('%Y/%m/%d')} ({month_name})\n"
            summary += f"📌 شماره پیگیری: {secretariat_no}\n"
            summary += f"📎 مدارک: {'ارسال شده' if doc_path else 'بدون مدرک'}\n\n"
            summary += f"🔄 **وضعیت:** در انتظار بررسی مدیر"
            
            bot.reply_to(message, summary, reply_markup=get_back_keyboard())
        except Exception as e:
            print(f"❌ خطا: {e}")
            bot.reply_to(message, f"❌ خطا: {str(e)}", reply_markup=get_back_keyboard())
    else:
        bot.reply_to(
            message,
            "📎 لطفاً فایل ارسال کنید یا 'تكميل' را وارد کنید.",
            reply_markup=get_cancel_keyboard()
        )

# ============================================================
# ===== وضعیت وام =====
# ============================================================
@bot.message_handler(func=lambda m: m.text == "4️⃣ وضعیت وام" or m.text == "4")
def loan_status_handler(message):
    user_id = message.from_user.id
    if user_id not in user_member_ids:
        bot.reply_to(message, "❌ ابتدا کد عضویت خود را وارد کنید!", reply_markup=get_main_keyboard())
        return
    
    try:
        member_code = user_member_ids[user_id]
        conn = get_db()
        if not conn:
            bot.reply_to(message, "❌ خطا در دیتابیس!")
            return
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT amount, remaining_amount, monthly_installment, status, paid_installments, total_installments, date
            FROM loans WHERE member_id = ? ORDER BY id DESC LIMIT 1
        """, (member_code,))
        loan = cursor.fetchone()
        conn.close()
        
        if loan:
            amount = loan['amount']
            remaining = loan['remaining_amount']
            monthly = loan['monthly_installment']
            status = loan['status']
            paid_installments = loan['paid_installments'] if loan['paid_installments'] else 0
            total_installments = loan['total_installments'] if loan['total_installments'] else 40
            loan_date = loan['date'] if loan['date'] else ''
            
            progress = int(((amount - remaining) / amount) * 100) if amount > 0 else 0
            status_text = "🟢 فعال" if status == 'active' and remaining > 0 else "✅ تسویه شده"
            paid_amount = amount - remaining if remaining >= 0 else amount
            
            text = f"📊 **وضعیت وام شما**\n\n"
            text += f"💰 مبلغ وام: {amount:,} ریال\n"
            text += f"📈 مانده: {remaining:,} ریال\n"
            text += f"💳 پرداختی: {paid_amount:,} ریال\n"
            text += f"📊 پیشرفت: {progress}%\n"
            text += f"📌 وضعیت: {status_text}\n"
            if total_installments > 0:
                text += f"🔄 اقساط: {paid_installments}/{total_installments}\n"
            if monthly > 0:
                text += f"💳 قسط ماهانه: {monthly:,} ریال\n"
            if remaining > 0 and monthly > 0:
                remaining_months = (remaining + monthly - 1) // monthly
                text += f"\n📌 تعداد اقساط باقیمانده: حدود {remaining_months} ماه"
        else:
            text = "❌ **شما وام فعالی ندارید.**\n\n📌 برای دریافت وام، از گزینه 3️⃣ استفاده کنید."
        
        bot.reply_to(message, text, reply_markup=get_back_keyboard())
    except Exception as e:
        print(f"❌ خطا: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}", reply_markup=get_back_keyboard())

# ============================================================
# ===== پیام‌های نامشخص =====
# ============================================================
@bot.message_handler(func=lambda m: True)
def unknown_handler(message):
    user_id = message.from_user.id
    if user_id in user_states and user_states[user_id] == 'register':
        bot.reply_to(message, "📝 لطفاً عدد وارد کنید یا 'لغو' را بزنید.", reply_markup=get_cancel_keyboard())
        return
    if user_id in user_states and user_states[user_id] == 'loan_amount':
        bot.reply_to(message, "💰 مبلغ وام را وارد کنید یا 'لغو' را بزنید.", reply_markup=get_cancel_keyboard())
        return
    if user_id in user_states and user_states[user_id] == 'loan_document':
        bot.reply_to(message, "📎 مدارک را ارسال کنید یا 'تكميل' را وارد کنید.", reply_markup=get_cancel_keyboard())
        return
    if user_id not in user_member_ids:
        bot.reply_to(message, "❌ ابتدا کد عضویت خود را وارد کنید!", reply_markup=get_main_keyboard())
        return
    bot.reply_to(message, "❌ گزینه نامعتبر!", reply_markup=get_main_keyboard())

# ============================================================
# ===== اجرا =====
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 ربات کامل صندوق قرض‌الحسنه ۱۴ معصوم")
    print("📱 شناسه: @masum_sandogh14_bot")
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
    
    print("🚀 وب سرور روی پورت 10000...")
    threading.Thread(target=run_web, daemon=True).start()
    
    print("🚀 ربات در حال اجرا...")
    bot.polling(none_stop=True, interval=3)
