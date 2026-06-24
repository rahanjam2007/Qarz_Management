# models.py - مدل‌های دیتابیس

from database import get_connection
import jdatetime

class Member:
    @staticmethod
    def create(name, phone, initial_accumulated=0, join_date=None):
        if join_date is None:
            join_date = jdatetime.date.today().strftime("%Y/%m/%d")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO members (name, phone, initial_accumulated, join_date, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, (name, phone, initial_accumulated, join_date))
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    @staticmethod
    def get_all():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE is_active = 1 ORDER BY name")
        result = cursor.fetchall()
        conn.close()
        return result
    
    @staticmethod
    def get_by_id(member_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    @staticmethod
    def update_phone(member_id, phone):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE members SET phone = ? WHERE id = ?", (phone, member_id))
        conn.commit()
        conn.close()

class Transaction:
    @staticmethod
    def create(member_id, date, amount_total, amount_subscription, amount_installment=0):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (member_id, date, amount_total, amount_subscription, amount_installment, confirmed)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (member_id, date, amount_total, amount_subscription, amount_installment))
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    @staticmethod
    def confirm(transaction_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE transactions SET confirmed = 1 WHERE id = ?", (transaction_id,))
        conn.commit()
        conn.close()

class Loan:
    @staticmethod
    def create(member_id, amount, monthly_installment, total_installments, date):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO loans (member_id, amount, remaining_amount, monthly_installment, total_installments, date, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
        """, (member_id, amount, amount, monthly_installment, total_installments, date))
        conn.commit()
        conn.close()
        return cursor.lastrowid

class LoanRequest:
    @staticmethod
    def create(member_id, amount, accumulated):
        date = jdatetime.date.today().strftime("%Y/%m/%d")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO loan_requests (member_id, amount, accumulated, request_date)
            VALUES (?, ?, ?, ?)
        """, (member_id, amount, accumulated, date))
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    @staticmethod
    def get_queue():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT lr.*, m.name as member_name
            FROM loan_requests lr
            JOIN members m ON lr.member_id = m.id
            WHERE lr.status = 'pending'
            ORDER BY lr.id ASC
        """)
        result = cursor.fetchall()
        conn.close()
        return result
