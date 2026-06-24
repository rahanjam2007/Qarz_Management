# telegram_bot_render.py - نسخه مستقل برای Render (بدون وابستگی به فایل‌های محلی)

import telebot
import os
import json
import time
import jdatetime
from datetime import datetime
import requests
from telebot import apihelper

# ===== تنظیمات =====
TOKEN = "8705261999:AAF34fID3LoF0_yiXVGKiwyStWNtb6zUIwo"
SUPPORT_PHONE = "09387026799"

# ===== افزایش timeout =====
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 60

bot = telebot.TeleBot(TOKEN)

# دیکشنری‌ها
user_states = {}
user_member_ids = {}
user_temp_data = {}

print("=" * 60)
print("🤖 ربات تلگرام صندوق قرض‌الحسنه ۱۴ معصوم")
print("📱 شناسه ربات: @sandoogh14_bot")
print("✅ در حال اجرا روی Render...")
print("=" * 60)


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


def process_code(message):
    user_id = message.from_user.id
    code = message.text.strip()
    
    try:
        member_id = int(code)
        # در این نسخه، کد عضویت را فقط تأیید می‌کنیم
        if code.isdigit():
            user_member_ids[user_id] = code
            user_states[user_id] = 'main'
            bot.reply_to(
                message,
                f"✅ کد عضویت {code} تأیید شد!\n\n"
                "📌 از منوی زیر استفاده کنید:",
                reply_markup=get_main_keyboard()
            )
        else:
            bot.reply_to(
                message,
                "❌ کد عضویت نامعتبر!",
                reply_markup=get_cancel_keyboard()
            )
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {str(e)}")


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


@bot.message_handler(func=lambda m: m.text == "5️⃣ راهنمای کامل" or m.text == "5")
def help_handler(message):
    text = "📖 **راهنمای کامل ربات**\n\n"
    text += "1️⃣ ثبت واریزی\n"
    text += "2️⃣ مانده حساب\n"
    text += "3️⃣ درخواست وام\n"
    text += "4️⃣ وضعیت وام\n\n"
    text += f"📞 پشتیبانی: {SUPPORT_PHONE}"
    bot.reply_to(message, text, reply_markup=get_back_keyboard())


@bot.message_handler(func=lambda m: m.text == "1️⃣ ثبت واریزی" or m.text == "1")
def register_start(message):
    if message.from_user.id not in user_member_ids:
        bot.reply_to(message, "❌ ابتدا کد عضویت خود را وارد کنید!", reply_markup=get_main_keyboard())
        return
    
    user_id = message.from_user.id
    user_temp_data[user_id] = {'step': 'total', 'total': 0, 'subscription': 0, 'installment': 0}
    user_states[user_id] = 'register'
    
    msg = bot.reply_to(
        message,
        "📝 **ثبت واریزی**\n\nمرحله 1 از 3:\nمبلغ کل واریزی را وارد کنید:\nمثال: 10000000",
        reply_markup=get_cancel_keyboard()
    )
    bot.register_next_step_handler(msg, process_register_total)


def process_register_total(message):
    user_id = message.from_user.id
    if message.text == "❌ لغو":
        user_states[user_id] = 'main'
        if user_id in user_temp_data:
            del user_temp_data[user_id]
        bot.reply_to(message, "✅ لغو شد.", reply_markup=get_main_keyboard())
        return
    
    try:
        total = int(message.text.replace(',', '').strip())
        if total <= 0:
            bot.reply_to(message, "❌ مبلغ باید بزرگتر از صفر باشد!")
            return
        
        user_temp_data[user_id]['total'] = total
        user_temp_data[user_id]['step'] = 'subscription'
        
        msg = bot.reply_to(
            message,
            f"✅ مبلغ کل: {total:,} ریال\n\nمرحله 2 از 3:\nمبلغ حق اشتراک را وارد کنید:",
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
        bot.reply_to(message, "✅ لغو شد.", reply_markup=get_main_keyboard())
        return
    
    try:
        subscription = int(message.text.replace(',', '').strip())
        total = user_temp_data[user_id]['total']
        
        if subscription < 0 or subscription > total:
            bot.reply_to(message, f"❌ مبلغ اشتراک باید بین 0 تا {total:,} باشد!")
            return
        
        user_temp_data[user_id]['subscription'] = subscription
        user_temp_data[user_id]['step'] = 'installment'
        
        remaining = total - subscription
        msg = bot.reply_to(
            message,
            f"✅ مبلغ اشتراک: {subscription:,} ریال\n"
            f"📌 باقیمانده: {remaining:,} ریال\n\n"
            "مرحله 3 از 3:\nمبلغ قسط را وارد کنید (0 اگر ندارید):",
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
        bot.reply_to(message, "✅ لغو شد.", reply_markup=get_main_keyboard())
        return
    
    try:
        installment = int(message.text.replace(',', '').strip())
        total = user_temp_data[user_id]['total']
        subscription = user_temp_data[user_id]['subscription']
        
        if installment < 0 or installment > (total - subscription):
            bot.reply_to(message, f"❌ مبلغ قسط باید بین 0 تا {total - subscription:,} باشد!")
            return
        
        # ثبت واریزی
        user_temp_data[user_id] = {}
        user_states[user_id] = 'main'
        
        today = jdatetime.date.today()
        month_name = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                     "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"][today.month - 1]
        
        summary = f"✅ **واریزی با موفقیت ثبت شد!**\n\n"
        summary += f"📅 تاریخ: {today.strftime('%Y/%m/%d')} ({month_name})\n"
        summary += f"💰 مبلغ کل: {total:,} ریال\n"
        summary += f"📊 اشتراک: {subscription:,} ریال\n"
        summary += f"💳 قسط: {installment:,} ریال\n\n"
        summary += f"⏳ **وضعیت:** در انتظار تأیید مدیر"
        
        bot.reply_to(message, summary, reply_markup=get_back_keyboard())
        
    except:
        bot.reply_to(message, "❌ لطفاً عدد وارد کنید!", reply_markup=get_cancel_keyboard())


@bot.message_handler(func=lambda m: m.text == "2️⃣ مانده حساب" or m.text == "2")
def balance_handler(message):
    if message.from_user.id not in user_member_ids:
        bot.reply_to(message, "❌ ابتدا کد عضویت خود را وارد کنید!", reply_markup=get_main_keyboard())
        return
    
    user_id = message.from_user.id
    today = jdatetime.date.today()
    month_name = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                 "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"][today.month - 1]
    
    text = f"📊 **اطلاعات مالی شما**\n\n"
    text += f"🆔 کد عضویت: {user_member_ids[user_id]}\n"
    text += f"📅 تاریخ: {today.strftime('%Y/%m/%d')} ({month_name})\n\n"
    text += f"💰 **انباشته:** اطلاعات در حال به‌روزرسانی\n"
    text += f"💳 **مانده وام:** اطلاعات در حال به‌روزرسانی\n\n"
    text += f"📌 این نسخه نمایشی است."
    
    bot.reply_to(message, text, reply_markup=get_back_keyboard())


@bot.message_handler(func=lambda m: m.text == "3️⃣ درخواست وام" or m.text == "3")
def loan_start(message):
    if message.from_user.id not in user_member_ids:
        bot.reply_to(message, "❌ ابتدا کد عضویت خود را وارد کنید!", reply_markup=get_main_keyboard())
        return
    
    user_id = message.from_user.id
    user_temp_data[user_id] = {'amount': 0, 'doc_path': None}
    user_states[user_id] = 'loan_amount'
    
    msg = bot.reply_to(
        message,
        "💰 **درخواست وام**\n\n"
        "مرحله 1 از 2:\n"
        "مبلغ وام مورد نظر را وارد کنید:\n"
        "مثال: 50000000\n\n"
        "⚠️ حداقل: 500,000 - حداکثر: 2 میلیارد",
        reply_markup=get_cancel_keyboard()
    )
    bot.register_next_step_handler(msg, process_loan_amount)


def process_loan_amount(message):
    user_id = message.from_user.id
    if message.text == "❌ لغو":
        user_states[user_id] = 'main'
        if user_id in user_temp_data:
            del user_temp_data[user_id]
        bot.reply_to(message, "✅ لغو شد.", reply_markup=get_main_keyboard())
        return
    
    try:
        amount = int(message.text.replace(',', '').strip())
        if amount < 500000:
            bot.reply_to(message, "❌ حداقل مبلغ 500,000 ریال است!")
            return
        if amount > 2000000000:
            bot.reply_to(message, "❌ حداکثر مبلغ 2 میلیارد ریال است!")
            return
        
        user_temp_data[user_id]['amount'] = amount
        user_states[user_id] = 'loan_document'
        
        msg = bot.reply_to(
            message,
            f"✅ مبلغ وام: {amount:,} ریال\n\n"
            "مرحله 2 از 2:\n"
            "📎 مدارک خود را ارسال کنید (تصویر یا PDF)\n"
            "📌 یا کلمه **'تكميل'** را برای تکمیل بدون مدرک وارد کنید.",
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
        bot.reply_to(message, "✅ لغو شد.", reply_markup=get_main_keyboard())
        return
    
    if message.text and "تكميل" in message.text.replace('ي', 'ی').replace('ك', 'ک'):
        # تکمیل درخواست
        amount = user_temp_data[user_id]['amount']
        user_states[user_id] = 'main'
        if user_id in user_temp_data:
            del user_temp_data[user_id]
        
        today = jdatetime.date.today()
        month_name = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                     "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"][today.month - 1]
        
        summary = f"✅ **درخواست وام ثبت شد!**\n\n"
        summary += f"💰 مبلغ: {amount:,} ریال\n"
        summary += f"📅 تاریخ: {today.strftime('%Y/%m/%d')}\n"
        summary += f"🔄 وضعیت: در انتظار بررسی مدیر"
        
        bot.reply_to(message, summary, reply_markup=get_back_keyboard())
    else:
        bot.reply_to(
            message,
            "📎 لطفاً مدارک خود را ارسال کنید یا 'تكميل' را وارد کنید.",
            reply_markup=get_cancel_keyboard()
        )


@bot.message_handler(func=lambda m: m.text == "4️⃣ وضعیت وام" or m.text == "4")
def loan_status_handler(message):
    if message.from_user.id not in user_member_ids:
        bot.reply_to(message, "❌ ابتدا کد عضویت خود را وارد کنید!", reply_markup=get_main_keyboard())
        return
    
    text = "📊 **وضعیت وام شما**\n\n"
    text += "❌ شما وام فعالی ندارید.\n\n"
    text += "📌 برای دریافت وام، از گزینه 3️⃣ استفاده کنید."
    
    bot.reply_to(message, text, reply_markup=get_back_keyboard())


@bot.message_handler(func=lambda m: True)
def unknown_handler(message):
    user_id = message.from_user.id
    if user_id in user_states and user_states[user_id] == 'register':
        bot.reply_to(message, "📝 لطفاً عدد وارد کنید یا 'لغو' را بزنید.", reply_markup=get_cancel_keyboard())
        return
    if user_id in user_states and user_states[user_id] == 'loan_amount':
        bot.reply_to(message, "💰 مبلغ وام را وارد کنید یا 'لغو' را بزنید.", reply_markup=get_cancel_keyboard())
        return
    if user_id not in user_member_ids:
        bot.reply_to(message, "❌ ابتدا کد عضویت خود را وارد کنید!", reply_markup=get_main_keyboard())
        return
    bot.reply_to(message, "❌ گزینه نامعتبر!", reply_markup=get_main_keyboard())


# ============================================================
# ===== اجرا =====
# ============================================================
if __name__ == "__main__":
    try:
        bot.remove_webhook()
        print("✅ Webhook پاک شد")
    except Exception as e:
        print(f"⚠️ خطا: {e}")
    
    print("🚀 ربات در حال اجرا...")
    bot.polling(none_stop=True, interval=3)
