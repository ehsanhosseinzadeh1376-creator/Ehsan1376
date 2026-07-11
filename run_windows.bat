@echo off
REM لانچر ویندوز - آزمون ساز
title Azmoon Saz
cd /d "%~dp0"

echo نصب پیش‌نیازها (فقط بار اول)...
pip install -r requirements.txt

echo.
echo اجرای نرم‌افزار...
python main.py

pause
