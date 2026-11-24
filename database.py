"""
KUBERA BANK - Database Setup
------------------------------
This file creates and manages the SQLite database.
All tables (users, accounts, transactions, etc.) are defined here.
"""

import sqlite3
import os
from config import Config

def get_db_connection():
    """
    Create and return a database connection.
    We use row_factory so we can access columns by name (like a dictionary).
    """
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Access results like: row['column_name']
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key support
    return conn

def initialize_database():
    """
    Create all database tables if they don't already exist.
    This function runs when the app starts.
    """
    # Make sure the database directory exists
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    os.makedirs(Config.STATEMENTS_FOLDER, exist_ok=True)
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    conn = get_db_connection()
    cursor = conn.cursor()

    # =============================================
    # TABLE 1: Users (login information)
    # =============================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT    UNIQUE NOT NULL,
            full_name   TEXT    NOT NULL,
            email       TEXT    UNIQUE NOT NULL,
            phone       TEXT    NOT NULL,
            password    TEXT    NOT NULL,
            is_admin    INTEGER DEFAULT 0,
            created_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    ''')

    # =============================================
    # TABLE 2: Accounts (bank account details)
    # =============================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL,
            account_number TEXT    UNIQUE NOT NULL,
            account_type   TEXT    NOT NULL,
            balance        REAL    DEFAULT 0.0,
            address        TEXT,
            date_of_birth  TEXT,
            is_active      INTEGER DEFAULT 1,
            created_at     TEXT    DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # =============================================
    # TABLE 3: Transactions (every money movement)
    # =============================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id   TEXT    UNIQUE NOT NULL,
            account_id       INTEGER NOT NULL,
            transaction_type TEXT    NOT NULL,
            amount           REAL    NOT NULL,
            balance_after    REAL    NOT NULL,
            description      TEXT,
            reference_account TEXT,
            created_at       TEXT    DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')

    # =============================================
    # TABLE 4: Loan Applications
    # =============================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loan_applications (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id   TEXT    UNIQUE NOT NULL,
            user_id          INTEGER NOT NULL,
            loan_type        TEXT    NOT NULL,
            amount           REAL    NOT NULL,
            monthly_income   REAL    NOT NULL,
            employment_status TEXT   NOT NULL,
            duration_months  INTEGER NOT NULL,
            reason           TEXT,
            status           TEXT    DEFAULT 'Pending',
            admin_note       TEXT,
            created_at       TEXT    DEFAULT (datetime('now', 'localtime')),
            updated_at       TEXT    DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # =============================================
    # TABLE 5: Credit Card Applications
    # =============================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credit_card_applications (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id  TEXT    UNIQUE NOT NULL,
            user_id         INTEGER NOT NULL,
            card_type       TEXT    NOT NULL,
            annual_income   REAL    NOT NULL,
            employment_type TEXT    NOT NULL,
            status          TEXT    DEFAULT 'Pending',
            admin_note      TEXT,
            created_at      TEXT    DEFAULT (datetime('now', 'localtime')),
            updated_at      TEXT    DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # =============================================
    # TABLE 6: Notifications
    # =============================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            message    TEXT    NOT NULL,
            is_read    INTEGER DEFAULT 0,
            created_at TEXT    DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")


def create_admin_user():
    """
    Create the default admin user if one doesn't exist.
    Admin can approve/reject loans and credit card applications.
    """
    from werkzeug.security import generate_password_hash

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if admin already exists
    existing_admin = cursor.execute(
        'SELECT id FROM users WHERE is_admin = 1'
    ).fetchone()

    if not existing_admin:
        # Create admin account
        cursor.execute('''
            INSERT INTO users (customer_id, full_name, email, phone, password, is_admin)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            'ADMIN001',
            'Kubera Admin',
            'admin@kuberabank.com',
            '9999999999',
            generate_password_hash(Config.ADMIN_PASSWORD),
            1
        ))
        conn.commit()
        print("✅ Admin user created: admin@kuberabank.com / kubera@admin2024")

    conn.close()
