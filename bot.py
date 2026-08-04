import os
import time
import requests
import subprocess
from threading import Thread
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home():
    return "ربات آنلاین!", 200

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

def send_message(chat_id, text):
    try:
        session.post(f"{BASE_URL}/sendMessage", 
                    data={"chat_id": chat_id, "text": text}, timeout=10)
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

def download_video(url):
    os.makedirs("downloads", exist_ok=True)
    cmd = [
        'yt-dlp',
        '-f', 'best[ext=mp4]/best',
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
            return os.path.join('downloads', files[-1]), "ویدیو"
        return None, None
    except:
        return None, None

print("🤖 ربات روشن شد!")
Thread(target=run_flask, daemon=True).start()

last_id = 0
while True:
    try:
        updates = get_updates(offset=last_id + 1)
        for u in updates:
            last_id = u["update_id"]
            if "message" in u:
                chat_id = u["message"]["chat"]["id"]
                text = u["message"].get("text", "")
                if text == "/start":
                    send_message(chat_id, "🎬 لینک بفرست!")
                elif text and not text.startswith("/"):
                    send_message(chat_id, "⏳ دانلود...")
                    path, title = download_video(text)
                    if path:
                        send_document(chat_id, path, "✅ دانلود شد!")
                        os.remove(path)
                    else:
                        send_message(chat_id, "❌ خطا")
        time.sleep(1)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"⚠️ {e}")
        time.sleep(5)
