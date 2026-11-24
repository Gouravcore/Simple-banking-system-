#!/usr/bin/env python3
"""
KUBERA BANK - Quick Start Script
Run this to check everything is in place and start the app.

Usage:
    python run.py
"""

import sys
import os
import subprocess

print("\n" + "="*55)
print("  KUBERA BANK – Smart Digital Banking System")
print("  Your Wealth, Our Responsibility.")
print("="*55 + "\n")

# --- Check Python version ---
if sys.version_info < (3, 7):
    print("❌ Python 3.7+ is required. You have:", sys.version)
    sys.exit(1)
else:
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

# --- Install required packages ---
required = ['flask', 'werkzeug']
print("\n📦 Checking dependencies...")

for package in required:
    try:
        __import__(package)
        print(f"  ✅ {package} is installed")
    except ImportError:
        print(f"  ⏳ Installing {package}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '--quiet'])
        print(f"  ✅ {package} installed")

# Optional: reportlab for PDF
try:
    import reportlab
    print("  ✅ reportlab is installed (PDF statements enabled)")
except ImportError:
    print("  ⚠️  reportlab not installed (PDF statements disabled)")
    print("     To enable: pip install reportlab")

# --- Create required directories ---
print("\n📁 Creating directories...")
dirs = ['database', 'static/css', 'static/js', 'static/images',
        'static/statements', 'static/uploads', 'templates']
for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"  ✅ {d}/")

# --- Start the app ---
print("\n" + "="*55)
print("  🚀 Starting Kubera Bank server...")
print("  🌐 URL: http://127.0.0.1:5000")
print("  👤 Admin: admin@kuberabank.com")
print("  🔑 Password: kubera@admin2024")
print("="*55 + "\n")

# Import and run the app
from app import app
from database import initialize_database, create_admin_user

initialize_database()
create_admin_user()
app.run(debug=True, port=5000, host='0.0.0.0')
