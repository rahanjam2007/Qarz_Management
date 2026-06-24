# telegram_bot_render.py - نسخه کامل برای Render با دیتابیس

import telebot
from telebot import apihelper
from bot_api import BotAPI
import jdatetime
import re
import os
import json
import time
import sys
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

# ===== غیرفعال کردن هشدارهای SSL =====
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = "8705261999:AAF34fID3LoF0_yiXVGKiwyStWNtb6zUIwo"
SUPPORT_PHONE = "09387026799"

# ===== تنظیم timeout =====
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 60

# ===== تنظیمات session =====
session = requests.Session()
retry = Retry(
    total=5,
    read=5,
    connect=5,
    backoff_factor=0.5,
    status_forcelist=(500, 502, 503, 504)
)
adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
session.mount('http://', adapter)
session.mount('https://', adapter)

bot = telebot.TeleBot(TOKEN)
bot.session = session

# دیکشنری‌ها
user_states = {}
user_member_ids = {}
user_temp_data = {}
MAX_RETRIES = 20
RETRY_DELAY = 15

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
# ===== مدیریت chat_id =====
# ============================================================
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
        "🔙 **به منوی اصلی بازگشتید.**",
        reply_markup=get_main_keyboard()
    )


# ============================================================
# ===== دریافت کد عضویت =====
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
                api = BotAPI()
                member = api.get_member_by_id(int(member_code))
                api.close()
                if member and member.get('phone'):
                    save_chat_id(member['phone'], chat_id)
            except Exception as e:
                print(f"⚠️ خطا در ذخيره chat_id: {e}")
            bot.reply_to(
                message,
                f"👋 **خوش برگشتيد!**\n🆔 كد عضويت: {user_member_ids[user_id]}",
                reply_markup=get_main_keyboard()
            )
            return
        
        user_states[user_id] = 'get_code'
        msg = bot.reply_to(
            message,
            "🤖 **به ربات صندوق قرض الحسنه 14 معصوم خوش آمديد!**\n\n"
            "📌 لطفاً **كد عضويت** خود را وارد كنيد.\n\n"
            "⚠️ اگر كد عضويت نداريد، با پشتيباني تماس بگيريد:\n"
            f"📞 {SUPPORT_PHONE}",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, process_code)
    except Exception as e:
        print(f"❌ خطا در start: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}")


def process_code(message):
    user_id = message.from_user.id
    chat_id = user_id
    code = message.text.strip()
    
    try:
        member_id = int(code)
        api = BotAPI()
        member = api.get_member_by_id(member_id)
        
        if member:
            user_member_ids[user_id] = code
            user_states[user_id] = 'main'
            phone = member.get('phone')
            if phone:
                save_chat_id(phone, chat_id)
            api.close()
            bot.reply_to(
                message,
                f"✅ **كد عضويت {code} تاييد شد!**\n\n"
                f"👤 نام: {member['name']}\n"
                f"🆔 كد عضويت: {member['id']}\n"
                f"📱 شماره همراه: {member['phone'] if member['phone'] else 'ثبت نشده'}\n\n"
                "📌 از منوي زير استفاده كنيد:",
                reply_markup=get_main_keyboard()
            )
        else:
            api.close()
            bot.reply_to(
                message,
                f"❌ كد عضويت {code} يافت نشد!",
                reply_markup=get_cancel_keyboard()
            )
            msg = bot.reply_to(message, "📝 كد عضويت خود را وارد كنيد:")
            bot.register_next_step_handler(msg, process_code)
    except Exception as e:
        print(f"❌ خطا در process_code: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}")


# ============================================================
# ===== راهنما =====
# ============================================================
@bot.message_handler(func=lambda m: m.text == "5️⃣ راهنمای کامل" or m.text == "5")
def help_handler(message):
    text = "📖 **راهنماي كامل ربات**\n\n"
    text += "1️⃣ **ثبت واريزي**\n"
    text += "   مراحل: مبلغ كل، اشتراك، قسط\n\n"
    text += "2️⃣ **مانده حساب**\n"
    text += "   نمايش انباشته و مانده وام\n\n"
    text += "3️⃣ **درخواست وام**\n"
    text += "   مراحل: مبلغ وام، ارسال مدارك\n\n"
    text += "4️⃣ **وضعيت وام**\n"
    text += "   نمايش وضعيت وام فعلي\n\n"
    text += "📌 **نكات مهم:**\n"
    text += "• براي انصراف، دكمه 'لغو' را بزنيد.\n"
    text += "• براي تكميل درخواست وام، كلمه **'تكميل'** را وارد كنيد.\n"
    text += f"📞 پشتيباني: {SUPPORT_PHONE}"
    bot.reply_to(message, text, reply_markup=get_back_keyboard())


# ============================================================
# ===== ثبت واریزی =====
# ============================================================
@bot.message_handler(func=lambda m: m.text == "1️⃣ ثبت واریزی" or m.text == "1")
def register_start(message):
    user_id = message.from_user.id
    try:
        if user_id not in user_member_ids:
            bot.reply_to(message, "❌ ابتدا كد عضويت خود را وارد كنيد!", reply_markup=get_main_keyboard())
            return
        
        user_temp_data[user_id] = {'step': 'total', 'total': 0, 'subscription': 0, 'installment': 0}
        user_states[user_id] = 'register'
        
        msg = bot.reply_to(
            message,
            "📝 **ثبت واريزي جديد**\n\nمرحله 1 از 3:\nلطفاً **مبلغ كل واريزي** را وارد كنيد.\nمثال: 10000000",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, process_register_total)
    except Exception as e:
        print(f"❌ خطا در register_start: {e}")


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
            bot.reply_to(message, "❌ مبلغ بايد بزرگتر از صفر باشد!")
            return
        user_temp_data[user_id]['total'] = total
        user_temp_data[user_id]['step'] = 'subscription'
        msg = bot.reply_to(
            message,
            f"✅ مبلغ كل: {total:,} ريال\n\nمرحله 2 از 3:\nمبلغ حق اشتراك را وارد كنيد:",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, process_register_subscription)
    except:
        bot.reply_to(message, "❌ لطفاً عدد وارد كنيد!", reply_markup=get_cancel_keyboard())


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
            bot.reply_to(message, f"❌ مبلغ اشتراك بايد بين 0 تا {total:,} باشد!")
            return
        user_temp_data[user_id]['subscription'] = subscription
        user_temp_data[user_id]['step'] = 'installment'
        remaining = total - subscription
        msg = bot.reply_to(
            message,
            f"✅ مبلغ اشتراك: {subscription:,} ريال\n📌 باقيمانده: {remaining:,} ريال\n\nمرحله 3 از 3:\nمبلغ قسط را وارد كنيد (0 اگر نداريد):",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, process_register_installment)
    except:
        bot.reply_to(message, "❌ لطفاً عدد وارد كنيد!", reply_markup=get_cancel_keyboard())


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
            bot.reply_to(message, f"❌ مبلغ قسط بايد بين 0 تا {total - subscription:,} باشد!")
            return
        
        member_code = user_member_ids.get(user_id)
        api = BotAPI()
        member = api.get_member_by_id(int(member_code))
        if not member:
            api.close()
            bot.reply_to(message, "❌ عضو يافت نشد!", reply_markup=get_main_keyboard())
            return
        
        result = api.register_transaction(member['id'], total, subscription, installment, source='bot')
        api.close()
        
        if user_id in user_temp_data:
            del user_temp_data[user_id]
        user_states[user_id] = 'main'
        
        if result['success']:
            today = jdatetime.date.today()
            month_name = ["فروردين", "ارديبهشت", "خرداد", "تير", "مرداد", "شهريور",
                         "مهر", "آبان", "آذر", "دي", "بهمن", "اسفند"][today.month - 1]
            summary = f"✅ **واريزي با موفقيت ثبت شد!**\n\n"
            summary += f"👤 عضو: {member['name']}\n"
            summary += f"📅 تاريخ: {today.strftime('%Y/%m/%d')} ({month_name})\n"
            summary += f"💰 مبلغ كل: {total:,} ريال\n"
            summary += f"📊 اشتراك: {subscription:,} ريال\n"
            summary += f"💳 قسط: {installment:,} ريال\n\n"
            summary += f"⏳ **وضعيت:** در انتظار تاييد مدير"
            bot.reply_to(message, summary, reply_markup=get_back_keyboard())
        else:
            bot.reply_to(message, "❌ خطا در ثبت!", reply_markup=get_back_keyboard())
    except Exception as e:
        print(f"❌ خطا: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}", reply_markup=get_cancel_keyboard())


# ============================================================
# ===== مانده حساب =====
# ============================================================
@bot.message_handler(func=lambda m: m.text == "2️⃣ مانده حساب" or m.text == "2")
def balance_handler(message):
    user_id = message.from_user.id
    try:
        if user_id not in user_member_ids:
            bot.reply_to(message, "❌ ابتدا كد عضويت خود را وارد كنيد!", reply_markup=get_main_keyboard())
            return
        
        member_code = user_member_ids.get(user_id)
        api = BotAPI()
        member = api.get_member_by_id(int(member_code))
        if not member:
            api.close()
            bot.reply_to(message, "❌ عضو يافت نشد!", reply_markup=get_main_keyboard())
            return
        
        balance = api.get_member_balance(member['id'])
        api.close()
        
        today = jdatetime.date.today()
        month_name = ["فروردين", "ارديبهشت", "خرداد", "تير", "مرداد", "شهريور",
                     "مهر", "آبان", "آذر", "دي", "بهمن", "اسفند"][today.month - 1]
        
        text = f"📊 **اطلاعات مالي شما**\n\n"
        text += f"👤 نام: {member['name']}\n"
        text += f"🆔 كد عضويت: {member['id']}\n"
        text += f"📅 تاريخ: {today.strftime('%Y/%m/%d')} ({month_name})\n\n"
        text += f"💰 **انباشته:** {balance['accumulated']:,} ريال\n"
        text += f"💳 **مانده وام:** {balance['loan_remaining']:,} ريال\n\n"
        if balance['loan_remaining'] > 0:
            text += "📌 وضعيت وام: **فعال**"
        else:
            text += "✅ وضعيت وام: **تسويه شده**"
        bot.reply_to(message, text, reply_markup=get_back_keyboard())
    except Exception as e:
        print(f"❌ خطا در balance_handler: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}", reply_markup=get_back_keyboard())


# ============================================================
# ===== درخواست وام =====
# ============================================================
@bot.message_handler(func=lambda m: m.text == "3️⃣ درخواست وام" or m.text == "3")
def loan_start(message):
    user_id = message.from_user.id
    try:
        if user_id not in user_member_ids:
            bot.reply_to(message, "❌ ابتدا كد عضويت خود را وارد كنيد!", reply_markup=get_main_keyboard())
            return
        
        user_temp_data[user_id] = {'amount': 0, 'doc_path': None}
        user_states[user_id] = 'loan_amount'
        msg = bot.reply_to(
            message,
            "💰 **درخواست وام**\n\nمرحله 1 از 2:\nمبلغ وام را وارد كنيد:\nمثال: 50000000\n\n⚠️ حداقل: 500,000 - حداكثر: 2 ميليارد",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, process_loan_amount)
    except Exception as e:
        print(f"❌ خطا: {e}")


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
            bot.reply_to(message, "❌ حداقل مبلغ 500,000 ريال است!")
            return
        if amount > 2000000000:
            bot.reply_to(message, "❌ حداكثر مبلغ 2 ميليارد ريال است!")
            return
        
        member_code = user_member_ids.get(user_id)
        api = BotAPI()
        member = api.get_member_by_id(int(member_code))
        if not member:
            api.close()
            bot.reply_to(message, "❌ عضو يافت نشد!", reply_markup=get_main_keyboard())
            return
        
        balance = api.get_member_balance(member['id'])
        required = int((amount // 2) * 0.75)
        api.close()
        
        if balance['accumulated'] < required:
            shortage = required - balance['accumulated']
            bot.reply_to(
                message,
                f"⚠️ **انباشته كافي نيست!**\n\n💰 انباشته فعلي: {balance['accumulated']:,} ريال\n🎯 نياز حداقل: {required:,} ريال\n➕ كمبود: {shortage:,} ريال\n\nآيا ادامه مي‌دهيد؟",
                reply_markup=get_cancel_keyboard()
            )
            msg = bot.reply_to(message, "📝 براي ادامه، 'ادامه' را وارد كنيد:")
            bot.register_next_step_handler(msg, process_loan_continue)
            return
        
        user_temp_data[user_id]['amount'] = amount
        user_states[user_id] = 'loan_document'
        msg = bot.reply_to(
            message,
            f"✅ مبلغ وام: {amount:,} ريال\n\nمرحله 2 از 2:\n📎 مدارك را ارسال كنيد (تصوير يا PDF)\n📌 يا 'تكميل' را براي تكميل بدون مدرك وارد كنيد.",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, process_loan_document)
    except Exception as e:
        print(f"❌ خطا: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}", reply_markup=get_cancel_keyboard())


def process_loan_continue(message):
    user_id = message.from_user.id
    if message.text == "❌ لغو":
        user_states[user_id] = 'main'
        if user_id in user_temp_data:
            del user_temp_data[user_id]
        bot.reply_to(message, "✅ لغو شد.", reply_markup=get_main_keyboard())
        return
    if message.text.lower() == "ادامه":
        amount = user_temp_data[user_id]['amount']
        user_states[user_id] = 'loan_document'
        msg = bot.reply_to(
            message,
            f"✅ مبلغ وام: {amount:,} ريال\n\nمرحله 2 از 2:\n📎 مدارك را ارسال كنيد\n📌 يا 'تكميل' را وارد كنيد.",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, process_loan_document)
    else:
        bot.reply_to(message, "❌ گزينه نامعتبر!", reply_markup=get_cancel_keyboard())


def process_loan_document(message):
    user_id = message.from_user.id
    if message.text == "❌ لغو":
        user_states[user_id] = 'main'
        if user_id in user_temp_data:
            del user_temp_data[user_id]
        bot.reply_to(message, "✅ لغو شد.", reply_markup=get_main_keyboard())
        return
    
    text = message.text.strip() if message.text else ""
    complete_words = ['تكميل', 'تکمیل', 'تكمیل', 'تکميل', 'complete', 'تمام', 'پایان']
    is_complete = any(w in text.replace('ي', 'ی').replace('ك', 'ک') for w in complete_words)
    
    if message.document or message.photo:
        # ذخیره فایل (ساده شده برای Render)
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
                f"✅ فايل '{file_name}' دريافت شد.\n📌 براي تكميل، 'تكميل' را وارد كنيد.",
                reply_markup=get_cancel_keyboard()
            )
        except Exception as e:
            bot.reply_to(message, f"❌ خطا در دريافت فايل: {str(e)}", reply_markup=get_cancel_keyboard())
    elif is_complete:
        # تکمیل درخواست
        try:
            amount = user_temp_data[user_id]['amount']
            doc_path = user_temp_data[user_id].get('doc_path', '')
            
            member_code = user_member_ids.get(user_id)
            api = BotAPI()
            member = api.get_member_by_id(int(member_code))
            if not member:
                api.close()
                bot.reply_to(message, "❌ عضو يافت نشد!", reply_markup=get_main_keyboard())
                return
            
            result = api.request_loan_with_doc(member['id'], amount, doc_path)
            api.close()
            
            if user_id in user_temp_data:
                del user_temp_data[user_id]
            user_states[user_id] = 'main'
            
            if result['success']:
                today = jdatetime.date.today()
                month_name = ["فروردين", "ارديبهشت", "خرداد", "تير", "مرداد", "شهريور",
                             "مهر", "آبان", "آذر", "دي", "بهمن", "اسفند"][today.month - 1]
                summary = f"✅ **درخواست وام ثبت شد!**\n\n"
                summary += f"👤 عضو: {member['name']}\n"
                summary += f"📅 تاريخ: {today.strftime('%Y/%m/%d')} ({month_name})\n"
                summary += f"💰 مبلغ: {amount:,} ريال\n"
                summary += f"📌 شماره پيگيري: {result['secretariat_no']}\n\n"
                summary += f"🔄 **وضعيت:** در انتظار بررسي مدير"
                bot.reply_to(message, summary, reply_markup=get_back_keyboard())
            else:
                bot.reply_to(message, f"❌ {result['message']}", reply_markup=get_back_keyboard())
        except Exception as e:
            print(f"❌ خطا: {e}")
            bot.reply_to(message, f"❌ خطا: {str(e)}", reply_markup=get_back_keyboard())
    else:
        bot.reply_to(
            message,
            "📎 لطفاً فايل ارسال كنيد يا 'تكميل' را وارد كنيد.",
            reply_markup=get_cancel_keyboard()
        )


# ============================================================
# ===== وضعیت وام =====
# ============================================================
@bot.message_handler(func=lambda m: m.text == "4️⃣ وضعیت وام" or m.text == "4")
def loan_status_handler(message):
    user_id = message.from_user.id
    try:
        if user_id not in user_member_ids:
            bot.reply_to(message, "❌ ابتدا كد عضويت خود را وارد كنيد!", reply_markup=get_main_keyboard())
            return
        
        member_code = user_member_ids.get(user_id)
        api = BotAPI()
        member = api.get_member_by_id(int(member_code))
        if not member:
            api.close()
            bot.reply_to(message, "❌ عضو يافت نشد!", reply_markup=get_main_keyboard())
            return
        
        loan = api.get_member_loan_status(member['id'])
        api.close()
        
        if loan:
            amount = loan.get('amount', 0)
            remaining = loan.get('remaining', 0)
            monthly = loan.get('monthly', 0)
            status = loan.get('status', '')
            paid_installments = loan.get('paid', 0)
            total_installments = loan.get('total', 40)
            progress = int(((amount - remaining) / amount) * 100) if amount > 0 else 0
            status_text = "🟢 فعال" if status == 'active' and remaining > 0 else "✅ تسويه شده"
            paid_amount = amount - remaining if remaining >= 0 else amount
            
            text = f"📊 **وضعيت وام شما**\n\n"
            text += f"👤 عضو: {member['name']}\n"
            text += f"💰 مبلغ وام: {amount:,} ريال\n"
            text += f"📈 مانده: {remaining:,} ريال\n"
            text += f"💳 پرداختي: {paid_amount:,} ريال\n"
            text += f"📊 پيشرفت: {progress}%\n"
            text += f"📌 وضعيت: {status_text}\n"
            if total_installments > 0:
                text += f"🔄 اقساط: {paid_installments}/{total_installments}\n"
            if monthly > 0:
                text += f"💳 قسط ماهانه: {monthly:,} ريال\n"
            if remaining > 0 and monthly > 0:
                remaining_months = (remaining + monthly - 1) // monthly
                text += f"\n📌 تعداد اقساط باقيمانده: حدود {remaining_months} ماه"
        else:
            text = "❌ **شما وام فعالی نداريد.**\n\n📌 براي دريافت وام، از گزينه 3️⃣ استفاده كنيد."
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
        bot.reply_to(message, "📝 عدد وارد كنيد يا 'لغو' را بزنيد.", reply_markup=get_cancel_keyboard())
        return
    if user_id in user_states and user_states[user_id] == 'loan_amount':
        bot.reply_to(message, "💰 مبلغ وام را وارد كنيد يا 'لغو' را بزنيد.", reply_markup=get_cancel_keyboard())
        return
    if user_id in user_states and user_states[user_id] == 'loan_document':
        bot.reply_to(message, "📎 مدارك را ارسال كنيد يا 'تكميل' را وارد كنيد.", reply_markup=get_cancel_keyboard())
        return
    if user_id not in user_member_ids:
        bot.reply_to(message, "❌ ابتدا كد عضويت خود را وارد كنيد!", reply_markup=get_main_keyboard())
        return
    bot.reply_to(message, "❌ گزينه نامعتبر!", reply_markup=get_main_keyboard())


# ============================================================
# ===== اجرا =====
# ============================================================
def run_bot():
    global bot
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            print("\n🚀 ربات در حال راه اندازي...")
            print("📱 منتظر پيام هاي كاربران...")
            print("=" * 60)
            try:
                bot.remove_webhook()
                print("✅ Webhook پاك شد")
            except Exception as e:
                print(f"⚠️ خطا: {e}")
            bot.polling(none_stop=True, interval=3, timeout=60, long_polling_timeout=60)
        except Exception as e:
            retry_count += 1
            print(f"⚠️ خطا (تلاش {retry_count}/{MAX_RETRIES}): {e}")
            time.sleep(RETRY_DELAY)
            try:
                bot = telebot.TeleBot(TOKEN)
                bot.session = session
                bot.remove_webhook()
            except:
                pass
    print("\n❌ ربات متوقف شد!")


if __name__ == "__main__":
    run_bot()
