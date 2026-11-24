"""
KUBERA BANK - Main Application File
--------------------------------------
This is the heart of our Flask web application.
All routes (web pages) and API endpoints are defined here.

Run this file to start the web server:
    python app.py
"""

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, send_file
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import uuid
import random
import string
import secrets
from datetime import datetime

from config import Config
from database import get_db_connection, initialize_database, create_admin_user

# ==========================================
# APP SETUP
# ==========================================
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# CSRF Token Generator & Validator
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

@app.before_request
def csrf_protect():
    """Verify CSRF token on all POST form submissions"""
    if request.method == "POST":
        # Allow internal JSON APIs
        if request.path.startswith('/api/'):
            return
        token = session.get('_csrf_token')
        form_token = request.form.get('csrf_token')
        if not token or not form_token or token != form_token:
            flash('Security check failed: Invalid or expired token. Please try again.', 'danger')
            return redirect(request.referrer or url_for('index'))

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def generate_customer_id():
    """Generate a unique 8-character customer ID like KB20240001"""
    year = datetime.now().year
    random_part = ''.join(random.choices(string.digits, k=4))
    return f"KB{year}{random_part}"

def generate_account_number():
    """Generate a 12-digit account number"""
    return ''.join(random.choices(string.digits, k=12))

def generate_transaction_id():
    """Generate a unique transaction ID"""
    return "TXN" + uuid.uuid4().hex[:10].upper()

def generate_application_id(prefix="APP"):
    """Generate a unique application ID"""
    return prefix + uuid.uuid4().hex[:8].upper()

def add_notification(user_id, message):
    """Save a notification for a user in the database"""
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO notifications (user_id, message) VALUES (?, ?)',
        (user_id, message)
    )
    conn.commit()
    conn.close()

def format_currency(amount):
    """Format amount as Indian Rupees"""
    return f"₹{amount:,.2f}"

# ==========================================
# LOGIN REQUIRED DECORATORS
# ==========================================

def login_required(f):
    """Decorator: redirect to login if user is not logged in"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access your account.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Decorator: redirect if user is not an admin"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ==========================================
# PUBLIC ROUTES
# ==========================================

@app.route('/')
def index():
    """Homepage - shown to all visitors"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    User Registration
    GET:  Show the registration form
    POST: Process the form data and create account
    """
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name', '').strip()
        email     = request.form.get('email', '').strip().lower()
        phone     = request.form.get('phone', '').strip()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')

        # Basic validation
        if not all([full_name, email, phone, password, confirm]):
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        conn = get_db_connection()
        try:
            # Check if email already exists
            existing = conn.execute(
                'SELECT id FROM users WHERE email = ?', (email,)
            ).fetchone()

            if existing:
                flash('Email already registered. Please log in.', 'warning')
                return render_template('register.html')

            # Generate unique customer ID (keep trying until unique)
            customer_id = generate_customer_id()
            while conn.execute('SELECT id FROM users WHERE customer_id = ?',
                               (customer_id,)).fetchone():
                customer_id = generate_customer_id()

            # Hash the password before saving
            hashed_pw = generate_password_hash(password)

            # Insert new user
            conn.execute('''
                INSERT INTO users (customer_id, full_name, email, phone, password)
                VALUES (?, ?, ?, ?, ?)
            ''', (customer_id, full_name, email, phone, hashed_pw))
            conn.commit()

            flash(f'Account created! Your Customer ID: {customer_id}. Please log in.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            flash('An error occurred. Please try again.', 'danger')
            print(f"Registration error: {e}")
        finally:
            conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    User Login
    GET:  Show the login form
    POST: Validate credentials and start session
    """
    if 'user_id' in session:
        if session.get('is_admin'):
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('login.html')

        conn = get_db_connection()
        try:
            user = conn.execute(
                'SELECT * FROM users WHERE email = ?', (email,)
            ).fetchone()

            if user and check_password_hash(user['password'], password):
                # Save user info in session
                session['user_id']     = user['id']
                session['user_name']   = user['full_name']
                session['customer_id'] = user['customer_id']
                session['is_admin']    = bool(user['is_admin'])

                if user['is_admin']:
                    flash(f"Welcome back, Admin!", 'success')
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash(f"Welcome back, {user['full_name'].split()[0]}!", 'success')
                    return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password.', 'danger')
        finally:
            conn.close()

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Clear session and redirect to homepage"""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))


# ==========================================
# CUSTOMER DASHBOARD
# ==========================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Main customer dashboard"""
    user_id = session['user_id']
    conn = get_db_connection()
    try:
        # Get user info
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

        # Get user's account
        account = conn.execute(
            'SELECT * FROM accounts WHERE user_id = ?', (user_id,)
        ).fetchone()

        # Get recent 5 transactions
        recent_transactions = []
        if account:
            recent_transactions = conn.execute('''
                SELECT * FROM transactions
                WHERE account_id = ?
                ORDER BY created_at DESC
                LIMIT 5
            ''', (account['id'],)).fetchall()

        # Get unread notifications
        notifications = conn.execute('''
            SELECT * FROM notifications
            WHERE user_id = ? AND is_read = 0
            ORDER BY created_at DESC
            LIMIT 10
        ''', (user_id,)).fetchall()

        # Get monthly analytics data for chart
        monthly_data = {}
        if account:
            rows = conn.execute('''
                SELECT
                    strftime('%Y-%m', created_at) as month,
                    transaction_type,
                    SUM(amount) as total
                FROM transactions
                WHERE account_id = ?
                GROUP BY month, transaction_type
                ORDER BY month DESC
                LIMIT 12
            ''', (account['id'],)).fetchall()
            for row in rows:
                month = row['month']
                if month not in monthly_data:
                    monthly_data[month] = {'deposit': 0, 'withdrawal': 0, 'transfer_in': 0, 'transfer_out': 0}
                ttype = row['transaction_type'].lower()
                if ttype in monthly_data[month]:
                    monthly_data[month][ttype] = row['total']

        now = datetime.now()
        return render_template('dashboard.html',
            user=user,
            account=account,
            recent_transactions=recent_transactions,
            notifications=notifications,
            monthly_data=monthly_data,
            notification_count=len(notifications),
            now_hour=now.hour,
            now_date=now.strftime('%A, %d %B %Y')
        )
    finally:
        conn.close()


# ==========================================
# ACCOUNT OPENING
# ==========================================

@app.route('/open-account', methods=['GET', 'POST'])
@login_required
def open_account():
    """Allow logged-in users to open a bank account"""
    user_id = session['user_id']

    conn = get_db_connection()
    try:
        # Check if account already exists
        existing = conn.execute(
            'SELECT id FROM accounts WHERE user_id = ?', (user_id,)
        ).fetchone()

        if existing:
            flash('You already have a bank account.', 'info')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            account_type  = request.form.get('account_type', '').strip()
            address       = request.form.get('address', '').strip()
            date_of_birth = request.form.get('date_of_birth', '').strip()

            if not all([account_type, address, date_of_birth]):
                flash('All fields are required.', 'danger')
                return render_template('open_account.html')

            if account_type not in ['Savings', 'Current']:
                flash('Invalid account type.', 'danger')
                return render_template('open_account.html')

            # Generate unique account number
            account_number = generate_account_number()
            while conn.execute('SELECT id FROM accounts WHERE account_number = ?',
                               (account_number,)).fetchone():
                account_number = generate_account_number()

            # Create the account
            conn.execute('''
                INSERT INTO accounts (user_id, account_number, account_type, balance, address, date_of_birth)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, account_number, account_type, 0.0, address, date_of_birth))
            conn.commit()

            # Send welcome notification
            add_notification(user_id,
                f"🎉 Welcome! Your {account_type} Account #{account_number} has been opened successfully.")

            flash(f'Your {account_type} Account has been opened! Account Number: {account_number}', 'success')
            return redirect(url_for('dashboard'))

    except Exception as e:
        flash('Error opening account. Please try again.', 'danger')
        print(f"Account opening error: {e}")
    finally:
        conn.close()

    return render_template('open_account.html')


# ==========================================
# DEPOSIT MONEY
# ==========================================

@app.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    """Deposit money into the user's account"""
    user_id = session['user_id']

    conn = get_db_connection()
    try:
        account = conn.execute(
            'SELECT * FROM accounts WHERE user_id = ?', (user_id,)
        ).fetchone()

        if not account:
            flash('Please open an account first.', 'warning')
            return redirect(url_for('open_account'))

        if request.method == 'POST':
            try:
                amount = float(request.form.get('amount', 0))
            except ValueError:
                flash('Invalid amount.', 'danger')
                return render_template('deposit.html', account=account)

            if amount <= 0:
                flash('Deposit amount must be greater than zero.', 'danger')
                return render_template('deposit.html', account=account)

            if amount > 10000000:  # 1 Crore limit
                flash('Maximum single deposit is ₹1,00,00,000.', 'danger')
                return render_template('deposit.html', account=account)

            description = request.form.get('description', 'Cash Deposit').strip()

            # Update balance and save transaction (using a transaction for safety)
            new_balance    = account['balance'] + amount
            transaction_id = generate_transaction_id()

            conn.execute(
                'UPDATE accounts SET balance = ? WHERE id = ?',
                (new_balance, account['id'])
            )
            conn.execute('''
                INSERT INTO transactions
                (transaction_id, account_id, transaction_type, amount, balance_after, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (transaction_id, account['id'], 'deposit', amount, new_balance, description))
            conn.commit()

            # Notification
            add_notification(user_id,
                f"✅ ₹{amount:,.2f} deposited. Transaction ID: {transaction_id}")

            flash(f'₹{amount:,.2f} deposited successfully! Transaction ID: {transaction_id}', 'success')
            return redirect(url_for('dashboard'))

    finally:
        conn.close()

    return render_template('deposit.html', account=account)


# ==========================================
# WITHDRAW MONEY
# ==========================================

@app.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    """Withdraw money from the user's account"""
    user_id = session['user_id']

    conn = get_db_connection()
    try:
        account = conn.execute(
            'SELECT * FROM accounts WHERE user_id = ?', (user_id,)
        ).fetchone()

        if not account:
            flash('Please open an account first.', 'warning')
            return redirect(url_for('open_account'))

        if request.method == 'POST':
            try:
                amount = float(request.form.get('amount', 0))
            except ValueError:
                flash('Invalid amount.', 'danger')
                return render_template('withdraw.html', account=account)

            if amount <= 0:
                flash('Withdrawal amount must be greater than zero.', 'danger')
                return render_template('withdraw.html', account=account)

            if amount > account['balance']:
                flash(f'Insufficient balance. Available: ₹{account["balance"]:,.2f}', 'danger')
                return render_template('withdraw.html', account=account)

            if amount > 200000:  # Daily ATM limit simulation
                flash('Maximum single withdrawal is ₹2,00,000.', 'danger')
                return render_template('withdraw.html', account=account)

            description = request.form.get('description', 'Cash Withdrawal').strip()

            # Update balance
            new_balance    = account['balance'] - amount
            transaction_id = generate_transaction_id()

            conn.execute(
                'UPDATE accounts SET balance = ? WHERE id = ?',
                (new_balance, account['id'])
            )
            conn.execute('''
                INSERT INTO transactions
                (transaction_id, account_id, transaction_type, amount, balance_after, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (transaction_id, account['id'], 'withdrawal', amount, new_balance, description))
            conn.commit()

            add_notification(user_id,
                f"💸 ₹{amount:,.2f} withdrawn. Transaction ID: {transaction_id}")

            flash(f'₹{amount:,.2f} withdrawn successfully! Transaction ID: {transaction_id}', 'success')
            return redirect(url_for('dashboard'))

    finally:
        conn.close()

    return render_template('withdraw.html', account=account)


# ==========================================
# MONEY TRANSFER
# ==========================================

@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    """Transfer money to another account"""
    user_id = session['user_id']

    conn = get_db_connection()
    try:
        # Get sender's account
        sender_account = conn.execute(
            'SELECT * FROM accounts WHERE user_id = ?', (user_id,)
        ).fetchone()

        if not sender_account:
            flash('Please open an account first.', 'warning')
            return redirect(url_for('open_account'))

        if request.method == 'POST':
            receiver_account_number = request.form.get('receiver_account', '').strip()
            try:
                amount = float(request.form.get('amount', 0))
            except ValueError:
                flash('Invalid amount.', 'danger')
                return render_template('transfer.html', account=sender_account)

            description = request.form.get('description', 'Fund Transfer').strip()

            # Validations
            if not receiver_account_number:
                flash('Please enter recipient account number.', 'danger')
                return render_template('transfer.html', account=sender_account)

            if receiver_account_number == sender_account['account_number']:
                flash('Cannot transfer to your own account.', 'danger')
                return render_template('transfer.html', account=sender_account)

            if amount <= 0:
                flash('Transfer amount must be greater than zero.', 'danger')
                return render_template('transfer.html', account=sender_account)

            if amount > sender_account['balance']:
                flash(f'Insufficient balance. Available: ₹{sender_account["balance"]:,.2f}', 'danger')
                return render_template('transfer.html', account=sender_account)

            # Find receiver's account
            receiver_account = conn.execute(
                'SELECT * FROM accounts WHERE account_number = ?',
                (receiver_account_number,)
            ).fetchone()

            if not receiver_account:
                flash('Recipient account not found.', 'danger')
                return render_template('transfer.html', account=sender_account)

            # Get receiver's user info
            receiver_user = conn.execute(
                'SELECT full_name FROM users WHERE id = ?', (receiver_account['user_id'],)
            ).fetchone()

            # Perform the transfer atomically
            new_sender_balance   = sender_account['balance'] - amount
            new_receiver_balance = receiver_account['balance'] + amount
            txn_id               = generate_transaction_id()

            # Deduct from sender
            conn.execute(
                'UPDATE accounts SET balance = ? WHERE id = ?',
                (new_sender_balance, sender_account['id'])
            )
            conn.execute('''
                INSERT INTO transactions
                (transaction_id, account_id, transaction_type, amount, balance_after, description, reference_account)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (txn_id, sender_account['id'], 'transfer_out', amount,
                  new_sender_balance, description, receiver_account_number))

            # Add to receiver
            conn.execute(
                'UPDATE accounts SET balance = ? WHERE id = ?',
                (new_receiver_balance, receiver_account['id'])
            )
            conn.execute('''
                INSERT INTO transactions
                (transaction_id, account_id, transaction_type, amount, balance_after, description, reference_account)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ("R" + txn_id[1:], receiver_account['id'], 'transfer_in', amount,
                  new_receiver_balance, description, sender_account['account_number']))

            conn.commit()

            # Notifications for both users
            receiver_name = receiver_user['full_name'] if receiver_user else 'recipient'
            add_notification(user_id,
                f"💸 ₹{amount:,.2f} transferred to {receiver_name} ({receiver_account_number}). Txn: {txn_id}")
            add_notification(receiver_account['user_id'],
                f"💰 ₹{amount:,.2f} received from account #{sender_account['account_number']}. Txn: {txn_id}")

            flash(f'₹{amount:,.2f} transferred to {receiver_name} successfully! Transaction ID: {txn_id}', 'success')
            return redirect(url_for('dashboard'))

    finally:
        conn.close()

    return render_template('transfer.html', account=sender_account)


# ==========================================
# TRANSACTION HISTORY
# ==========================================

@app.route('/transactions')
@login_required
def transactions():
    """Show all transactions for the user's account"""
    user_id = session['user_id']

    # Filter options
    filter_type = request.args.get('type', 'all')
    filter_date = request.args.get('date', '')

    conn = get_db_connection()
    try:
        account = conn.execute(
            'SELECT * FROM accounts WHERE user_id = ?', (user_id,)
        ).fetchone()

        if not account:
            flash('Please open an account first.', 'warning')
            return redirect(url_for('open_account'))

        # Build query with optional filters
        query  = 'SELECT * FROM transactions WHERE account_id = ?'
        params = [account['id']]

        if filter_type != 'all':
            query += ' AND transaction_type = ?'
            params.append(filter_type)

        if filter_date:
            query += " AND date(created_at) = date(?)"
            params.append(filter_date)

        query += ' ORDER BY created_at DESC'

        txns = conn.execute(query, params).fetchall()

        return render_template('transactions.html',
            account=account,
            transactions=txns,
            filter_type=filter_type,
            filter_date=filter_date
        )
    finally:
        conn.close()


# ==========================================
# LOAN APPLICATION
# ==========================================

@app.route('/loans', methods=['GET', 'POST'])
@login_required
def loans():
    """Loan application page"""
    user_id = session['user_id']

    conn = get_db_connection()
    try:
        # Get existing loan applications
        my_loans = conn.execute(
            'SELECT * FROM loan_applications WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        ).fetchall()

        if request.method == 'POST':
            loan_type         = request.form.get('loan_type', '').strip()
            amount            = request.form.get('amount', '')
            monthly_income    = request.form.get('monthly_income', '')
            employment_status = request.form.get('employment_status', '').strip()
            duration          = request.form.get('duration_months', '')
            reason            = request.form.get('reason', '').strip()

            # Validate
            try:
                amount         = float(amount)
                monthly_income = float(monthly_income)
                duration       = int(duration)
            except ValueError:
                flash('Please enter valid numeric values.', 'danger')
                return render_template('loans.html', my_loans=my_loans)

            valid_types = ['Personal Loan', 'Education Loan', 'Home Loan']
            if loan_type not in valid_types:
                flash('Invalid loan type.', 'danger')
                return render_template('loans.html', my_loans=my_loans)

            if amount <= 0 or monthly_income <= 0 or duration <= 0:
                flash('All values must be positive.', 'danger')
                return render_template('loans.html', my_loans=my_loans)

            app_id = generate_application_id('LN')

            conn.execute('''
                INSERT INTO loan_applications
                (application_id, user_id, loan_type, amount, monthly_income,
                 employment_status, duration_months, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (app_id, user_id, loan_type, amount, monthly_income,
                  employment_status, duration, reason))
            conn.commit()

            add_notification(user_id,
                f"📄 Your {loan_type} application ({app_id}) for ₹{amount:,.2f} has been submitted.")

            flash(f'{loan_type} application submitted! Application ID: {app_id}', 'success')
            return redirect(url_for('loans'))

    finally:
        conn.close()

    return render_template('loans.html', my_loans=my_loans)


# ==========================================
# CREDIT CARD APPLICATION
# ==========================================

@app.route('/credit-cards', methods=['GET', 'POST'])
@login_required
def credit_cards():
    """Credit card application page"""
    user_id = session['user_id']

    conn = get_db_connection()
    try:
        my_cards = conn.execute(
            'SELECT * FROM credit_card_applications WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        ).fetchall()

        if request.method == 'POST':
            card_type       = request.form.get('card_type', '').strip()
            annual_income   = request.form.get('annual_income', '')
            employment_type = request.form.get('employment_type', '').strip()

            try:
                annual_income = float(annual_income)
            except ValueError:
                flash('Please enter a valid income.', 'danger')
                return render_template('credit_cards.html', my_cards=my_cards)

            valid_cards = ['Classic Card', 'Gold Card', 'Premium Card']
            if card_type not in valid_cards:
                flash('Invalid card type.', 'danger')
                return render_template('credit_cards.html', my_cards=my_cards)

            if annual_income <= 0:
                flash('Annual income must be positive.', 'danger')
                return render_template('credit_cards.html', my_cards=my_cards)

            app_id = generate_application_id('CC')

            conn.execute('''
                INSERT INTO credit_card_applications
                (application_id, user_id, card_type, annual_income, employment_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (app_id, user_id, card_type, annual_income, employment_type))
            conn.commit()

            add_notification(user_id,
                f"💳 Your {card_type} application ({app_id}) has been submitted.")

            flash(f'{card_type} application submitted! Application ID: {app_id}', 'success')
            return redirect(url_for('credit_cards'))

    finally:
        conn.close()

    return render_template('credit_cards.html', my_cards=my_cards)


# ==========================================
# PROFILE PAGE
# ==========================================

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page"""
    user_id = session['user_id']

    conn = get_db_connection()
    try:
        user    = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        account = conn.execute('SELECT * FROM accounts WHERE user_id = ?', (user_id,)).fetchone()

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'update_profile':
                phone = request.form.get('phone', '').strip()
                if phone:
                    conn.execute('UPDATE users SET phone = ? WHERE id = ?', (phone, user_id))
                    conn.commit()
                    flash('Profile updated.', 'success')

            elif action == 'change_password':
                current_pw = request.form.get('current_password', '')
                new_pw     = request.form.get('new_password', '')
                confirm_pw = request.form.get('confirm_password', '')

                if not check_password_hash(user['password'], current_pw):
                    flash('Current password is incorrect.', 'danger')
                elif len(new_pw) < 6:
                    flash('New password must be at least 6 characters.', 'danger')
                elif new_pw != confirm_pw:
                    flash('Passwords do not match.', 'danger')
                else:
                    conn.execute(
                        'UPDATE users SET password = ? WHERE id = ?',
                        (generate_password_hash(new_pw), user_id)
                    )
                    conn.commit()
                    flash('Password changed successfully.', 'success')

            return redirect(url_for('profile'))

    finally:
        conn.close()

    return render_template('profile.html', user=user, account=account)


# ==========================================
# NOTIFICATIONS
# ==========================================

@app.route('/notifications')
@login_required
def notifications():
    """View all notifications"""
    user_id = session['user_id']

    conn = get_db_connection()
    try:
        # Mark all as read
        conn.execute(
            'UPDATE notifications SET is_read = 1 WHERE user_id = ?', (user_id,)
        )
        conn.commit()

        all_notifs = conn.execute(
            'SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        ).fetchall()

        return render_template('notifications.html', notifications=all_notifs)
    finally:
        conn.close()


# ==========================================
# DOWNLOAD PDF STATEMENT
# ==========================================

@app.route('/download-statement')
@login_required
def download_statement():
    """Generate and download PDF bank statement"""
    user_id = session['user_id']

    conn = get_db_connection()
    try:
        user    = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        account = conn.execute('SELECT * FROM accounts WHERE user_id = ?', (user_id,)).fetchone()

        if not account:
            flash('No account found.', 'warning')
            return redirect(url_for('dashboard'))

        txns = conn.execute('''
            SELECT * FROM transactions WHERE account_id = ?
            ORDER BY created_at DESC LIMIT 50
        ''', (account['id'],)).fetchall()

    finally:
        conn.close()

    # Generate PDF using ReportLab
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        import io

        buffer = io.BytesIO()
        doc    = SimpleDocTemplate(buffer, pagesize=A4,
                                   rightMargin=0.5*inch, leftMargin=0.5*inch,
                                   topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles  = getSampleStyleSheet()
        content = []

        # Title
        title_style = ParagraphStyle('title', parent=styles['Title'],
                                     textColor=colors.HexColor('#B71C1C'),
                                     fontSize=22, spaceAfter=4)
        content.append(Paragraph("KUBERA BANK", title_style))
        content.append(Paragraph("Your Wealth, Our Responsibility.", styles['Normal']))
        content.append(Spacer(1, 12))
        content.append(Paragraph(f"Bank Statement", styles['Heading2']))
        content.append(Spacer(1, 6))

        # Account info
        info_data = [
            ['Account Holder:', user['full_name']],
            ['Customer ID:', user['customer_id']],
            ['Account Number:', account['account_number']],
            ['Account Type:', account['account_type']],
            ['Current Balance:', f"₹{account['balance']:,.2f}"],
            ['Statement Date:', datetime.now().strftime('%d %B %Y')],
        ]
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME',  (0,0), (-1,-1), 'Helvetica'),
            ('FONTNAME',  (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTSIZE',  (0,0), (-1,-1), 10),
            ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.HexColor('#FAF9F6')]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        content.append(info_table)
        content.append(Spacer(1, 20))

        # Transactions table
        content.append(Paragraph("Transaction History (Last 50)", styles['Heading3']))
        content.append(Spacer(1, 6))

        txn_header = [['Date', 'Transaction ID', 'Type', 'Amount (₹)', 'Balance (₹)']]
        txn_rows   = []
        for t in txns:
            txn_rows.append([
                t['created_at'][:16],
                t['transaction_id'],
                t['transaction_type'].replace('_', ' ').title(),
                f"{t['amount']:,.2f}",
                f"{t['balance_after']:,.2f}",
            ])

        txn_data = txn_header + txn_rows
        txn_table = Table(txn_data, colWidths=[1.3*inch, 1.5*inch, 1.1*inch, 1.1*inch, 1.1*inch])
        txn_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#B71C1C')),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,-1), 8),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#FFF8F8')]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('PADDING', (0,0), (-1,-1), 5),
            ('ALIGN', (3,0), (-1,-1), 'RIGHT'),
        ]))
        content.append(txn_table)
        content.append(Spacer(1, 20))
        content.append(Paragraph("This is a computer-generated statement. No signature required.",
                                  styles['Italic']))

        doc.build(content)
        buffer.seek(0)

        filename = f"KuberaBank_Statement_{user['customer_id']}_{datetime.now().strftime('%Y%m%d')}.pdf"
        return send_file(buffer, as_attachment=True, download_name=filename,
                        mimetype='application/pdf')

    except ImportError:
        flash('PDF generation requires ReportLab. Run: pip install reportlab', 'warning')
        return redirect(url_for('transactions'))


# ==========================================
# CHATBOT API
# ==========================================

@app.route('/api/chatbot', methods=['POST'])
@login_required
def chatbot():
    """
    Simple rule-based banking chatbot.
    Answers predefined banking questions.
    No paid AI API needed!
    """
    data    = request.get_json()
    message = data.get('message', '').lower().strip()

    # Banking FAQ responses
    responses = {
        'open account': {
            'keywords': ['open account', 'create account', 'new account', 'register account'],
            'reply': '🏦 To open a bank account, go to <strong>Dashboard → Open Account</strong>. Fill in your personal details, choose Savings or Current account, and your account will be created instantly!'
        },
        'deposit': {
            'keywords': ['deposit', 'add money', 'put money', 'credit'],
            'reply': '💰 To deposit money: Go to <strong>Dashboard → Deposit Money</strong>. Enter the amount and click Deposit. The amount will be credited to your account immediately.'
        },
        'withdraw': {
            'keywords': ['withdraw', 'take money', 'debit', 'cash out'],
            'reply': '💸 To withdraw money: Go to <strong>Dashboard → Withdraw Money</strong>. Enter the amount (must not exceed your balance). Maximum single withdrawal is ₹2,00,000.'
        },
        'transfer': {
            'keywords': ['transfer', 'send money', 'neft', 'imps'],
            'reply': '🔄 To transfer money: Go to <strong>Dashboard → Transfer Money</strong>. Enter the recipient\'s account number and amount. The transfer happens instantly!'
        },
        'balance': {
            'keywords': ['balance', 'how much', 'account balance', 'check balance'],
            'reply': '💳 Your account balance is shown on your <strong>Dashboard</strong>. You can also check it in the Account Details section.'
        },
        'loan': {
            'keywords': ['loan', 'borrow', 'personal loan', 'home loan', 'education loan'],
            'reply': '📋 We offer Personal, Education, and Home Loans. Go to <strong>Dashboard → Apply for Loan</strong>. Fill in the form and your application will be reviewed within 2-3 business days.'
        },
        'credit card': {
            'keywords': ['credit card', 'card', 'classic', 'gold', 'premium'],
            'reply': '💳 We offer Classic, Gold, and Premium credit cards. Go to <strong>Dashboard → Apply for Credit Card</strong> to submit your application.'
        },
        'statement': {
            'keywords': ['statement', 'download', 'pdf', 'transaction history'],
            'reply': '📄 To download your bank statement: Go to <strong>Transactions → Download Statement</strong>. You will get a PDF with your complete transaction history.'
        },
        'services': {
            'keywords': ['services', 'features', 'what can', 'offer', 'help'],
            'reply': '🏦 Kubera Bank offers: Account Opening, Deposits & Withdrawals, Money Transfers, Loan Applications (Personal/Education/Home), Credit Card Applications, Transaction History, PDF Statements, and Financial Analytics!'
        },
        'hours': {
            'keywords': ['timing', 'hours', 'open', 'working hours', 'available'],
            'reply': '🕐 Our digital banking platform is available <strong>24/7</strong>! You can perform all banking operations anytime, anywhere.'
        },
        'security': {
            'keywords': ['security', 'safe', 'secure', 'password', 'protect'],
            'reply': '🔒 Your account is protected with password hashing, secure sessions, and form validation. Never share your password with anyone. Kubera Bank will never ask for your password via email or phone.'
        },
    }

    # Find the best matching response
    reply = None
    for key, data in responses.items():
        for keyword in data['keywords']:
            if keyword in message:
                reply = data['reply']
                break
        if reply:
            break

    if not reply:
        reply = "🤔 I'm not sure about that. Here's what I can help you with:<br>• Open Account<br>• Deposit / Withdraw<br>• Transfer Money<br>• Check Balance<br>• Apply for Loan<br>• Apply for Credit Card<br>• Download Statement<br><br>Type any of these topics!"

    return jsonify({'reply': reply})


# ==========================================
# ANALYTICS API
# ==========================================

@app.route('/api/analytics')
@login_required
def analytics():
    """Return spending analytics data for Chart.js"""
    user_id = session['user_id']

    conn = get_db_connection()
    try:
        account = conn.execute(
            'SELECT * FROM accounts WHERE user_id = ?', (user_id,)
        ).fetchone()

        if not account:
            return jsonify({'error': 'No account found'})

        # Monthly totals by type
        rows = conn.execute('''
            SELECT
                strftime('%b %Y', created_at) as month,
                strftime('%Y-%m', created_at) as sort_month,
                transaction_type,
                SUM(amount) as total
            FROM transactions
            WHERE account_id = ?
            GROUP BY sort_month, transaction_type
            ORDER BY sort_month ASC
            LIMIT 24
        ''', (account['id'],)).fetchall()

        months   = []
        deposits = []
        withdrawals = []

        month_map = {}
        for row in rows:
            m = row['month']
            if m not in month_map:
                month_map[m] = {'deposit': 0, 'withdrawal': 0, 'transfer_in': 0, 'transfer_out': 0}
            ttype = row['transaction_type']
            if ttype in month_map[m]:
                month_map[m][ttype] = row['total']

        for month, vals in month_map.items():
            months.append(month)
            deposits.append(vals['deposit'] + vals['transfer_in'])
            withdrawals.append(vals['withdrawal'] + vals['transfer_out'])

        # Transaction type distribution
        dist = conn.execute('''
            SELECT transaction_type, COUNT(*) as count, SUM(amount) as total
            FROM transactions
            WHERE account_id = ?
            GROUP BY transaction_type
        ''', (account['id'],)).fetchall()

        distribution = {row['transaction_type']: {'count': row['count'], 'total': row['total']}
                       for row in dist}

        return jsonify({
            'months': months,
            'deposits': deposits,
            'withdrawals': withdrawals,
            'distribution': distribution
        })
    finally:
        conn.close()


# ==========================================
# ADMIN DASHBOARD
# ==========================================

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard - overview of all bank activity"""
    conn = get_db_connection()
    try:
        # Statistics
        total_customers    = conn.execute("SELECT COUNT(*) FROM users WHERE is_admin=0").fetchone()[0]
        total_accounts     = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        total_transactions = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        total_deposits     = conn.execute(
            "SELECT SUM(amount) FROM transactions WHERE transaction_type='deposit'"
        ).fetchone()[0] or 0
        pending_loans      = conn.execute(
            "SELECT COUNT(*) FROM loan_applications WHERE status='Pending'"
        ).fetchone()[0]
        pending_cards      = conn.execute(
            "SELECT COUNT(*) FROM credit_card_applications WHERE status='Pending'"
        ).fetchone()[0]

        # Recent customers
        recent_customers = conn.execute('''
            SELECT u.*, a.account_number, a.account_type, a.balance
            FROM users u
            LEFT JOIN accounts a ON u.id = a.user_id
            WHERE u.is_admin = 0
            ORDER BY u.created_at DESC
            LIMIT 10
        ''').fetchall()

        # Pending loan applications
        pending_loan_apps = conn.execute('''
            SELECT l.*, u.full_name, u.email
            FROM loan_applications l
            JOIN users u ON l.user_id = u.id
            WHERE l.status = 'Pending'
            ORDER BY l.created_at DESC
        ''').fetchall()

        # Pending credit card applications
        pending_card_apps = conn.execute('''
            SELECT c.*, u.full_name, u.email
            FROM credit_card_applications c
            JOIN users u ON c.user_id = u.id
            WHERE c.status = 'Pending'
            ORDER BY c.created_at DESC
        ''').fetchall()

        return render_template('admin_dashboard.html',
            total_customers=total_customers,
            total_accounts=total_accounts,
            total_transactions=total_transactions,
            total_deposits=total_deposits,
            pending_loans=pending_loans,
            pending_cards=pending_cards,
            recent_customers=recent_customers,
            pending_loan_apps=pending_loan_apps,
            pending_card_apps=pending_card_apps,
        )
    finally:
        conn.close()


@app.route('/admin/loan/<int:app_id>/<action>', methods=['POST'])
@admin_required
def admin_loan_action(app_id, action):
    """Admin: Approve or reject a loan application"""
    if action not in ['approve', 'reject']:
        flash('Invalid action.', 'danger')
        return redirect(url_for('admin_dashboard'))

    conn = get_db_connection()
    try:
        loan = conn.execute(
            'SELECT * FROM loan_applications WHERE id = ?', (app_id,)
        ).fetchone()

        if not loan:
            flash('Application not found.', 'danger')
            return redirect(url_for('admin_dashboard'))

        status    = 'Approved' if action == 'approve' else 'Rejected'
        note      = request.form.get('note', '')

        conn.execute('''
            UPDATE loan_applications
            SET status = ?, admin_note = ?, updated_at = datetime('now', 'localtime')
            WHERE id = ?
        ''', (status, note, app_id))
        conn.commit()

        # Notify customer
        emoji = '✅' if status == 'Approved' else '❌'
        add_notification(loan['user_id'],
            f"{emoji} Your loan application ({loan['application_id']}) has been {status}. {note}")

        flash(f'Loan application {status}.', 'success')
    finally:
        conn.close()

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/card/<int:app_id>/<action>', methods=['POST'])
@admin_required
def admin_card_action(app_id, action):
    """Admin: Approve or reject a credit card application"""
    if action not in ['approve', 'reject']:
        flash('Invalid action.', 'danger')
        return redirect(url_for('admin_dashboard'))

    conn = get_db_connection()
    try:
        card = conn.execute(
            'SELECT * FROM credit_card_applications WHERE id = ?', (app_id,)
        ).fetchone()

        if not card:
            flash('Application not found.', 'danger')
            return redirect(url_for('admin_dashboard'))

        status = 'Approved' if action == 'approve' else 'Rejected'
        note   = request.form.get('note', '')

        conn.execute('''
            UPDATE credit_card_applications
            SET status = ?, admin_note = ?, updated_at = datetime('now', 'localtime')
            WHERE id = ?
        ''', (status, note, app_id))
        conn.commit()

        emoji = '✅' if status == 'Approved' else '❌'
        add_notification(card['user_id'],
            f"{emoji} Your {card['card_type']} application ({card['application_id']}) has been {status}. {note}")

        flash(f'Credit card application {status}.', 'success')
    finally:
        conn.close()

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/customers')
@admin_required
def admin_customers():
    """Admin: View all customers"""
    conn = get_db_connection()
    try:
        customers = conn.execute('''
            SELECT u.*, a.account_number, a.account_type, a.balance, a.is_active
            FROM users u
            LEFT JOIN accounts a ON u.id = a.user_id
            WHERE u.is_admin = 0
            ORDER BY u.created_at DESC
        ''').fetchall()

        return render_template('admin_customers.html', customers=customers)
    finally:
        conn.close()


@app.route('/admin/transactions')
@admin_required
def admin_transactions():
    """Admin: View all transactions"""
    conn = get_db_connection()
    try:
        txns = conn.execute('''
            SELECT t.*, a.account_number, u.full_name
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            JOIN users u ON a.user_id = u.id
            ORDER BY t.created_at DESC
            LIMIT 100
        ''').fetchall()

        return render_template('admin_transactions.html', transactions=txns)
    finally:
        conn.close()


# ==========================================
# APP STARTUP
# ==========================================

if __name__ == '__main__':
    # Initialize the database when the app starts
    initialize_database()
    create_admin_user()
    print("\n" + "="*50)
    print("  KUBERA BANK - Smart Digital Banking System")
    print("  Your Wealth, Our Responsibility.")
    print("="*50)
    print(f"\n  Running at: http://127.0.0.1:5000")
    print(f"  Admin Login: admin@kuberabank.com / kubera@admin2024")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)
