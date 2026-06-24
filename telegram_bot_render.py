# telegram_bot.py - نسخه پایدار با افزایش timeout و مدیریت بهتر اتصال

import telebot
from telebot import apihelper
from bot_api import BotAPI
import jdatetime
import re
import os
import json
import time
import sys
import shutil
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

# ===== غیرفعال کردن هشدارهای SSL =====
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===== تنظیم encoding برای ویندوز =====
if sys.platform == 'win32':
    try:
        import codecs
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except Exception:
        pass

TOKEN = "8705261999:AAF34fID3LoF0_yiXVGKiwyStWNtb6zUIwo"

# ===== تنظیم timeout در سطح کتابخانه (مهم) =====
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 60

# ===== تنظیمات ویژه برای اتصال پایدار =====
session = requests.Session()
retry = Retry(
    total=5,
    read=5,
    connect=5,
    backoff_factor=0.5,  # افزایش فاکتور پشتیبان
    status_forcelist=(500, 502, 503, 504)
)
adapter = HTTPAdapter(
    max_retries=retry,
    pool_connections=20,  # افزایش تعداد اتصالات
    pool_maxsize=20
)
session.mount('http://', adapter)
session.mount('https://', adapter)

bot = telebot.TeleBot(TOKEN)
bot.session = session

# دیکشنری‌ها
user_states = {}
user_member_ids = {}
user_temp_data = {}
CHAT_IDS_FILE = "user_chat_ids.json"
MAX_RETRIES = 20  # افزایش تعداد تلاش‌ها
RETRY_DELAY = 15  # افزایش زمان بین تلاش‌ها
SUPPORT_PHONE = "09387026799"

print("=" * 60)
print("🤖 ربات تلگرام صندوق قرض‌الحسنه ۱۴ معصوم")
print("📱 شناسه ربات: @sandoogh14_bot")
print("✅ در حال اجرا...")
print("=" * 60)


# ============================================================
# ===== کیبوردهای ربات =====
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
# ===== توابع مدیریت chat_id =====
# ============================================================
def save_chat_id(phone, chat_id):
    if not phone:
        return
    data = {}
    if os.path.exists(CHAT_IDS_FILE):
        try:
            with open(CHAT_IDS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = {}
    data[str(phone)] = chat_id
    with open(CHAT_IDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ chat_id {chat_id} براي شماره {phone} ذخيره شد")


def get_chat_id(phone):
    if not phone:
        return None
    if os.path.exists(CHAT_IDS_FILE):
        try:
            with open(CHAT_IDS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(str(phone))
        except:
            return None
    return None


# ============================================================
# ===== هندلر دکمه بازگشت =====
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
        "🔙 **به منوی اصلی بازگشتید.**\n\n"
        "📌 از گزینه‌های زیر استفاده کنید:",
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
            "⚠️ اگر كد عضويت نداريد، لطفاً با پشتيباني تماس بگيريد:\n"
            f"📞 پشتيباني: {SUPPORT_PHONE}",
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
            else:
                bot.reply_to(
                    message,
                    f"⚠️ **توجه:** شماره همراه شما در سيستم ثبت نشده است!\n\n"
                    f"براي دريافت پيام‌هاي تاييديه، لطفاً با مدير تماس بگيريد.\n"
                    f"📞 پشتيباني: {SUPPORT_PHONE}",
                    reply_markup=get_main_keyboard()
                )
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
                f"❌ كد عضويت {code} يافت نشد!\n\n"
                "📌 لطفاً دوباره تلاش كنيد.",
                reply_markup=get_cancel_keyboard()
            )
            msg = bot.reply_to(message, "📝 كد عضويت خود را وارد كنيد:")
            bot.register_next_step_handler(msg, process_code)
            
    except ValueError:
        bot.reply_to(
            message,
            "❌ كد عضويت بايد عدد باشد!",
            reply_markup=get_cancel_keyboard()
        )
        msg = bot.reply_to(message, "📝 كد عضويت خود را وارد كنيد:")
        bot.register_next_step_handler(msg, process_code)
    except Exception as e:
        print(f"❌ خطا در process_code: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}")


# ============================================================
# ===== راهنمای کامل =====
# ============================================================
@bot.message_handler(func=lambda m: m.text == "5️⃣ راهنمای کامل" or m.text == "5")
def help_handler(message):
    try:
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
        text += "• براي انصراف از هر مرحله، دكمه 'لغو' را بزنيد.\n"
        text += "• براي تكميل درخواست وام، كلمه **'تكميل'** را وارد كنيد.\n"
        text += f"📞 پشتيباني: {SUPPORT_PHONE}"
        
        bot.reply_to(message, text, reply_markup=get_back_keyboard())
    except Exception as e:
        print(f"❌ خطا در help_handler: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}", reply_markup=get_main_keyboard())


# ============================================================
# ===== ثبت واریزی (تابع‌های اصلی) =====
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
            "📝 **ثبت واريزي جديد**\n\n"
            "مرحله 1 از 3:\n"
            "لطفاً **مبلغ كل واريزي** را به ريال وارد كنيد.\n\n"
            "مثال: 10000000\n\n"
            "➖ براي انصراف، دكمه 'لغو' را بزنيد.",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, process_register_total)
    except Exception as e:
        print(f"❌ خطا در register_start: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}")


def process_register_total(message):
    user_id = message.from_user.id
    if message.text == "❌ لغو":
        user_states[user_id] = 'main'
        if user_id in user_temp_data:
            del user_temp_data[user_id]
        bot.reply_to(message, "✅ ثبت واريزي لغو شد.", reply_markup=get_main_keyboard())
        return
    
    try:
        total = int(message.text.replace(',', '').strip())
        if total <= 0:
            bot.reply_to(message, "❌ مبلغ كل بايد بزرگتر از صفر باشد!", reply_markup=get_cancel_keyboard())
            msg = bot.reply_to(message, "📝 مبلغ كل واريزي را وارد كنيد:")
            bot.register_next_step_handler(msg, process_register_total)
            return
        
        user_temp_data[user_id]['total'] = total
        user_temp_data[user_id]['step'] = 'subscription'
        
        msg = bot.reply_to(
            message,
            f"✅ مبلغ كل: {total:,} ريال\n\n"
            "مرحله 2 از 3:\n"
            "لطفاً **مبلغ حق اشتراك** را به ريال وارد كنيد.\n\n"
            "مثال: 5000000\n\n"
            "➖ براي انصراف، دكمه 'لغو' را بزنيد.",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, process_register_subscription)
        
    except ValueError:
        bot.reply_to(message, "❌ لطفاً فقط عدد وارد كنيد!\nمثال: 10000000", reply_markup=get_cancel_keyboard())
        msg = bot.reply_to(message, "📝 مبلغ كل واريزي را وارد كنيد:")
        bot.register_next_step_handler(msg, process_register_total)
    except Exception as e:
        print(f"❌ خطا در process_register_total: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}")


def process_register_subscription(message):
    user_id = message.from_user.id
    if message.text == "❌ لغو":
        user_states[user_id] = 'main'
        if user_id in user_temp_data:
            del user_temp_data[user_id]
        bot.reply_to(message, "✅ ثبت واريزي لغو شد.", reply_markup=get_main_keyboard())
        return
    
    try:
        subscription = int(message.text.replace(',', '').strip())
        total = user_temp_data[user_id]['total']
        
        if subscription < 0:
            bot.reply_to(message, "❌ مبلغ اشتراك نمي تواند منفي باشد!", reply_markup=get_cancel_keyboard())
            msg = bot.reply_to(message, "📝 مبلغ حق اشتراك را وارد كنيد:")
            bot.register_next_step_handler(msg, process_register_subscription)
            return
        
        if subscription > total:
            bot.reply_to(
                message,
                f"❌ مبلغ اشتراك ({subscription:,} ريال) از مبلغ كل ({total:,} ريال) بيشتر است!",
                reply_markup=get_cancel_keyboard()
            )
            msg = bot.reply_to(message, "📝 مبلغ حق اشتراك را وارد كنيد:")
            bot.register_next_step_handler(msg, process_register_subscription)
            return
        
        user_temp_data[user_id]['subscription'] = subscription
        user_temp_data[user_id]['step'] = 'installment'
        
        remaining = total - subscription
        msg = bot.reply_to(
            message,
            f"✅ مبلغ كل: {total:,} ريال\n"
            f"✅ مبلغ اشتراك: {subscription:,} ريال\n"
            f"📌 باقيمانده: {remaining:,} ريال\n\n"
            "مرحله 3 از 3:\n"
            "لطفاً **مبلغ قسط پرداختي** را به ريال وارد كنيد.\n\n"
            "مثال: 2000000\n"
            "(اگر قسطي پرداخت نمي كنيد، عدد 0 را وارد كنيد)\n\n"
            "➖ براي انصراف، دكمه 'لغو' را بزنيد.",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, process_register_installment)
        
    except ValueError:
        bot.reply_to(message, "❌ لطفاً فقط عدد وارد كنيد!\nمثال: 5000000", reply_markup=get_cancel_keyboard())
        msg = bot.reply_to(message, "📝 مبلغ حق اشتراك را وارد كنيد:")
        bot.register_next_step_handler(msg, process_register_subscription)
    except Exception as e:
        print(f"❌ خطا در process_register_subscription: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}")


def process_register_installment(message):
    user_id = message.from_user.id
    if message.text == "❌ لغو":
        user_states[user_id] = 'main'
        if user_id in user_temp_data:
            del user_temp_data[user_id]
        bot.reply_to(message, "✅ ثبت واريزي لغو شد.", reply_markup=get_main_keyboard())
        return
    
    try:
        installment = int(message.text.replace(',', '').strip())
        total = user_temp_data[user_id]['total']
        subscription = user_temp_data[user_id]['subscription']
        
        if installment < 0:
            bot.reply_to(message, "❌ مبلغ قسط نمي تواند منفي باشد!", reply_markup=get_cancel_keyboard())
            msg = bot.reply_to(message, "📝 مبلغ قسط را وارد كنيد:")
            bot.register_next_step_handler(msg, process_register_installment)
            return
        
        if installment > (total - subscription):
            bot.reply_to(
                message,
                f"❌ مبلغ قسط ({installment:,} ريال) از باقيمانده ({total - subscription:,} ريال) بيشتر است!",
                reply_markup=get_cancel_keyboard()
            )
            msg = bot.reply_to(message, "📝 مبلغ قسط را وارد كنيد:")
            bot.register_next_step_handler(msg, process_register_installment)
            return
        
        member_code = user_member_ids.get(user_id)
        api = BotAPI()
        member = api.get_member_by_id(int(member_code))
        
        if not member:
            api.close()
            bot.reply_to(message, "❌ اطلاعات شما يافت نشد!", reply_markup=get_main_keyboard())
            user_states[user_id] = 'main'
            if user_id in user_temp_data:
                del user_temp_data[user_id]
            return
        
        result = api.register_transaction(
            member_id=member['id'],
            amount=total,
            subscription=subscription,
            installment=installment,
            source='bot'
        )
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
            summary += f"🆔 كد عضويت: {member['id']}\n"
            summary += f"📅 تاريخ: {today.strftime('%Y/%m/%d')} ({month_name})\n"
            summary += f"💰 مبلغ كل: {total:,} ريال\n"
            summary += f"📊 اشتراك: {subscription:,} ريال\n"
            summary += f"💳 قسط: {installment:,} ريال\n"
            summary += f"📌 شماره تراكنش: {result['transaction_id']}\n\n"
            summary += f"⏳ **وضعيت:** در انتظار تاييد مدير"
            
            bot.reply_to(message, summary, reply_markup=get_back_keyboard())
        else:
            bot.reply_to(message, f"❌ خطا: {result.get('message', 'خطاي نامشخص')}", reply_markup=get_back_keyboard())
        
    except ValueError:
        bot.reply_to(message, "❌ لطفاً فقط عدد وارد كنيد!\nمثال: 2000000", reply_markup=get_cancel_keyboard())
        msg = bot.reply_to(message, "📝 مبلغ قسط را وارد كنيد:")
        bot.register_next_step_handler(msg, process_register_installment)
    except Exception as e:
        print(f"❌ خطا در process_register_installment: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}", reply_markup=get_back_keyboard())


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
            bot.reply_to(message, "❌ اطلاعات شما يافت نشد!", reply_markup=get_back_keyboard())
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
            "💰 **درخواست وام**\n\n"
            "مرحله 1 از 2:\n"
            "لطفاً **مبلغ وام** مورد نظر را به ريال وارد كنيد.\n"
            "مثال: 50000000\n\n"
            "⚠️ حداقل مبلغ: 500,000 ريال\n"
            "⚠️ حداكثر مبلغ: 2 ميليارد ريال\n\n"
            "➖ براي انصراف، دكمه 'لغو' را بزنيد.",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, process_loan_amount)
    except Exception as e:
        print(f"❌ خطا در loan_start: {e}")
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
            bot.reply_to(message, "❌ حداقل مبلغ وام 500,000 ريال است.", reply_markup=get_cancel_keyboard())
            msg = bot.reply_to(message, "📝 مبلغ وام را وارد كنيد:")
            bot.register_next_step_handler(msg, process_loan_amount)
            return
        
        if amount > 2000000000:
            bot.reply_to(message, "❌ حداكثر مبلغ وام 2 ميليارد ريال است.", reply_markup=get_cancel_keyboard())
            msg = bot.reply_to(message, "📝 مبلغ وام را وارد كنيد:")
            bot.register_next_step_handler(msg, process_loan_amount)
            return
        
        user_temp_data[user_id]['amount'] = amount
        user_states[user_id] = 'loan_document'
        
        msg = bot.reply_to(
            message,
            f"✅ مبلغ وام: {amount:,} ريال\n\n"
            "مرحله 2 از 2:\n"
            "📎 **لطفاً مدارك را ارسال كنيد** (تصوير يا PDF)\n"
            "📌 براي تكميل بدون مدرك، كلمه **'تكميل'** را وارد كنيد.\n\n"
            "➖ براي انصراف، دكمه 'لغو' را بزنيد.",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, process_loan_document)
        
    except ValueError:
        bot.reply_to(message, "❌ لطفاً مبلغ را به عدد وارد كنيد!", reply_markup=get_cancel_keyboard())
        msg = bot.reply_to(message, "📝 مبلغ وام را وارد كنيد:")
        bot.register_next_step_handler(msg, process_loan_amount)
    except Exception as e:
        print(f"❌ خطا در process_loan_amount: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}", reply_markup=get_main_keyboard())


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
            bot.reply_to(message, "❌ اطلاعات شما يافت نشد!", reply_markup=get_back_keyboard())
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
            loan_date = loan.get('date', '')
            
            if amount > 0:
                progress = int(((amount - remaining) / amount) * 100)
                if progress > 100:
                    progress = 100
                if progress < 0:
                    progress = 0
            else:
                progress = 0
            
            if status == 'active' and remaining > 0:
                status_text = "🟢 فعال"
            elif status == 'settled' or remaining == 0:
                status_text = "✅ تسويه شده"
            else:
                status_text = "🔴 نامشخص"
            
            paid_amount = amount - remaining if remaining >= 0 else amount
            
            text = f"📊 **وضعيت وام شما**\n\n"
            text += f"👤 عضو: {member['name']}\n"
            text += f"🆔 كد عضويت: {member['id']}\n"
            text += f"💰 مبلغ وام: {amount:,} ريال\n"
            
            if remaining > 0:
                text += f"📈 مانده: {remaining:,} ريال\n"
            else:
                text += f"📈 مانده: 0 ريال (تسويه شده)\n"
            
            text += f"💳 مبلغ پرداختي: {paid_amount:,} ريال\n"
            text += f"📊 پيشرفت: {progress}%\n"
            text += f"📌 وضعيت: {status_text}\n"
            
            if total_installments > 0:
                text += f"🔄 اقساط: {paid_installments}/{total_installments}\n"
            
            if monthly > 0:
                text += f"💳 قسط ماهانه: {monthly:,} ريال\n"
            
            if loan_date:
                text += f"📅 تاريخ اعطا: {loan_date}\n"
            
            if remaining > 0 and monthly > 0:
                remaining_months = (remaining + monthly - 1) // monthly
                text += f"\n📌 **تعداد اقساط باقيمانده:** حدود {remaining_months} ماه"
        else:
            text = "❌ **شما وام فعالی نداريد.**\n\n"
            text += "📌 برای دريافت وام، از گزينه 3️⃣ استفاده كنيد."
        
        bot.reply_to(message, text, reply_markup=get_back_keyboard())
        
    except Exception as e:
        print(f"❌ خطا در loan_status_handler: {e}")
        bot.reply_to(message, f"❌ خطا: {str(e)}", reply_markup=get_back_keyboard())


# ============================================================
# ===== پیام‌های نامشخص =====
# ============================================================
@bot.message_handler(func=lambda m: True)
def unknown_handler(message):
    user_id = message.from_user.id
    try:
        if user_id in user_states and user_states[user_id] == 'register':
            bot.reply_to(message, "📝 لطفاً اطلاعات را وارد كنيد يا 'لغو' را بزنيد.", reply_markup=get_cancel_keyboard())
            return
        
        if user_id in user_states and user_states[user_id] == 'loan_amount':
            bot.reply_to(message, "💰 مبلغ وام را وارد كنيد يا 'لغو' را بزنيد.", reply_markup=get_cancel_keyboard())
            return
        
        if user_id not in user_member_ids:
            bot.reply_to(message, "❌ ابتدا كد عضويت خود را وارد كنيد!", reply_markup=get_main_keyboard())
            return
        
        bot.reply_to(message, "❌ گزينه نامعتبر!\n📌 لطفاً از منو استفاده كنيد.", reply_markup=get_main_keyboard())
    except Exception as e:
        print(f"❌ خطا در unknown_handler: {e}")


# ============================================================
# ===== تابع اصلی با مدیریت خطا و بازیابی =====
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
                print(f"⚠️ خطا در پاك كردن webhook: {e}")
            
            bot.polling(
                none_stop=True,
                interval=3,
                timeout=60,
                long_polling_timeout=60
            )
            
        except requests.exceptions.ConnectionError as e:
            retry_count += 1
            print(f"⚠️ خطاي اتصال (تلاش {retry_count}/{MAX_RETRIES}): {e}")
            print(f"🔄 تلاش مجدد در {RETRY_DELAY} ثانيه...")
            time.sleep(RETRY_DELAY)
            
            try:
                bot = telebot.TeleBot(TOKEN)
                bot.session = session
                bot.remove_webhook()
                print("🔄 ربات بازنشاني شد")
            except Exception as reset_error:
                print(f"❌ خطا در بازنشاني ربات: {reset_error}")
                
        except Exception as e:
            retry_count += 1
            print(f"⚠️ خطا در اجراي ربات (تلاش {retry_count}/{MAX_RETRIES}): {e}")
            
            if "ConnectionResetError" in str(e) or "Connection aborted" in str(e):
                print("🔄 خطاي قطع اتصال، تلاش مجدد...")
                time.sleep(RETRY_DELAY)
                
                try:
                    bot = telebot.TeleBot(TOKEN)
                    bot.session = session
                    bot.remove_webhook()
                    print("🔄 ربات بازنشاني شد")
                except Exception as reset_error:
                    print(f"❌ خطا در بازنشاني ربات: {reset_error}")
            else:
                time.sleep(5)
    
    print("\n❌ ربات پس از چندين تلاش متوقف شد!")
    print("📌 لطفاً خطاها را بررسي كنيد.")


if __name__ == "__main__":
    run_bot()
