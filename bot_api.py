# bot_api.py - نسخه کامل با متد request_loan_with_doc

from database import get_connection
import jdatetime

class BotAPI:
    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()
    
    def close(self):
        self.conn.close()
    
    # ===== دریافت عضو با کد عضویت =====
    def get_member_by_id(self, member_id):
        """دریافت اطلاعات عضو بر اساس کد عضویت"""
        self.cursor.execute("""
            SELECT id, name, phone, member_type, initial_accumulated, is_active
            FROM members WHERE id = ? AND is_active = 1
        """, (member_id,))
        result = self.cursor.fetchone()
        if result:
            return {
                'id': result[0],
                'name': result[1],
                'phone': result[2] if result[2] else "",
                'member_type': result[3],
                'accumulated': result[4] if result[4] else 0,
                'is_active': result[5]
            }
        return None
    
    # ===== دریافت عضو با شماره همراه =====
    def get_member_by_phone(self, phone):
        """دریافت اطلاعات عضو بر اساس شماره همراه"""
        if not phone:
            return None
        self.cursor.execute("""
            SELECT id, name, phone, member_type, initial_accumulated, is_active
            FROM members WHERE phone = ? AND is_active = 1
        """, (phone,))
        result = self.cursor.fetchone()
        if result:
            return {
                'id': result[0],
                'name': result[1],
                'phone': result[2] if result[2] else "",
                'member_type': result[3],
                'accumulated': result[4] if result[4] else 0,
                'is_active': result[5]
            }
        return None
    
    # ===== ثبت نام خودکار =====
    def auto_register_member(self, phone, name=None):
        """ثبت نام خودکار عضو"""
        if not phone:
            return None
        
        existing = self.get_member_by_phone(phone)
        if existing:
            return existing
        
        if not name:
            name = f"عضو {phone[-4:]}"
        
        today = jdatetime.date.today().strftime("%Y/%m/%d")
        self.cursor.execute("""
            INSERT INTO members (name, phone, initial_accumulated, join_date, member_type, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, phone, 0, today, 0, 1))
        self.conn.commit()
        
        return {
            'id': self.cursor.lastrowid,
            'name': name,
            'phone': phone,
            'accumulated': 0,
            'is_active': 1
        }
    
    # ===== دریافت اطلاعات مالی =====
    def get_member_balance(self, member_id):
        """دریافت اطلاعات مالی عضو"""
        self.cursor.execute("SELECT initial_accumulated FROM members WHERE id = ?", (member_id,))
        result = self.cursor.fetchone()
        accumulated = result[0] if result and result[0] else 0
        
        self.cursor.execute("SELECT remaining_amount FROM loans WHERE member_id = ? AND status = 'active'", (member_id,))
        loan = self.cursor.fetchone()
        loan_remaining = loan[0] if loan else 0
        
        self.cursor.execute("""
            SELECT date, amount_total, amount_subscription, amount_installment, confirmed, source
            FROM transactions 
            WHERE member_id = ? 
            ORDER BY id DESC LIMIT 5
        """, (member_id,))
        last_transactions = self.cursor.fetchall()
        
        return {
            'member_id': member_id,
            'accumulated': accumulated,
            'loan_remaining': loan_remaining,
            'last_transactions': last_transactions
        }
    
    # ===== ثبت واریزی =====
    def register_transaction(self, member_id, amount, subscription, installment, date=None, source='bot'):
        """ثبت واریزی جدید"""
        if date is None:
            date = jdatetime.date.today().strftime("%Y/%m/%d")
        
        self.cursor.execute("""
            INSERT INTO transactions 
            (member_id, date, amount_total, amount_subscription, amount_installment, confirmed, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (member_id, date, amount, subscription, installment, 0, source))
        self.conn.commit()
        
        return {
            'success': True,
            'transaction_id': self.cursor.lastrowid,
            'member_id': member_id,
            'status': 'pending'
        }
    
    # ===== ثبت درخواست وام =====
    def request_loan(self, member_id, amount, description=""):
        """ثبت درخواست وام"""
        self.cursor.execute("SELECT id FROM loans WHERE member_id = ? AND status = 'active'", (member_id,))
        if self.cursor.fetchone():
            return {'success': False, 'message': 'شما وام فعال دارید!'}
        
        today = jdatetime.date.today()
        year = str(today.year)
        self.cursor.execute("SELECT COUNT(*) FROM secretariat_requests")
        count = self.cursor.fetchone()[0] + 1
        secretariat_no = f"{year}-{str(count).zfill(4)}"
        
        self.cursor.execute("""
            INSERT INTO secretariat_requests 
            (secretariat_no, member_id, amount, description, request_date, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (secretariat_no, member_id, amount, description, today.strftime("%Y/%m/%d"), 'bot'))
        self.conn.commit()
        
        return {
            'success': True,
            'secretariat_no': secretariat_no,
            'message': f'درخواست وام با شماره {secretariat_no} ثبت شد!'
        }
    
    # ===== ثبت درخواست وام با مدارک (متد جدید) =====
    def request_loan_with_doc(self, member_id, amount, doc_path, description=""):
        """ثبت درخواست وام با مدارک"""
        # بررسی وام فعال
        self.cursor.execute("SELECT id FROM loans WHERE member_id = ? AND status = 'active'", (member_id,))
        if self.cursor.fetchone():
            return {'success': False, 'message': 'شما وام فعال دارید!'}
        
        today = jdatetime.date.today()
        year = str(today.year)
        self.cursor.execute("SELECT COUNT(*) FROM secretariat_requests")
        count = self.cursor.fetchone()[0] + 1
        secretariat_no = f"{year}-{str(count).zfill(4)}"
        
        # ثبت درخواست با مسیر مدارک
        self.cursor.execute("""
            INSERT INTO secretariat_requests 
            (secretariat_no, member_id, amount, doc_path, description, request_date, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (secretariat_no, member_id, amount, doc_path, description, today.strftime("%Y/%m/%d"), 'bot'))
        self.conn.commit()
        
        return {
            'success': True,
            'secretariat_no': secretariat_no,
            'message': f'درخواست وام با شماره {secretariat_no} ثبت شد!'
        }
    
    # ===== دریافت وضعیت وام =====
    def get_member_loan_status(self, member_id):
        """دریافت وضعیت وام عضو"""
        self.cursor.execute("""
            SELECT id, amount, remaining_amount, monthly_installment, 
                   paid_installments, total_installments, status, date
            FROM loans 
            WHERE member_id = ? 
            ORDER BY id DESC LIMIT 1
        """, (member_id,))
        loan = self.cursor.fetchone()
        
        if loan:
            return {
                'id': loan[0],
                'amount': loan[1],
                'remaining': loan[2],
                'monthly': loan[3],
                'paid': loan[4],
                'total': loan[5],
                'status': loan[6],
                'date': loan[7]
            }
        return None
