import os
import time
import requests
import subprocess
import json
from threading import Thread
from flask import Flask
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===== سرور Flask برای Render =====
app = Flask(__name__)
@app.route('/')
def home():
    return "ربات دانلودر آنلاین است!", 200

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# ===== تشخیص محیط =====
IS_RENDER = os.environ.get('RENDER', False)

TOKEN = "8493164976:AAHWrtBg5ii8QQY1OXem9dfsVV_C_ZJ5ABU"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# ===== تنظیم پروکسی بر اساس محیط =====
if IS_RENDER:
    print("🚀 اجرا روی Render - بدون پروکسی")
    session = requests.Session()
    session.verify = False
else:
    print("🖥️ اجرا روی سیستم شخصی - با پروکسی Hiddify")
    PROXY = {
        'http': 'socks5://127.0.0.1:12334',
        'https': 'socks5://127.0.0.1:12334'
    }
    session = requests.Session()
    session.proxies = PROXY
    session.verify = False

# ===== توابع ربات =====
def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        session.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"خطا در ارسال پیام: {e}")

def send_document(chat_id, file_path, caption=""):
    url = f"{BASE_URL}/sendDocument"
    try:
        with open(file_path, 'rb') as f:
            files = {"document": f}
            data = {"chat_id": chat_id, "caption": caption}
            session.post(url, data=data, files=files, timeout=60)
    except Exception as e:
        send_message(chat_id, f"❌ خطا در ارسال فایل: {str(e)[:100]}")

def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 10, "offset": offset}
    try:
        response = session.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return response.json().get("result", [])
        else:
            print(f"خطا در دریافت آپدیت: {response.status_code}")
            return []
    except Exception as e:
        print(f"خطا در get_updates: {e}")
        return []

def download_video(url, audio_only=False):
    os.makedirs("downloads", exist_ok=True)
    
    # استفاده از yt-dlp از طریق خط فرمان
    try:
        # تنظیمات برای خط فرمان
        if audio_only:
            cmd = [
                'yt-dlp',
                '-f', 'bestaudio/best',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '192',
                '--cookies', 'cookies.txt',
                '--restrict-filenames',
                '--output', 'downloads/%(id)s.%(ext)s',
                '--no-warnings',
                '--quiet',
                url
            ]
        else:
            cmd = [
                'yt-dlp',
                '-f', 'best[ext=mp4]/best',
                '--cookies', 'cookies.txt',
                '--restrict-filenames',
                '--output', 'downloads/%(id)s.%(ext)s',
                '--no-warnings',
                '--quiet',
                url
            ]
        
        # اجرای دستور
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise Exception(f"خطا در اجرای yt-dlp: {result.stderr}")
        
        # پیدا کردن فایل دانلود شده
        files = os.listdir('downloads')
        if not files:
            raise Exception("فایلی دانلود نشد")
        
        # گرفتن آخرین فایل
        filename = os.path.join('downloads', files[-1])
        
        # گرفتن عنوان از خروجی
        title = f"ویدیو از یوتیوب (ID: {os.path.splitext(files[-1])[0]})"
        
        return filename, title
        
    except subprocess.TimeoutExpired:
        raise Exception("زمان دانلود به پایان رسید")
    except Exception as e:
        raise Exception(f"خطا در دانلود: {str(e)}")

print("🤖 ربات روشن شد! منتظر پیام‌های شما هستم...")
print("📍 برای خروج Ctrl+C رو بزن")

# ===== اجرای سرور Flask در پس‌زمینه =====
Thread(target=run_flask, daemon=True).start()

# ===== حلقه اصلی ربات =====
last_update_id = 0
while True:
    try:
        updates = get_updates(offset=last_update_id + 1)
        if updates:
            print(f"📩 دریافت {len(updates)} پیام جدید")
        for update in updates:
            last_update_id = update["update_id"]
            if "message" in update:
                chat_id = update["message"]["chat"]["id"]
                text = update["message"].get("text", "")
                if text == "/start":
                    send_message(chat_id, 
                        "🎬 **ربات دانلودر حرفه‌ای**\n\n"
                        "لینک ویدیو از یوتیوب، اینستاگرام، فیسبوک، تیک‌تاک و... رو بفرست.\n"
                        "ربات به صورت خودکار بهترین کیفیت رو دانلود می‌کنه.\n\n"
                        "✅ پشتیبانی از: یوتیوب، اینستاگرام، فیسبوک، تیک‌تاک و صدها سایت دیگه"
                    )
                elif text and not text.startswith("/"):
                    send_message(chat_id, "⏳ دانلود شروع شد... لطفاً صبر کن.")
                    try:
                        filename, title = download_video(text)
                        send_document(chat_id, filename, f"✅ دانلود کامل شد!\n📁 {title}")
                        os.remove(filename)
                        print(f"🗑️ فایل پاک شد: {filename}")
                    except Exception as e:
                        send_message(chat_id, f"❌ خطا: {str(e)[:200]}")
        time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 ربات خاموش شد!")
        break
    except Exception as e:
        print(f"⚠️ خطا: {e}")
        time.sleep(5)
