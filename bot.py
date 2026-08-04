import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import os
import time
import requests
import subprocess
from threading import Thread
from flask import Flask
import re
app = Flask(__name__)
@app.route('/')
def home():
    return "ربات دانلودر آنلاین!", 200

def run_flask():
    app.run(host='0.0.0.0', port=10000)

IS_RENDER = os.environ.get('RENDER', False)
TOKEN = "8493164976:AAHWrtBg5ii8QQY1OXem9dfsVV_C_ZJ5ABU"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

session = requests.Session()
session.verify = False

if not IS_RENDER:
    session.proxies = {
        'http': 'socks5://127.0.0.1:12334',
        'https': 'socks5://127.0.0.1:12334'
    }

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = reply_markup
    try:
        session.post(f"{BASE_URL}/sendMessage", json=data, timeout=10)
    except Exception as e:
        print(f"خطا: {e}")

def send_document(chat_id, file_path, caption=""):
    try:
        with open(file_path, 'rb') as f:
            session.post(f"{BASE_URL}/sendDocument",
                        data={"chat_id": chat_id, "caption": caption},
                        files={"document": f}, timeout=60)
    except Exception as e:
        send_message(chat_id, f"❌ خطا: {str(e)[:100]}")

def get_updates(offset=None):
    try:
        r = session.get(f"{BASE_URL}/getUpdates",
                       params={"timeout": 10, "offset": offset}, timeout=15)
        return r.json().get("result", []) if r.status_code == 200 else []
    except:
        return []

def download_video(url, audio_only=False, quality="best"):
    os.makedirs("downloads", exist_ok=True)
    
    if audio_only:
        cmd = [
            'yt-dlp',
            '-f', 'bestaudio/best',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '192',
            '--cookies', 'cookies.txt',
            '--restrict-filenames',
            '-o', 'downloads/%(id)s.%(ext)s',
            '--no-warnings',
            '--quiet',
            url
        ]
    else:
        if quality == "1080p":
            fmt = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]'
        elif quality == "720p":
            fmt = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]'
        elif quality == "480p":
            fmt = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]'
        else:
            fmt = 'best[ext=mp4]/best'
        
        cmd = [
            'yt-dlp',
            '-f', fmt,
            '--cookies', 'cookies.txt',
            '--restrict-filenames',
            '-o', 'downloads/%(id)s.%(ext)s',
            '--no-warnings',
            '--quiet',
            url
        ]
    
    try:
        subprocess.run(cmd, check=True, timeout=300)
        files = os.listdir('downloads')
        if files:
            return os.path.join('downloads', files[-1]), "دانلود شد"
        return None, None
    except Exception as e:
        print(f"خطا در دانلود: {e}")
        return None, None

print("🤖 ربات روشن شد!")
Thread(target=run_flask, daemon=True).start()

last_id = 0
user_data = {}

while True:
    try:
        updates = get_updates(offset=last_id + 1)
        for u in updates:
            last_id = u["update_id"]
            
            # مدیریت دکمه‌ها
            if "callback_query" in u:
                query = u["callback_query"]
                data = query["data"]
                chat_id = query["message"]["chat"]["id"]
                
                send_message(chat_id, "⏳ دانلود شروع شد...")
                
                url = user_data.get(chat_id, {}).get("url")
                if not url:
                    send_message(chat_id, "❌ لینکی پیدا نشد. دوباره بفرست.")
                    continue
                
                if data == "q_audio":
                    path, _ = download_video(url, audio_only=True)
                    if path:
                        send_document(chat_id, path, "🎵 دانلود صوتی کامل شد!")
                        os.remove(path)
                    else:
                        send_message(chat_id, "❌ خطا در دانلود صوت")
                else:
                    quality = data.replace("q_", "")
                    path, _ = download_video(url, audio_only=False, quality=quality)
                    if path:
                        send_document(chat_id, path, f"✅ ویدیو با کیفیت {quality} دانلود شد!")
                        os.remove(path)
                    else:
                        send_message(chat_id, "❌ خطا در دانلود ویدیو")
                
                continue
            
            if "message" in u:
                chat_id = u["message"]["chat"]["id"]
                text = u["message"].get("text", "")
                
                if text == "/start":
                    send_message(chat_id, 
                        "🎬 **ربات دانلودر حرفه‌ای**\n\n"
                        "لینک ویدیو یا اهنگ رو بفرست.\n"
                        "پشتیبانی از:\n"
                        "✅ یوتیوب\n"
                        "✅ اینستاگرام\n"
                        "✅ فیسبوک\n"
                        "✅ تیک‌تاک\n\n"
                        "بعد از ارسال لینک، کیفیت دلخواه رو انتخاب کن.")
                
                elif text and not text.startswith("/"):
                    user_data[chat_id] = {"url": text}
                    
                    # ساخت دکمه‌ها
                    keyboard = {
                        "inline_keyboard": [
                            [{"text": "🎥 1080p", "callback_data": "q_1080p"},
                             {"text": "🎥 720p", "callback_data": "q_720p"}],
                            [{"text": "🎥 480p", "callback_data": "q_480p"},
                             {"text": "🎵 فقط صوت (MP3)", "callback_data": "q_audio"}]
                        ]
                    }
                    send_message(chat_id, 
                        "📹 لینک دریافت شد!\n\n"
                        "حالا یکی از گزینه‌های زیر رو انتخاب کن:",
                        reply_markup=keyboard)
        
        time.sleep(1)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"⚠️ {e}")
        time.sleep(5)
