import sqlite3
from database import get_connection
from datetime import datetime, timedelta

def calculate_required_accumulated(loan_amount):
    """
    محاسبه انباشته لازم برای وام مورد نظر
    قانون: انباشته لازم = 50% مبلغ وام
    """
    return loan_amount // 2

def check_loan_eligibility(member_id, requested_amount):
    """
    بررسی شرایط دریافت وام
    بازگشت: (is_eligible, message, required_accumulated, current_accumulated)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. بررسی اقساط معوق
        cursor.execute("""
            SELECT COUNT(*) FROM installments i
            JOIN loans l ON i.loan_id = l.id
            WHERE l.member_id = ? AND i.paid = 0 AND i.due_date < date('now')
        """, (member_id,))
        overdue_installments = cursor.fetchone()[0]
        
        if overdue_installments > 0:
            return False, f"❌ شما {overdue_installments} قسط معوق دارید. ابتدا اقساط را تسویه کنید.", 0, 0
        
        # 2. محاسبه انباشته فعلی
        cursor.execute("""
            SELECT SUM(amount_subscription) - SUM(amount_installment)
            FROM transactions
            WHERE member_id = ? AND confirmed = 1
        """, (member_id,))
        current_accumulated = cursor.fetchone()[0] or 0
        
        # 3. انباشته لازم
        required_accumulated = calculate_required_accumulated(requested_amount)
        
        # 4. شرط 75% هنگام درخواست
        required_at_request = int(required_accumulated * 0.75)
        
        if current_accumulated < required_at_request:
            return False, f"❌ انباشته شما برای درخواست این وام کافی نیست.\n📊 انباشته فعلی: {current_accumulated:,} تومان\n💰 نیاز حداقل هنگام درخواست: {required_at_request:,} تومان\n🎯 انباشته نهایی مورد نیاز: {required_accumulated:,} تومان", required_accumulated, current_accumulated
        
        return True, "✅ شرایط دریافت وام را دارید.", required_accumulated, current_accumulated

def calculate_loan_installments(loan_amount, months, fee_percent=5):
    """
    محاسبه اقساط وام با کارمزد
    بازگشت: (total_amount, monthly_installment)
    """
    fee_amount = int(loan_amount * fee_percent / 100)
    total_amount = loan_amount + fee_amount
    monthly_installment = total_amount // months
    return total_amount, monthly_installment

def get_whatsapp_report():
    """
    تولید گزارش برای ارسال در واتساپ
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # اعضای معوق (بیش از 3 ماه واریز نداشته‌اند)
        cursor.execute("""
            SELECT m.name, MAX(t.date) as last_payment
            FROM members m
            LEFT JOIN transactions t ON m.id = t.member_id AND t.confirmed = 1
            WHERE m.is_active = 1
            GROUP BY m.id
            HAVING last_payment IS NULL OR julianday('now') - julianday(last_payment) > 90
        """)
        overdue_members = cursor.fetchall()
        
        # صف انتظار وام
        cursor.execute("""
            SELECT r.id, m.name, r.requested_amount, r.accumulated_at_request
            FROM loan_requests r
            JOIN members m ON r.member_id = m.id
            WHERE r.status = 'pending'
            ORDER BY r.request_date ASC
            LIMIT 5
        """)
        queue = cursor.fetchall()
        
        # تولید متن گزارش
        report = "🏦 **صندوق قرض‌الحسنه ۱۴ معصوم**\n"
        report += f"📅 گزارش ماهانه - {datetime.now().strftime('%Y/%m/%d')}\n\n"
        
        report += "🔴 **اعضای دارای اقساط معوق:**\n"
        if overdue_members:
            for member in overdue_members:
                report += f"- {member[0]}\n"
        else:
            report += "- هیچ عضو معوقی نداریم ✅\n"
        
        report += "\n🟡 **صف انتظار وام (۵ نفر بعدی):**\n"
        if queue:
            for i, q in enumerate(queue, 1):
                report += f"{i}. {q[1]} - درخواست {q[2]:,} تومان\n"
        else:
            report += "- هیچ درخواست وامی در صف نیست\n"
        
        report += "\n📌 لطفاً اقساط خود را به شماره حساب:\n"
        report += "**۴۰۱۳۳۸۱۵۰** بانک رفاه واریز کنید.\n"
        report += "و رسید را در ربات ارسال نمایید.\n"
        
        return report

def get_member_accumulated_history(member_id):
    """
    دریافت تاریخچه انباشته عضو
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, amount_subscription, amount_installment,
                   SUM(amount_subscription) OVER (ORDER BY date) - SUM(amount_installment) OVER (ORDER BY date) as accumulated
            FROM transactions
            WHERE member_id = ? AND confirmed = 1
            ORDER BY date
        """, (member_id,))
        return cursor.fetchall()
