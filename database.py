# database.py - مدیریت اتصال به دیتابیس

import sqlite3
import os

DB_PATH = "fund.db"

def get_connection():
    """دریافت اتصال به دیتابیس"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ خطا در اتصال به دیتابیس: {e}")
        return None

def init_db():
    """ایجاد جداول اولیه دیتابیس"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # جدول اعضا
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            member_type INTEGER DEFAULT 0,
            initial_accumulated INTEGER DEFAULT 0,
            join_date TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # جدول تراکنش‌ها
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            amount_total INTEGER NOT NULL,
            amount_subscription INTEGER NOT NULL,
            amount_installment INTEGER DEFAULT 0,
            confirmed INTEGER DEFAULT 0,
            source TEXT DEFAULT 'desktop',
            FOREIGN KEY (member_id) REFERENCES members(id)
        )
    """)
    
    # جدول وام‌ها
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            remaining_amount INTEGER NOT NULL,
            monthly_installment INTEGER NOT NULL,
            paid_installments INTEGER DEFAULT 0,
            total_installments INTEGER DEFAULT 40,
            status TEXT DEFAULT 'active',
            date TEXT NOT NULL,
            FOREIGN KEY (member_id) REFERENCES members(id)
        )
    """)
    
    # جدول درخواست‌های وام
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loan_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            accumulated INTEGER NOT NULL,
            request_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            secretariat_id INTEGER,
            FOREIGN KEY (member_id) REFERENCES members(id)
        )
    """)
    
    # جدول دبیرخانه
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS secretariat_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            secretariat_no TEXT NOT NULL,
            member_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            doc_path TEXT,
            description TEXT,
            status TEXT DEFAULT 'در انتظار',
            request_date TEXT NOT NULL,
            source TEXT DEFAULT 'desktop',
            FOREIGN KEY (member_id) REFERENCES members(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ دیتابیس با موفقیت ساخته شد!")

if __name__ == "__main__":
    init_db()
