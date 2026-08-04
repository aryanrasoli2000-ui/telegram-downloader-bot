import sys
import os
import yt_dlp
import time
import urllib3
import requests
from threading import Thread
from flask import Flask
import locale

# ===== تنظیم encoding به روش امن =====
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except:
    pass

# ===== سرور Flask برای Render =====
app = Flask(__name__)
@app.route('/')
def home():
    return "ربات دانلودر آنلاین است!", 200

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# ===== تشخیص محیط =====
IS_RENDER = os.environ.get('RENDER', False)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    
    # تنظیمات نهایی برای حل مشکل encoding
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt',
        'restrictfilenames': True,
        'compat_options': ['filename-sanitization'],
        'ignoreerrors': True,
        'extract_flat': 'in_playlist',  # فقط اطلاعات اصلی را بگیر
        'format': 'best[ext=mp4]/best',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'extractor_args': {
            'youtube': {
                'skip': ['hls', 'dash', 'description', 'metadata'],
                'player_client': ['android', 'web'],
            }
        }
    }
    
    if audio_only:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if audio_only:
                filename = filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')
            
            # عنوان ساده برای کپشن
            title = info.get('title', f"ویدیو-{info.get('id', 'N/A')}")
            return filename, title
    except Exception as e:
        # اگر خطا بود، با تنظیمات ساده‌تر امتحان کن
        simple_opts = {
            'outtmpl': 'downloads/video_%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'cookiefile': 'cookies.txt',
            'skip_download': False,
            'format': 'best[ext=mp4]/best',
            'ignoreerrors': True,
        }
        try:
            with yt_dlp.YoutubeDL(simple_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return filename, f"ویدیو-{info.get('id', 'N/A')}"
        except Exception as e2:
            raise Exception(f"خطا در دانلود: {str(e2)}")

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
