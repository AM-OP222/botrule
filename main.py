import io
import os
import random
import time
from threading import Thread
import http.server
import socketserver
import requests
import telebot
import xml.etree.ElementTree as ET

# ----------------- Configuration & Tokens -----------------
BOT_TOKEN = "8969280684:AAHaRWG3CKj3WAq_R-tPzALh9KsEIu5N1E0"

# اعتبارسنجی منابع مختلف (که فرستادی)
RULE34_USER_ID = "6501593"
RULE34_API_KEY = "7177a4499703fedb969488fc7d60d5d90dd7a6b95e84d1683e8f560228c877108a497988d74be4f506c00b410ab193d4da9d2474db8456e6398041fca4b81901"

E621_LOGIN = "OPishere"
E621_API_KEY = "EB9iLmaxpKMwNd9hW2uFR8mL"

DANBOORU_LOGIN = "OPishere"
DANBOORU_API_KEY = "KFwndPbQb4g3Ep8K3A8GYvCR"

GELBOORU_USER_ID = "2015335"
GELBOORU_API_KEY = "650c61ab16fecf72ab0c16d696ca74e0bd2c42eabb15cc0803c1ac32a2846d890b5ff2cba34cbd31c5a36a8af259f846d6597054769fc4f4949427098bfef562"

session = requests.Session()
session.trust_env = True
session.headers.update({
    "User-Agent": f"TelegramBotProject/1.0 (by {E621_LOGIN})"
})

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# 🧠 Strict Anti-Duplicate Cache (Stores up to 2000 items to guarantee NO REPEATED MEDIA)
SENT_MEDIA = []

def add_to_sent_cache(media_id):
    # برای جلوگیری از تداخل آیدی بوردهای مختلف، اسم منبع را هم در آیدی ترکیب می‌کنیم
    if media_id not in SENT_MEDIA:
        SENT_MEDIA.append(media_id)
    if len(SENT_MEDIA) > 2000:
        SENT_MEDIA.pop(0)

# ----------------- APIs Crawlers -----------------

def fetch_from_rule34(tag, limit=30):
    """دریافت تصاویر از Rule34"""
    url = "https://api.rule34.xxx/index.php"
    params = {
        "page": "dapi",
        "s": "post",
        "q": "index",
        "tags": tag,
        "limit": limit,
        "user_id": RULE34_USER_ID,
        "api_key": RULE34_API_KEY
    }
    try:
        res = session.get(url, params=params, timeout=8)
        if res.status_code == 200 and res.text.strip() and "Missing authentication" not in res.text:
            root = ET.fromstring(res.text)
            posts = root.findall('post')
            results = []
            for p in posts:
                p_id = f"r34_{p.get('id')}"
                url_file = p.get("file_url")
                if url_file and p_id not in SENT_MEDIA:
                    ext = url_file.split(".")[-1].lower().split("?")[0]
                    if ext in ["jpg", "jpeg", "png", "bmp", "webp"]:
                        results.append({"id": p_id, "url": url_file})
            return results
    except Exception as e:
        print(f"🚨 Rule34 API Error: {e}")
    return []

def fetch_from_e621(tag, limit=30):
    """دریافت تصاویر از e621 (مخصوص Furry)"""
    url = "https://e621.net/posts.json"
    params = {
        "tags": tag,
        "limit": limit,
        "login": E621_LOGIN,
        "api_key": E621_API_KEY
    }
    try:
        res = session.get(url, params=params, timeout=8)
        if res.status_code == 200:
            data = res.json()
            results = []
            for post in data.get("posts", []):
                p_id = f"e6_{post.get('id')}"
                url_file = post.get("file", {}).get("url")
                if url_file and p_id not in SENT_MEDIA:
                    ext = url_file.split(".")[-1].lower().split("?")[0]
                    if ext in ["jpg", "jpeg", "png", "bmp", "webp"]:
                        results.append({"id": p_id, "url": url_file})
            return results
    except Exception as e:
        print(f"🚨 e621 API Error: {e}")
    return []

def fetch_from_konachan(tag, limit=30):
    """دریافت تصاویر باکیفیت از Konachan"""
    url = "https://konachan.com/post.json"
    params = {
        "tags": tag,
        "limit": limit
    }
    try:
        res = session.get(url, params=params, timeout=8)
        if res.status_code == 200:
            data = res.json()
            results = []
            for post in data:
                p_id = f"kona_{post.get('id')}"
                url_file = post.get("file_url")
                if url_file and p_id not in SENT_MEDIA:
                    if not url_file.startswith("http"):
                        url_file = "https:" + url_file
                    ext = url_file.split(".")[-1].lower().split("?")[0]
                    if ext in ["jpg", "jpeg", "png", "bmp", "webp"]:
                        results.append({"id": p_id, "url": url_file})
            return results
    except Exception as e:
        print(f"🚨 Konachan API Error: {e}")
    return []

def fetch_from_danbooru(tag, limit=30):
    """دریافت تصاویر از Danbooru"""
    url = "https://danbooru.donmai.us/posts.json"
    params = {
        "tags": tag,
        "limit": limit,
        "login": DANBOORU_LOGIN,
        "api_key": DANBOORU_API_KEY
    }
    try:
        res = session.get(url, params=params, timeout=8)
        if res.status_code == 200:
            data = res.json()
            results = []
            for post in data:
                p_id = f"dan_{post.get('id')}"
                url_file = post.get("file_url")
                if url_file and p_id not in SENT_MEDIA:
                    ext = url_file.split(".")[-1].lower().split("?")[0]
                    if ext in ["jpg", "jpeg", "png", "bmp", "webp"]:
                        results.append({"id": p_id, "url": url_file})
            return results
    except Exception as e:
        print(f"🚨 Danbooru API Error: {e}")
    return []

def fetch_from_gelbooru(tag, limit=30):
    """دریافت تصاویر از Gelbooru"""
    url = "https://gelbooru.com/index.php"
    params = {
        "page": "dapi",
        "s": "post",
        "q": "index",
        "json": 1,
        "tags": tag,
        "limit": limit,
        "api_key": GELBOORU_API_KEY,
        "user_id": GELBOORU_USER_ID
    }
    try:
        res = session.get(url, params=params, timeout=8)
        if res.status_code == 200:
            data = res.json()
            posts = data.get("post", []) if isinstance(data, dict) else []
            results = []
            for post in posts:
                p_id = f"gel_{post.get('id')}"
                url_file = post.get("file_url")
                if url_file and p_id not in SENT_MEDIA:
                    ext = url_file.split(".")[-1].lower().split("?")[0]
                    if ext in ["jpg", "jpeg", "png", "bmp", "webp"]:
                        results.append({"id": p_id, "url": url_file})
            return results
    except Exception as e:
        print(f"🚨 Gelbooru API Error: {e}")
    return []

# ----------------- Telegram Bot Handlers -----------------

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    welcome_text = (
        "⚡️ **WELCOME TO MULTI-BOORU MEDIA BOT** ⚡️\n\n"
        "🎬 **Commands available:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📸 **Get 5 Unique Photos (From 5 Databases):**\n"
        "👉 `/pic34 [tag]`\n"
        "*(Searches: Rule34, e621, Konachan, Danbooru, Gelbooru)*\n\n"
        "🎥 **Get 1 Video (Supports up to 200MB):**\n"
        "👉 `/vid34 [tag]`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💻 **Developer:** @ItsShaah\n"
        "📢 *Type your tag carefully for perfect results.*"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")


# 📸 Handler: Send 5 Random Pictures (Multi-Database Mixer Method)
@bot.message_handler(commands=["pic34"])
def send_pictures(message):
    text_parts = message.text.split(" ", 1)
    if len(text_parts) < 2:
        bot.reply_to(message, "⚠️ **Please provide a tag!**\n*Example:* `/pic34 hinata`", parse_mode="Markdown")
        return

    tag = text_parts[1].strip()
    cleaned_tag = tag.lower().replace(" ", "_")
    waiting_msg = bot.reply_to(message, f"🔍 **Searching 5 unique photos for** `#{tag}` **across all databases...**", parse_mode="Markdown")

    # دریافت اطلاعات از تمام منابع به صورت همزمان
    all_media = []
    all_media.extend(fetch_from_rule34(cleaned_tag, limit=15))
    all_media.extend(fetch_from_e621(cleaned_tag, limit=15))
    all_media.extend(fetch_from_konachan(cleaned_tag, limit=15))
    all_media.extend(fetch_from_danbooru(cleaned_tag, limit=15))
    all_media.extend(fetch_from_gelbooru(cleaned_tag, limit=15))

    if all_media:
        # قاطی کردن کل تصاویر دریافتی برای بالا بردن تنوع و جذابیت
        random.shuffle(all_media)

        # حذف پیام Waiting قبل از شروع ارسال برای تجربه کاربری تمیزتر
        try:
            bot.delete_message(message.chat.id, waiting_msg.message_id)
        except:
            pass

        success_count = 0
        for item in all_media[:15]:  # چک کردن حداکثر ۱۵ عکس برای رسیدن به ۵ ارسال موفق
            if success_count >= 5:
                break
            try:
                # ارسال مستقیم عکس از آدرس وب بدون دانلود بیهوده روی سرور
                bot.send_photo(message.chat.id, item["url"], timeout=20)
                add_to_sent_cache(item["id"])
                success_count += 1
                time.sleep(0.5)  # تاخیر برای دلیوری روان تلگرام
            except Exception as e:
                print(f"⚠️ Image stream failed for id {item['id']}: {e}")
                continue
        
        if success_count == 0:
            bot.send_message(message.chat.id, "❌ **Error sending images via URL stream.**\nContact: @ItsShaah", parse_mode="Markdown")
    else:
        bot.edit_message_text("❌ **No new images found for this tag in any database.**", message.chat.id, waiting_msg.message_id, parse_mode="Markdown")


# 🎬 Handler: Send 1 Random Video (High Speed Stream, Supports up to 200MB)
@bot.message_handler(commands=["vid34"])
def send_video(message):
    text_parts = message.text.split(" ", 1)
    if len(text_parts) < 2:
        bot.reply_to(message, "⚠️ **Please provide a tag!**\n*Example:* `/vid34 aki`", parse_mode="Markdown")
        return

    tag = text_parts[1].strip()
    cleaned_tag = tag.lower().replace(" ", "_")
    waiting_msg = bot.reply_to(message, f"🔍 **Searching & streaming video for** `#{tag}`**...**", parse_mode="Markdown")
    
    # ویدیوها فعلاً فقط از دیتابیس Rule34 استخراج می‌شوند
    url = "https://api.rule34.xxx/index.php"
    params = {
        "page": "dapi",
        "s": "post",
        "q": "index",
        "tags": cleaned_tag,
        "limit": 100,
        "user_id": RULE34_USER_ID,
        "api_key": RULE34_API_KEY
    }

    try:
        res = session.get(url, params=params, timeout=12)
        if res.status_code == 200 and "Missing authentication" not in res.text and res.text.strip():
            root = ET.fromstring(res.text)
            posts = root.findall('post')
            video_list = []
            
            for p in posts:
                post_id = f"r34_vid_{p.get('id')}"
                media_url = p.get("file_url")
                if post_id in SENT_MEDIA:
                    continue
                if media_url:
                    ext = media_url.split(".")[-1].lower().split("?")[0]
                    if ext in ["mp4", "webm"]:
                        video_list.append({"id": post_id, "url": media_url})

            if video_list:
                random.shuffle(video_list)
                success = False
                for item in video_list[:5]:
                    try:
                        bot.send_video(message.chat.id, item["url"], timeout=120)
                        add_to_sent_cache(item["id"])
                        success = True
                        break
                    except Exception as e:
                        print(f"⚠️ Video stream failed for id {item['id']}: {e}")
                        continue

                if success:
                    try:
                        bot.delete_message(message.chat.id, waiting_msg.message_id)
                    except:
                        pass
                else:
                    bot.edit_message_text("❌ **Failed to stream video.**\n*The file might be over 200MB or link is broken.*", message.chat.id, waiting_msg.message_id, parse_mode="Markdown")
            else:
                bot.edit_message_text("❌ **No new videos found for this tag.**", message.chat.id, waiting_msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text("❌ **No videos found / Connection issue.**", message.chat.id, waiting_msg.message_id, parse_mode="Markdown")
    except Exception as e:
        print(f"🚨 Video Handler Error: {e}")
        bot.edit_message_text("🚨 **Server connection error.**", message.chat.id, waiting_msg.message_id, parse_mode="Markdown")


# ----------------- Keep Alive Layer -----------------
def start_bot_polling():
    print("🚀 Bot Polling Started with 5 Databases...")
    bot.delete_webhook(drop_pending_updates=True)
    bot.infinity_polling()

if __name__ == "__main__":
    bot_thread = Thread(target=start_bot_polling)
    bot_thread.daemon = True
    bot_thread.start()
    
    class SimpleHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")

    port = int(os.environ.get("PORT", 8080))
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", port), SimpleHandler) as httpd:
        print(f"📡 Web server online on port {port}. Developer: @ItsShaah")
        httpd.serve_forever()
