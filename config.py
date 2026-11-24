"""
KUBERA BANK - Configuration File
---------------------------------
This file holds all important settings for the Flask application.
Students: You can change these settings as needed.
"""

import os
import secrets

# Base directory of our project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Secret key is used to protect user sessions and CSRF tokens
    # We generate a random secret key for security
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    # Database location - stored in the /database folder
    DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'kubera_bank.db')

    # Upload folder for any files
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

    # Admin credentials (change these in production!)
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'kubera@admin2024'

    # Bank settings
    BANK_NAME = 'Kubera Bank'
    BANK_TAGLINE = 'Your Wealth, Our Responsibility.'

    # Minimum balance required (some banks require a minimum)
    MIN_BALANCE = 0.0

    # Maximum transfer limit per transaction
    MAX_TRANSFER_LIMIT = 1000000.0

    # PDF statement folder
    STATEMENTS_FOLDER = os.path.join(BASE_DIR, 'static', 'statements')
