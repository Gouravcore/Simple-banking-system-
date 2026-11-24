# 📄 KUBERA BANK – Comprehensive Project Documentation

**Project Title**: KUBERA BANK – Smart Digital Banking System  
**Tagline**: "Your Wealth, Our Responsibility"  
**Academic Level**: College Micro-Project (First-Year Undergraduate)  
**Architecture**: Model-View-Controller (MVC) Pattern with Python Flask & SQLite  

---

## 1. System Architecture & Flow

Kubera Bank follows the standard **Model-View-Controller (MVC)** architectural pattern:

- **Model (`database.py`)**: Defines SQLite schema, foreign keys, and direct database queries via parameterized execution.
- **View (`/templates/*.html`, `/static/css/*.css`, `/static/js/*.js`)**: Jinja2-templated HTML5 views styled with an original, brand-centric banking color palette (Deep Red `#B71C1C`, Royal Gold `#D4AF37`, Off-White `#FAF9F6`, and Dark Charcoal `#252525`).
- **Controller (`app.py`)**: Manages routing, session security, business logic, form validation, and JSON REST endpoints for analytics and chatbot integration.

```
       +-------------------------------------------------------+
       |                     Web Browser                       |
       |  HTML5 + CSS3 + Bootstrap + GSAP + Chart.js + JS      |
       +-------------------------------------------------------+
                                  |
                                  | HTTP Requests (GET / POST)
                                  v
       +-------------------------------------------------------+
       |               Flask Application (app.py)              |
       |  - Routing & Controllers                              |
       |  - Session & CSRF Security                            |
       |  - ReportLab PDF Statement Engine                     |
       |  - Smart Banking Assistant (Chatbot API)              |
       +-------------------------------------------------------+
                                  |
                                  | Python DB-API (sqlite3)
                                  v
       +-------------------------------------------------------+
       |                  SQLite Database                      |
       |  - users, accounts, transactions                      |
       |  - loan_applications, credit_card_applications       |
       |  - notifications                                      |
       +-------------------------------------------------------+
```

---

## 2. Detailed Functional Modules

### Module 1: User Onboarding & Identity
- **Registration**: Captures full name, email, mobile phone, and password.
- **Customer ID Algorithm**: `KB` + current year + 4 random digits (e.g. `KB20248492`), ensuring uniqueness across the database.
- **Password Protection**: Passwords are salted and hashed using Werkzeug (`scrypt`/`pbkdf2:sha256`).

### Module 2: Account Opening & Management
- Accounts can be created as either **Savings** or **Current**.
- Generates a unique 12-digit account number.
- Records date of birth, home address, and initial zero balance.
- Associates one primary account per user.

### Module 3: Cash Deposits & Withdrawals
- **Deposit**:
  - Enforces positive numbers (> 0) and validates maximum limits.
  - Updates the account balance and records a transaction log entry.
  - Generates a unique Transaction ID (`TXN` + hexadecimal string).
  - Sends a confirmation notification to the user's notification center.
- **Withdrawal**:
  - Validates that the requested amount is strictly less than or equal to the current balance.
  - Protects against overdrafts and invalid numeric entries.
  - Updates the balance, creates a transaction record, and notifies the account holder.

### Module 4: Inter-Account Funds Transfer
- Accepts the recipient's 12-digit account number and the transfer amount.
- Validates that the recipient account exists in the database and is not the sender's own account.
- Checks that the sender has sufficient balance.
- Updates sender and recipient balances.
- Creates two synchronized transaction records:
  - `transfer_out` on the sender's account with the recipient's account number as reference.
  - `transfer_in` on the recipient's account with the sender's account number as reference.
- Delivers instant notifications to both parties.

### Module 5: Credit Cards & Loans
- **Loans**: Customers can apply for Personal, Education, or Home loans, specifying loan duration, monthly income, employment status, and reason.
- **Live EMI Calculator**: On frontend input, the estimated monthly installment is computed dynamically in JavaScript using the compound interest formula:
  $$\text{EMI} = \frac{P \times r \times (1+r)^n}{(1+r)^n - 1}$$
- **Credit Cards**: Customers can review benefits for Classic, Gold, or Premium cards and apply with annual income verification.
- **Status Tracking**: Both cards and loans display real-time status badges: `Pending`, `Approved`, or `Rejected`.

### Module 6: Manager / Admin Portal
- Accessible exclusively by accounts with `is_admin = 1`.
- View macro financial metrics: total customer count, total open accounts, total bank transactions, and total cumulative deposits.
- One-click approval/rejection modal for loan applications and credit card applications with personalized bank notes.
- Master transaction ledger displaying every account movement.

### Module 7: Smart Banking Assistant (Chatbot)
- Rule-based natural language parser located at `/api/chatbot`.
- Recognizes user intent through keyword clustering (e.g. "open account", "interest rate", "how to deposit", "statement", "security").
- Delivers clean, formatted answers instantly without external paid APIs.

### Module 8: PDF Statement Generation
- Built with the Python **ReportLab** library.
- Formats customer details, account summary, and the last 50 transactions into a formal tabular document with deep red and gold headers.

---

## 3. Security & Validation Practices

1. **SQL Injection Prevention**: All queries in `app.py` use parameterized SQL queries (`?` placeholders) and never string formatting or interpolation.
2. **Session Hijacking Prevention**: Sessions are encrypted using Flask's `SECRET_KEY` generated via `secrets.token_hex(32)`.
3. **Cross-Site Request Forgery (CSRF)**: Custom `@app.before_request` middleware validates cryptographic CSRF tokens on all state-changing `POST` submissions.
4. **Access Control**: `@login_required` and `@admin_required` decorators ensure that unauthorized users cannot inspect or manipulate other customers' balances or admin pages.

---

## 4. How to Explain This Project in a Viva (Tips for First-Year Students)

1. **Start with the Problem Statement**: "Kubera Bank simulates a full-stack digital bank, demonstrating modern fintech architectures from user onboarding to double-entry transaction integrity and administrative oversight."
2. **Highlight the Frontend Innovation**: "Rather than static corporate templates, we implemented a 2.5D architectural scroll entrance using GSAP and ScrollTrigger that simulates stepping into a physical bank."
3. **Emphasize Database Consistency**: "All money transfers update both sender and receiver accounts within transaction controls so money is never lost in transit."
4. **Mention Code Clarity**: "The code is cleanly modularized into `app.py` for controllers, `database.py` for models, and `config.py` for environment parameters, avoiding complex frameworks like React to maintain transparent first-year readability."
