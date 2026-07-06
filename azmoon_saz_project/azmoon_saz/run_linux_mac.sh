#!/usr/bin/env bash
# لانچر لینوکس/مک - آزمون ساز
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "🔧 ایجاد محیط مجازی پایتون..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "📦 نصب پیش‌نیازها..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "🚀 اجرای نرم‌افزار..."
python main.py
