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
    return "ربات پیشرفته آنلاین!", 200

def run_flask():
    app.run(host='0.0.0.0', port=10001)

TOKEN = "8493164976:AAHWrtBg5ii8QQY1OXem9dfsVV_C_ZJ5ABU"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# ===== تنظیمات بدون پروکسی =====
session = requests.Session()
session.trust_env = False
session.proxies = {'http': None, 'https': None}
session.verify = False
# ================================

USERS_FILE = 'users.json'
ADMIN_ID = 8493164976

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

def is_admin(chat_id):
    return chat_id == ADMIN_ID

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

def get_video_info(url):
    """دریافت اطلاعات ویدیو بدون دانلود"""
    cmd = ['yt-dlp', '--dump-json', '--no-warnings', '--quiet', url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            info = json.loads(result.stdout)
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'formats': len(info.get('formats', [])),
                'thumbnail': info.get('thumbnail', '')
            }
    except:
        pass
    return None

def download_video(url):
    os.makedirs("downloads", exist_ok=True)
    if os.path.exists('downloads/video.mp4'):
        os.remove('downloads/video.mp4')
    
    cmd = ['yt-dlp', '-f', 'best[ext=mp4]', '-o', 'downloads/video.mp4', url]
    try:
        subprocess.run(cmd, check=True, timeout=300)
        if os.path.exists('downloads/video.mp4') and os.path.getsize('downloads/video.mp4') > 0:
            return 'downloads/video.mp4'
    except:
        pass
    return None

print("🤖 ربات پیشرفته روشن شد!")
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
                        "🎬 **ربات پیشرفته**\n\n"
                        "📌 دستورات:\n"
                        "/info [لینک] - اطلاعات ویدیو\n"
                        "/broadcast [پیام] - ارسال به همه (مدیر)\n"
                        "/stats - تعداد کاربران")
                
                elif text.startswith('/info'):
                    url = text.replace('/info', '').strip()
                    if url:
                        info = get_video_info(url)
                        if info:
                            send_message(chat_id, 
                                f"📹 **{info['title']}**\n"
                                f"⏱ مدت: {info['duration']} ثانیه\n"
                                f"📊 کیفیت‌ها: {info['formats']}")
                        else:
                            send_message(chat_id, "❌ اطلاعاتی یافت نشد")
                    else:
                        send_message(chat_id, "❌ لینک را وارد کنید: /info [لینک]")
                
                elif text.startswith('/broadcast') and is_admin(chat_id):
                    msg = text.replace('/broadcast', '').strip()
                    if msg:
                        users = load_users()
                        count = 0
                        for uid in users:
                            try:
                                send_message(uid, f"📢 پیام از مدیریت:\n\n{msg}")
                                count += 1
                            except:
                                pass
                        send_message(chat_id, f"✅ پیام به {count} کاربر ارسال شد.")
                    else:
                        send_message(chat_id, "❌ پیام را وارد کنید: /broadcast [پیام]")
                
                elif text == "/stats":
                    count = get_user_count()
                    send_message(chat_id, f"👥 **تعداد کاربران:** {count}")
                
                elif text.startswith('http'):
                    user_data[chat_id] = {"url": text}
                    send_message(chat_id, "✅ لینک ذخیره شد.\nحالا عدد ۱ تا ۴ رو بفرست.")
                
                elif text in ["1", "2", "3", "4"]:
                    if chat_id not in user_data or "url" not in user_data[chat_id]:
                        send_message(chat_id, "❌ اول لینک بفرست!")
                        continue
                    
                    url = user_data[chat_id]["url"]
                    send_message(chat_id, "⏳ دانلود...")
                    path = download_video(url)
                    if path:
                        send_document(chat_id, path)
                        os.remove(path)
                        send_message(chat_id, "✅ دانلود شد!")
                    else:
                        send_message(chat_id, "❌ خطا")
        
        time.sleep(1)
    except KeyboardInterrupt:
        print("👋 خاموش شد!")
        break
    except Exception as e:
        print(f"⚠️ {e}")
        time.sleep(5)
