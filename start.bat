@echo off
title Kubera Bank - Smart Digital Banking System
color 0A

echo.
echo  ============================================
echo   KUBERA BANK - Smart Digital Banking System
echo   Your Wealth, Our Responsibility.
echo  ============================================
echo.

:: Check if Python is installed
python --version 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [1/3] Installing required packages...
python -m pip install Flask Werkzeug reportlab --quiet

if errorlevel 1 (
    echo [ERROR] Failed to install packages. Check your internet connection.
    pause
    exit /b 1
)

echo [2/3] Creating database directory...
if not exist "database" mkdir database
if not exist "static\statements" mkdir static\statements
if not exist "static\uploads" mkdir static\uploads

echo [3/3] Starting Kubera Bank server...
echo.
echo  ============================================
echo   Server running at: http://127.0.0.1:5000
echo   Admin: admin@kuberabank.com / kubera@admin2024
echo  ============================================
echo.
echo  Press CTRL+C to stop the server.
echo.

python app.py

pause
