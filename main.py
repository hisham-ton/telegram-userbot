from telethon import TelegramClient, events
import requests
import re
import time
import os
from flask import Flask
from threading import Thread

# Telegram API
api_id = 29087738
api_hash = '5f6f0d880cbfd0131c047574df024a87'
client = TelegramClient('session_name', api_id, api_hash)

# صاحب البوت
owner_id = 1069707781

# Google Gemini Flash API
GEMINI_API_KEY = "AIzaSyDWPpiUF_8B0aAFoXntX-zICgIvc_rgQMc"

# الجروبات المسموح فيها الرد
special_group = "Notghosts_chat"
general_allowed_chats = {
    -1002151137677,
    -1002163515274,
    -1002232716511,
    "MG_Plus5",
    "CryptoPlusFAMILY",
}

allowed_chats = {special_group} | general_allowed_chats
group_status = set()

# ردود خاصة
special_replies = {
    "ايه": "خدتك عليه 🫢",
    "ليه": "خدتك عليه 😹",
    "قول": "ناكك بتاع الفول 🌝",
    "مين": "فرده طيزك اليمين 🫣"
}

# ردود عامة
general_replies = {
    "السلام عليكم": "وعليكم السلام ورحمة الله وبركاته 🌸"
}

# دالة استدعاء Gemini API
async def ask_gemini(question):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": question}]}]
    }
    try:
        res = requests.post(url, json=payload)
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"🚫 حصل خطأ من Gemini: {e}"

# Keep Alive Server
app = Flask('')

@app.route('/')
def home():
    return "انا شغال 😎"

def run():
    app.run(host='0.0.0.0', port=8000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# تشغيل السيرفر
keep_alive()

# الأحداث
@client.on(events.NewMessage)
async def handler(event):
    sender = await event.get_sender()
    sender_id = sender.id
    chat = await event.get_chat()
    chat_id = getattr(chat, 'id', None)
    chat_username = getattr(event.chat, 'username', None)
    msg = event.raw_text.strip()

    # الحساب الآلي
    match = re.match(r"^(\d+)\s*([+xX*])\s*(\d+)$", msg)
    if match:
        a, op, b = match.groups()
        a, b = int(a), int(b)
        if op == '+':
            result = a + b
        else:
            result = a * b
        await event.respond(str(result))
        return

    # تشغيل / إيقاف
    if msg == "ايقاف" and sender_id == owner_id:
        group_status.add(chat_id)
        await event.reply("❌ تم إيقاف البوت في هذا الجروب.")
        return
    elif msg == "تشغيل" and sender_id == owner_id:
        group_status.discard(chat_id)
        await event.reply("✅ تم تشغيل البوت في هذا الجروب.")
        return

    if chat_id in group_status:
        return

    # ردود خاصة
    if msg in special_replies and (chat_id == special_group):
        if sender_id != owner_id:
            await event.reply(special_replies[msg])
        return

    # ردود عامة
    if msg in general_replies and (chat_id in general_allowed_chats or chat_username in general_allowed_chats):
        now = time.time()
        if msg == "السلام عليكم":
            if not hasattr(event, 'last_salam'):
                event.last_salam = {}
            if time.time() - event.last_salam.get(sender_id, 0) < 60:
                return
            event.last_salam[sender_id] = time.time()
        await event.reply(general_replies[msg])
        return

    # سؤال ذكاء اصطناعي
    if msg.startswith("س") and re.fullmatch(r"س\s+.*", msg, re.DOTALL):
        if event.is_private or chat_id in allowed_chats:
            await event.reply("⏳ جاري التفكير والإجابة من Gemini 🤖")
            question = re.sub(r"^س\s+", "", msg)
            reply = await ask_gemini(question)
            await event.reply(reply)

client.start()
print("✅ البوت شغال على Koyeb...")
client.run_until_disconnected()
