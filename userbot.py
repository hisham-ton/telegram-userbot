from telethon import TelegramClient, events
import requests
import re
import time

# Telegram API
api_id = 29087738
api_hash = '5f6f0d880cbfd0131c047574df024a87'
client = TelegramClient('session_name', api_id, api_hash)

# صاحب البوت
owner_id = 1069707781

# Google Gemini Flash API
GEMINI_API_KEY = "AIzaSyDWPpiUF_8B0aAFoXntX-zICgIvc_rgQMc"

# الجروبات المسموح فيها الردود
special_group = "Notghosts_chat"
general_allowed_chats = [
    -1002151137677,
    'MG_Plus5',
    -1002163515274,
    'CryptoPlusFAMILY',
    -1002232716511
]
allowed_chats = [special_group] + general_allowed_chats
group_status = {}

# ردود خاصة
special_replies = {
    "ايه": "خدتك عليه 😏",
    "ليه": "خدتك عليه 😏",
    "قول": "ناكك بتاع الفول 😎",
    "مين": "فرده طيزك اليمين 🍑"
}

# ردود عامة
general_replies = {
    "السلام عليكم": "وعليكم السلام ورحمة الله وبركاته 🌸",
    "صباح الخير": "صباح النور ☀️",
    "مساء الخير": "مساء الورد 🌹"
}

# 🕒 تتبع آخر سلام لكل شخص
last_salams = {}

# دالة الذكاء الاصطناعي باستخدام Gemini Flash
def ask_gemini(question):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": question}]
            }]
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return reply.strip()
    except Exception as e:
        return f"🚫 خطأ من Gemini REST: {e}"

# دوال الآلة الحاسبة (جمع + ضرب فقط)
def is_strict_math_expression(text):
    pattern = r'^\s*\d+\s*[\+\*x×X]\s*\d+\s*$'
    return re.match(pattern, text)

def solve_basic_expression(expr):
    try:
        expr = expr.lower().replace('x', '*').replace('×', '*')
        result = eval(expr)
        return str(result)
    except Exception:
        return None

# الحدث الرئيسي
@client.on(events.NewMessage)
async def handler(event):
    chat = await event.get_chat()
    msg = event.raw_text.strip().lower()
    msg_words = msg.split()

    is_private = event.is_private
    chat_id = getattr(chat, 'id', None)
    chat_username = getattr(chat, 'username', None)

    # 🔒 لو جروب مش مسموح → تجاهل
    if not is_private and (chat_id not in allowed_chats) and (chat_username not in allowed_chats):
        return

    # 🛑 لو الجروب متوقف → تجاهل (حتى الذكاء الاصطناعي)
    if not is_private and not group_status.get(chat_id, True):
        return

    # ✅ الآلة الحاسبة
    if is_strict_math_expression(msg):
        result = solve_basic_expression(msg)
        if result is not None:
            if event.sender_id == owner_id:
                await event.delete()
            await event.reply(result)
            return

    # ✅ الذكاء الاصطناعي (سؤال يبدأ بـ "س")
    if msg_words and msg_words[0] == "س":
        if is_private or (chat_id in allowed_chats) or (chat_username in allowed_chats):
            if len(msg_words) < 2:
                await event.reply("❗اكتب سؤال بعد حرف س.")
                return
            question = " ".join(msg_words[1:]).strip(" ؟:")
            reply = ask_gemini(question)
            await event.reply(reply)
            return

    # ✅ أوامر التحكم في الجروبات فقط
    if not is_private:
        if chat_id not in group_status:
            group_status[chat_id] = True

        if msg == "/ايقاف":
            if event.sender_id == owner_id:
                group_status[chat_id] = False
                await event.reply("❌ تم إيقاف البوت في هذا الجروب.")
            else:
                await event.reply("🚫 الأمر ده خاص بصاحب البوت فقط.")
            return

        elif msg == "/تشغيل":
            if event.sender_id == owner_id:
                group_status[chat_id] = True
                await event.reply("✅ تم تشغيل البوت في هذا الجروب.")
            else:
                await event.reply("🚫 الأمر ده خاص بصاحب البوت فقط.")
            return

        elif msg == "/الحالة":
            status = group_status.get(chat_id, True)
            emoji = "✅ شغال" if status else "❌ واقف"
            await event.reply(f"🔍 حالة البوت في هذا الجروب: {emoji}")
            return

        # ✅ ردود خاصة لأي حد ماعدا صاحب البوت
        if chat_username == special_group and event.sender_id != owner_id:
            for keyword, reply_text in special_replies.items():
                if keyword in msg_words:
                    await event.reply(reply_text)
                    return

        # ✅ ردود عامة (السلام عليكم فيها تأخير)
        if (chat_id in general_allowed_chats) or (chat_username in general_allowed_chats):
            for keyword, reply_text in general_replies.items():
                if keyword in msg:
                    if keyword == "السلام عليكم":
                        user_id = event.sender_id
                        now = time.time()
                        last_time = last_salams.get(user_id, 0)
                        if now - last_time < 60:
                            return
                        last_salams[user_id] = now
                    await event.reply(reply_text)
                    return

# تشغيل البوت
client.start()
print("✅ البوت شغال بكل التعديلات (تشغيل/إيقاف حقيقي + ذكاء + ردود + حاسبة)")
client.run_until_disconnected()
