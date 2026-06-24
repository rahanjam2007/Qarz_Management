# telegram_bot_render.py - نسخه مخصوص Render

import telebot
import os
import time
import requests
import jdatetime
import json
from datetime import datetime

# ===== توکن از متغیر محیطی =====
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    print("❌ خطا: TELEGRAM_TOKEN تنظیم نشده است!")
    exit(1)

bot = telebot.TeleBot(TOKEN)

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
    bot.reply_to(
        message,
        "🤖 **به ربات صندوق قرض الحسنه 14 معصوم خوش آمديد!**\n\n"
        "✅ ربات با موفقیت روی Render اجرا شده است!\n\n"
        "📌 لطفاً از منوی زیر استفاده کنید.",
        reply_markup=get_main_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "🔙 بازگشت به منوی اصلی")
def back_to_main(message):
    bot.reply_to(
        message,
        "🔙 **به منوی اصلی بازگشتید.**\n\n"
        "📌 از گزینه‌های زیر استفاده کنید:",
        reply_markup=get_main_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "1️⃣ ثبت واریزی" or m.text == "1")
def register_start(message):
    bot.reply_to(
        message,
        "📝 **ثبت واریزی جدید**\n\n"
        "این بخش در حال راه‌اندازی است.\n"
        "📌 به زودی فعال می‌شود.",
        reply_markup=get_back_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "2️⃣ مانده حساب" or m.text == "2")
def balance_handler(message):
    bot.reply_to(
        message,
        "📊 **مانده حساب**\n\n"
        "این بخش در حال راه‌اندازی است.\n"
        "📌 به زودی فعال می‌شود.",
        reply_markup=get_back_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "3️⃣ درخواست وام" or m.text == "3")
def loan_start(message):
    bot.reply_to(
        message,
        "💰 **درخواست وام**\n\n"
        "این بخش در حال راه‌اندازی است.\n"
        "📌 به زودی فعال می‌شود.",
        reply_markup=get_back_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "4️⃣ وضعیت وام" or m.text == "4")
def loan_status_handler(message):
    bot.reply_to(
        message,
        "📊 **وضعیت وام**\n\n"
        "این بخش در حال راه‌اندازی است.\n"
        "📌 به زودی فعال می‌شود.",
        reply_markup=get_back_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "5️⃣ راهنمای کامل" or m.text == "5")
def help_handler(message):
    text = "📖 **راهنماي كامل ربات**\n\n"
    text += "1️⃣ **ثبت واريزي**\n"
    text += "   در حال راه‌اندازی\n\n"
    text += "2️⃣ **مانده حساب**\n"
    text += "   در حال راه‌اندازی\n\n"
    text += "3️⃣ **درخواست وام**\n"
    text += "   در حال راه‌اندازی\n\n"
    text += "4️⃣ **وضعيت وام**\n"
    text += "   در حال راه‌اندازی\n\n"
    text += "📞 پشتيباني: 09387026799"
    
    bot.reply_to(message, text, reply_markup=get_back_keyboard())


@bot.message_handler(func=lambda m: True)
def unknown_handler(message):
    bot.reply_to(
        message,
        "❌ گزينه نامعتبر!\n\n"
        "📌 لطفاً از دكمه هاي منو استفاده كنيد.",
        reply_markup=get_main_keyboard()
    )


# ============================================================
# ===== اجرا =====
# ============================================================
if __name__ == "__main__":
    try:
        bot.remove_webhook()
        print("✅ Webhook پاك شد")
    except Exception as e:
        print(f"⚠️ خطا در پاك كردن webhook: {e}")
    
    print("🚀 ربات در حال اجرا...")
    bot.polling(none_stop=True, interval=3)
