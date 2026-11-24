"""
KUBERA BANK - Comprehensive Automated Test Suite
-------------------------------------------------
This script tests all banking operations, security rules,
database integrity, and admin workflows end-to-end.

Run with:
    python test_banking.py
"""

import os
import sys
import unittest
from datetime import datetime

# Set test environment
os.environ['SECRET_KEY'] = 'test-secret-key-12345'

from config import Config
# Use a test database
Config.DATABASE_PATH = os.path.join(Config.BASE_DIR, 'database', 'test_kubera_bank.db')

from app import app
from database import get_db_connection, initialize_database, create_admin_user

class KuberaBankTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Clean up existing test database if any
        if os.path.exists(Config.DATABASE_PATH):
            os.remove(Config.DATABASE_PATH)
        initialize_database()
        create_admin_user()

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_01_homepage_renders(self):
        """Test homepage renders with bank brand name and status 200"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'KUBERA BANK', response.data)
        self.assertIn(b'Your Wealth, Our Responsibility', response.data)
        print("  [PASS] Homepage renders with brand and tagline")

    def test_02_admin_user_exists(self):
        """Verify default admin user exists in database"""
        conn = get_db_connection()
        admin = conn.execute("SELECT * FROM users WHERE email='admin@kuberabank.com'").fetchone()
        conn.close()
        self.assertIsNotNone(admin)
        self.assertEqual(admin['is_admin'], 1)
        self.assertEqual(admin['customer_id'], 'ADMIN001')
        print("  [PASS] Admin user initialized properly")

    def test_03_user_registration(self):
        """Test user registration workflow with CSRF"""
        with self.app as c:
            c.get('/register')
            csrf = c.session.get('_csrf_token')
            response = c.post('/register', data={
                'csrf_token': csrf,
                'full_name': 'Rahul Sharma',
                'email': 'rahul@example.com',
                'phone': '9876543210',
                'password': 'Password@123',
                'confirm_password': 'Password@123'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Account created', response.data)

        # Verify in DB
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email='rahul@example.com'").fetchone()
        conn.close()
        self.assertIsNotNone(user)
        self.assertTrue(user['customer_id'].startswith('KB'))
        print(f"  [PASS] User registered: {user['full_name']} (ID: {user['customer_id']})")

    def test_04_user_login(self):
        """Test login with credentials"""
        with self.app as c:
            c.get('/login')
            csrf = c.session.get('_csrf_token')
            response = c.post('/login', data={
                'csrf_token': csrf,
                'email': 'rahul@example.com',
                'password': 'Password@123'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Good', response.data)  # Dashboard greeting
            self.assertIn(b'Rahul', response.data)
        print("  [PASS] User login and session management")

    def test_05_open_bank_account(self):
        """Test opening a Savings account"""
        with self.app as c:
            # Login first
            c.get('/login')
            csrf = c.session.get('_csrf_token')
            c.post('/login', data={
                'csrf_token': csrf,
                'email': 'rahul@example.com',
                'password': 'Password@123'
            })

            # Open account
            csrf = c.session.get('_csrf_token')
            response = c.post('/open-account', data={
                'csrf_token': csrf,
                'account_type': 'Savings',
                'date_of_birth': '2000-01-15',
                'address': '101 Marine Drive, Mumbai'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)

        conn = get_db_connection()
        acc = conn.execute("""
            SELECT a.* FROM accounts a 
            JOIN users u ON a.user_id = u.id 
            WHERE u.email = 'rahul@example.com'
        """).fetchone()
        conn.close()
        self.assertIsNotNone(acc)
        self.assertEqual(len(acc['account_number']), 12)
        self.assertEqual(acc['balance'], 0.0)
        print(f"  [PASS] Bank account created: #{acc['account_number']} (Type: {acc['account_type']})")

    def test_06_deposit_money(self):
        """Test deposit operation and balance update"""
        with self.app as c:
            c.get('/login')
            csrf = c.session.get('_csrf_token')
            c.post('/login', data={
                'csrf_token': csrf,
                'email': 'rahul@example.com',
                'password': 'Password@123'
            })

            csrf = c.session.get('_csrf_token')
            response = c.post('/deposit', data={
                'csrf_token': csrf,
                'amount': '15000',
                'description': 'Initial Salary Deposit'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'deposited successfully', response.data)

        conn = get_db_connection()
        acc = conn.execute("""
            SELECT a.balance FROM accounts a 
            JOIN users u ON a.user_id = u.id 
            WHERE u.email = 'rahul@example.com'
        """).fetchone()
        txn = conn.execute("SELECT * FROM transactions WHERE transaction_type='deposit'").fetchone()
        conn.close()
        self.assertEqual(acc['balance'], 15000.0)
        self.assertIsNotNone(txn)
        self.assertEqual(txn['amount'], 15000.0)
        print("  [PASS] Deposit of ₹15,000 processed correctly, balance updated")

    def test_07_withdraw_money(self):
        """Test withdrawal operation with balance check"""
        with self.app as c:
            c.get('/login')
            csrf = c.session.get('_csrf_token')
            c.post('/login', data={
                'csrf_token': csrf,
                'email': 'rahul@example.com',
                'password': 'Password@123'
            })

            # Attempt withdrawal beyond balance (should fail)
            csrf = c.session.get('_csrf_token')
            fail_resp = c.post('/withdraw', data={
                'csrf_token': csrf,
                'amount': '999999',
                'description': 'Excessive'
            }, follow_redirects=True)
            self.assertIn(b'Insufficient balance', fail_resp.data)

            # Valid withdrawal
            csrf = c.session.get('_csrf_token')
            ok_resp = c.post('/withdraw', data={
                'csrf_token': csrf,
                'amount': '3000',
                'description': 'ATM Cash'
            }, follow_redirects=True)
            self.assertEqual(ok_resp.status_code, 200)
            self.assertIn(b'withdrawn successfully', ok_resp.data)

        conn = get_db_connection()
        acc = conn.execute("""
            SELECT a.balance FROM accounts a 
            JOIN users u ON a.user_id = u.id 
            WHERE u.email = 'rahul@example.com'
        """).fetchone()
        conn.close()
        self.assertEqual(acc['balance'], 12000.0)
        print("  [PASS] Withdrawal logic: prevented overdraft & processed ₹3,000 withdrawal (New balance: ₹12,000)")

    def test_08_money_transfer_between_accounts(self):
        """Create second user and test funds transfer"""
        # Register second user
        with self.app as c:
            c.get('/register')
            csrf = c.session.get('_csrf_token')
            c.post('/register', data={
                'csrf_token': csrf,
                'full_name': 'Priya Patel',
                'email': 'priya@example.com',
                'phone': '9123456780',
                'password': 'Password@123',
                'confirm_password': 'Password@123'
            })

            # Login Priya and open account
            csrf = c.session.get('_csrf_token')
            c.post('/login', data={
                'csrf_token': csrf,
                'email': 'priya@example.com',
                'password': 'Password@123'
            })
            csrf = c.session.get('_csrf_token')
            c.post('/open-account', data={
                'csrf_token': csrf,
                'account_type': 'Savings',
                'date_of_birth': '2001-05-20',
                'address': '202 Bandra West, Mumbai'
            })

        conn = get_db_connection()
        priya_acc = conn.execute("""
            SELECT a.account_number FROM accounts a 
            JOIN users u ON a.user_id = u.id 
            WHERE u.email = 'priya@example.com'
        """).fetchone()
        conn.close()
        priya_acc_num = priya_acc['account_number']

        # Rahul transfers ₹4,000 to Priya
        with self.app as c:
            c.get('/login')
            csrf = c.session.get('_csrf_token')
            c.post('/login', data={
                'csrf_token': csrf,
                'email': 'rahul@example.com',
                'password': 'Password@123'
            })

            csrf = c.session.get('_csrf_token')
            resp = c.post('/transfer', data={
                'csrf_token': csrf,
                'receiver_account': priya_acc_num,
                'amount': '4000',
                'description': 'Project Shared Expense'
            }, follow_redirects=True)
            self.assertIn(b'transferred to Priya Patel successfully', resp.data)

        # Check balances: Rahul was 12000 -> 8000; Priya was 0 -> 4000
        conn = get_db_connection()
        rahul_b = conn.execute("SELECT a.balance FROM accounts a JOIN users u ON a.user_id=u.id WHERE u.email='rahul@example.com'").fetchone()[0]
        priya_b = conn.execute("SELECT a.balance FROM accounts a JOIN users u ON a.user_id=u.id WHERE u.email='priya@example.com'").fetchone()[0]
        conn.close()
        self.assertEqual(rahul_b, 8000.0)
        self.assertEqual(priya_b, 4000.0)
        print(f"  [PASS] Inter-account transfer: Rahul (₹8,000) -> Priya (₹4,000)")

    def test_09_loan_application_and_admin_approval(self):
        """Test loan application by customer and approval by admin"""
        with self.app as c:
            # Login as Rahul
            c.get('/login')
            csrf = c.session.get('_csrf_token')
            c.post('/login', data={'csrf_token': csrf, 'email': 'rahul@example.com', 'password': 'Password@123'})

            csrf = c.session.get('_csrf_token')
            c.post('/loans', data={
                'csrf_token': csrf,
                'loan_type': 'Personal Loan',
                'amount': '100000',
                'monthly_income': '50000',
                'employment_status': 'Salaried',
                'duration_months': '24',
                'reason': 'Laptop and equipment purchase'
            }, follow_redirects=True)

        conn = get_db_connection()
        loan = conn.execute("SELECT * FROM loan_applications WHERE loan_type='Personal Loan'").fetchone()
        conn.close()
        self.assertIsNotNone(loan)
        self.assertEqual(loan['status'], 'Pending')

        # Admin logs in and approves loan
        with self.app as c:
            c.get('/login')
            csrf = c.session.get('_csrf_token')
            c.post('/login', data={'csrf_token': csrf, 'email': 'admin@kuberabank.com', 'password': 'kubera@admin2024'})
            csrf = c.session.get('_csrf_token')
            resp = c.post(f'/admin/loan/{loan["id"]}/approve', data={
                'csrf_token': csrf,
                'note': 'Approved after credit check.'
            }, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

        conn = get_db_connection()
        updated_loan = conn.execute("SELECT * FROM loan_applications WHERE id=?", (loan['id'],)).fetchone()
        conn.close()
        self.assertEqual(updated_loan['status'], 'Approved')
        print(f"  [PASS] Loan application submitted and approved by Admin ({updated_loan['application_id']})")

    def test_10_credit_card_application_and_approval(self):
        """Test credit card application and admin review"""
        with self.app as c:
            # Login Rahul
            c.get('/login')
            csrf = c.session.get('_csrf_token')
            c.post('/login', data={'csrf_token': csrf, 'email': 'rahul@example.com', 'password': 'Password@123'})
            csrf = c.session.get('_csrf_token')
            c.post('/credit-cards', data={
                'csrf_token': csrf,
                'card_type': 'Gold Card',
                'annual_income': '600000',
                'employment_type': 'Salaried'
            }, follow_redirects=True)

        conn = get_db_connection()
        card = conn.execute("SELECT * FROM credit_card_applications WHERE card_type='Gold Card'").fetchone()
        conn.close()
        self.assertIsNotNone(card)

        # Admin approves
        with self.app as c:
            c.get('/login')
            csrf = c.session.get('_csrf_token')
            c.post('/login', data={'csrf_token': csrf, 'email': 'admin@kuberabank.com', 'password': 'kubera@admin2024'})
            csrf = c.session.get('_csrf_token')
            c.post(f'/admin/card/{card["id"]}/approve', data={
                'csrf_token': csrf,
                'note': 'Gold card issued.'
            }, follow_redirects=True)

        conn = get_db_connection()
        updated_card = conn.execute("SELECT * FROM credit_card_applications WHERE id=?", (card['id'],)).fetchone()
        conn.close()
        self.assertEqual(updated_card['status'], 'Approved')
        print(f"  [PASS] Credit Card application submitted and approved ({updated_card['application_id']})")

    def test_11_chatbot_api(self):
        """Test rule-based AI Banking Assistant API"""
        with self.app as c:
            c.get('/login')
            csrf = c.session.get('_csrf_token')
            c.post('/login', data={'csrf_token': csrf, 'email': 'rahul@example.com', 'password': 'Password@123'})

            # Ask about loans
            res = c.post('/api/chatbot', json={'message': 'how to apply for personal loan'})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertIn('loan', data['reply'].lower())

            # Ask about deposit
            res2 = c.post('/api/chatbot', json={'message': 'how can I deposit money'})
            self.assertIn('deposit', res2.get_json()['reply'].lower())
        print("  [PASS] Smart Banking Assistant returns accurate responses for FAQs")

    def test_12_analytics_api(self):
        """Test Spending Analytics API endpoint"""
        with self.app as c:
            c.get('/login')
            csrf = c.session.get('_csrf_token')
            c.post('/login', data={'csrf_token': csrf, 'email': 'rahul@example.com', 'password': 'Password@123'})

            res = c.get('/api/analytics')
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertIn('months', data)
            self.assertIn('deposits', data)
            self.assertIn('withdrawals', data)
        print("  [PASS] Spending analytics API delivers Chart.js formatted data")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  RUNNING FULL TEST SUITE FOR KUBERA BANK")
    print("="*60)
    unittest.main(verbosity=1)
