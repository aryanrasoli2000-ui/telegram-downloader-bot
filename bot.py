نimport os
import time
import requests
import subprocess
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

# ===== بدون پروکسی =====
session = requests.Session()
session.verify = False

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
        return r.json().get("result", []) if r.status_code == 200 else []
    except:
        return []

def download_video(url):
    os.makedirs("downloads", exist_ok=True)
    cmd = ['yt-dlp', '-f', 'best[ext=mp4]/best', '-o', 'downloads/%(id)s.%(ext)s', '--no-warnings', url]
    try:
        subprocess.run(cmd, check=True, timeout=300)
        files = os.listdir('downloads')
        if files:
            return os.path.join('downloads', files[-1])
    except:
        pass
    return None

print("🤖 ربات بدون پروکسی روشن شد!")
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
                
                if text == "/start":
                    send_message(chat_id, "🎬 لینک ویدیو رو بفرست.")
                
                elif text.startswith('http'):
                    user_data[chat_id] = {"url": text}
                    keyboard = {
                        "inline_keyboard": [
                            [{"text": "🎥 1080p", "callback_data": "q_1080p"},
                             {"text": "🎥 720p", "callback_data": "q_720p"}],
                            [{"text": "🎥 480p", "callback_data": "q_480p"},
                             {"text": "🎵 صوت", "callback_data": "q_audio"}]
                        ]
                    }
                    send_message(chat_id, "کیفیت رو انتخاب کن:")
                    session.post(f"{BASE_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "کیفیت رو انتخاب کن:",
                        "reply_markup": keyboard
                    })
        
        time.sleep(1)
    except Exception as e:
        print(f"⚠️ {e}")
        time.sleep(5)
