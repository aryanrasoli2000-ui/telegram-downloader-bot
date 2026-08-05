import os
import time
import requests
import subprocess
import json
from threading import Thread
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home():
    return "ربات دانلودر آنلاین!", 200

def run_flask():
    app.run(host='0.0.0.0', port=10000)

TOKEN = "8493164976:AAHWrtBg5ii8QQY1OXem9dfsVV_C_ZJ5ABU"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

session = requests.Session()
# ===== غیرفعال کردن پروکسی =====
session.trust_env = False
session.proxies = {}
# ================================
session.verify = False

# ===== سیستم شمارش کاربران =====
USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f)

def get_user_count():
    return len(load_users())
# ==============================

# ===== پنل مدیریت =====
ADMIN_ID = 8493164976

def is_admin(chat_id):
    return chat_id == ADMIN_ID
# =====================

def send_message(chat_id, text):
    try:
        session.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        print(f"خطا: {e}")

def send_document(chat_id, file_path):
    try:
        with open(file_path, 'rb') as f:
            session.post(f"{BASE_URL}/sendDocument", data={"chat_id": chat_id}, files={"document": f}, timeout=60)
    except Exception as e:
        send_message(chat_id, f"❌ خطا: {str(e)[:100]}")

def get_updates(offset=None):
    try:
        r = session.get(f"{BASE_URL}/getUpdates", params={"timeout": 10, "offset": offset}, timeout=15)
        if r.status_code == 200:
            return r.json().get("result", [])
        return []
    except:
        return []

def download_video(url, quality="best"):
    os.makedirs("downloads", exist_ok=True)
    
    cmd = [
        'yt-dlp',
        '--cookies', 'cookies.txt',
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        '--no-warnings',
        '--quiet',
        '--no-check-certificate',
        '-o', 'downloads/%(id)s.%(ext)s'
    ]
    
    if quality == "audio":
        cmd.extend([
            '-f', 'bestaudio/best',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '192'
        ])
    elif quality == "1080":
        cmd.extend(['-f', 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]'])
    elif quality == "720":
        cmd.extend(['-f', 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]'])
    elif quality == "480":
        cmd.extend(['-f', 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]'])
    else:
        cmd.extend(['-f', 'best[ext=mp4]/best'])
    
    cmd.append(url)
    
    try:
        subprocess.run(cmd, check=True, timeout=300)
        files = os.listdir('downloads')
        if files:
            files.sort(key=lambda x: os.path.getmtime(os.path.join('downloads', x)), reverse=True)
            return os.path.join('downloads', files[0])
    except Exception as e:
        print(f"خطا در دانلود: {e}")
    return None

print("🤖 ربات روشن شد!")
Thread(target=run_flask, daemon=True).start()

last_id = 0
user_data = {}

while True:
    try:
        updates = get_updates(offset=last_id + 1)
        for u in updates:
            last_id = u["update_id"]
            if "message" in u:
                chat_id = u["message"]["chat"]["id"]
                text = u["message"].get("text", "")
                
                save_user(chat_id)
                
                if text == "/start":
                    send_message(chat_id, 
                        "🎬 **ربات دانلودر**\n\n"
                        "لینک ویدیو رو بفرست.\n"
                        "بعدش عدد ۱ تا ۴ رو بفرست:\n"
                        "1️⃣ = 1080p\n"
                        "2️⃣ = 720p\n"
                        "3️⃣ = 480p\n"
                        "4️⃣ = فقط صوت (MP3)")
                
                elif text == "/stats":
                    count = get_user_count()
                    send_message(chat_id, f"👥 **تعداد کاربران ربات:** {count}")
                
                elif text == "/broadcast" and is_admin(chat_id):
                    user_data[chat_id] = {"mode": "broadcast"}
                    send_message(chat_id, "📢 پیام عمومی رو بفرست:")
                
                elif chat_id in user_data and user_data[chat_id].get("mode") == "broadcast":
                    msg = text
                    users = load_users()
                    for uid in users:
                        try:
                            send_message(uid, f"📢 پیام از مدیریت:\n\n{msg}")
                        except:
                            pass
                    send_message(chat_id, f"✅ پیام به {len(users)} کاربر ارسال شد.")
                    user_data[chat_id] = {}
                
                elif text.startswith('http'):
                    user_data[chat_id] = {"url": text}
                    send_message(chat_id, "✅ لینک ذخیره شد.\nحالا عدد ۱ تا ۴ رو بفرست.")
                
                elif text in ["1", "2", "3", "4"]:
                    if chat_id not in user_data or "url" not in user_data[chat_id]:
                        send_message(chat_id, "❌ اول یه لینک معتبر بفرست!")
                        continue
                    
                    url = user_data[chat_id]["url"]
                    send_message(chat_id, "⏳ دانلود شروع شد...")
                    
                    if text == "4":
                        path = download_video(url, "audio")
                        if path:
                            send_document(chat_id, path)
                            os.remove(path)
                            send_message(chat_id, "✅ دانلود صوتی کامل شد!")
                        else:
                            send_message(chat_id, "❌ خطا در دانلود صوت")
                    else:
                        quality_map = {"1": "1080", "2": "720", "3": "480"}
                        quality = quality_map[text]
                        path = download_video(url, quality)
                        if path:
                            send_document(chat_id, path)
                            os.remove(path)
                            send_message(chat_id, f"✅ ویدیو با کیفیت {quality}p دانلود شد!")
                        else:
                            send_message(chat_id, "❌ خطا در دانلود ویدیو")
        
        time.sleep(1)
    except KeyboardInterrupt:
        print("👋 ربات خاموش شد!")
        break
    except Exception as e:
        print(f"⚠️ خطا: {e}")
        time.sleep(5)