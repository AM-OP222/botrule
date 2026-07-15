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
USER_ID = "6501593"
API_KEY = "7177a4499703fedb969488fc7d60d5d90dd7a6b95e84d1683e8f560228c877108a497988d74be4f506c00b410ab193d4da9d2474db8456e6398041fca4b81901"

session = requests.Session()
session.trust_env = True
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# 🧠 Strict Anti-Duplicate Cache (Stores up to 1000 items to guarantee NO REPEATED MEDIA)
SENT_MEDIA = []

def add_to_sent_cache(media_id):
    if media_id not in SENT_MEDIA:
        SENT_MEDIA.append(media_id)
    if len(SENT_MEDIA) > 1000:
        SENT_MEDIA.pop(0)

# ----------------- Helper Functions -----------------
def fetch_media_from_api(tag, mode="pic"):
    url = "https://api.rule34.xxx/index.php"
    cleaned_tag = tag.lower().strip().replace(" ", "_")
    
    params = {
        "page": "dapi",
        "s": "post",
        "q": "index",
        "tags": cleaned_tag,
        "limit": 100,
        "user_id": USER_ID,
        "api_key": API_KEY
    }

    try:
        response = session.get(url, params=params, timeout=12)
        if response.status_code == 200:
            if "Missing authentication" in response.text:
                return None, "auth_error"
            if not response.text.strip():
                return None, "no_posts"
                
            root = ET.fromstring(response.text)
            posts = root.findall('post')

            if posts and len(posts) > 0:
                media_list = []
                for p in posts:
                    post_id = p.get("id")
                    media_url = p.get("file_url")
                    
                    # 100% Duplicate Filter
                    if post_id in SENT_MEDIA:
                        continue
                        
                    if media_url:
                        ext = media_url.split(".")[-1].lower().split("?")[0]
                        if mode == "pic" and ext in ["jpg", "jpeg", "png", "bmp", "webp"]:
                            media_list.append({"id": post_id, "url": media_url})
                        elif mode == "vid" and ext in ["mp4", "webm"]:
                            media_list.append({"id": post_id, "url": media_url})

                if media_list:
                    random.shuffle(media_list)
                    return media_list, "success"
                else:
                    return None, "no_new_media"
            else:
                return None, "no_posts"
    except Exception as e:
        print(f"🚨 API Error: {e}")
    return None, "error"

# ----------------- Telegram Bot Handlers -----------------

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    welcome_text = (
        "⚡️ **WELCOME TO 34 MEDIA BOT** ⚡️\n\n"
        "🎬 **Commands available:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📸 **Get 5 Unique Photos (Ultra Fast):**\n"
        "👉 `/pic34 [tag]`\n\n"
        "🎥 **Get 1 Video (Supports up to 200MB):**\n"
        "👉 `/vid34 [tag]`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💻 **Developer:** @ItsShaah\n"
        "📢 *Type your tag carefully for perfect results.*"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")


# 📸 Handler: Send 5 Random Pictures (Ultra Fast URL Stream Method)
@bot.message_handler(commands=["pic34"])
def send_pictures(message):
    text_parts = message.text.split(" ", 1)
    if len(text_parts) < 2:
        bot.reply_to(message, "⚠️ **Please provide a tag!**\n*Example:* `/pic34 hinata`", parse_mode="Markdown")
        return

    tag = text_parts[1].strip()
    waiting_msg = bot.reply_to(message, f"🔍 **Searching 5 unique photos for** `#{tag}`**...**", parse_mode="Markdown")
    media_list, status = fetch_media_from_api(tag, mode="pic")

    if media_list and status == "success":
        # حذف پیام Waiting قبل از شروع ارسال برای تجربه کاربری تمیزتر
        try:
            bot.delete_message(message.chat.id, waiting_msg.message_id)
        except:
            pass

        success_count = 0
        for item in media_list[:10]:  # حداکثر ۱۰ مورد را امتحان می‌کند تا حتماً ۵ ارسال موفق داشته باشد
            if success_count >= 5:
                break
            try:
                # ارسال مستقیم عکس از طریق آدرس وب بدون دانلود روی رندر
                bot.send_photo(message.chat.id, item["url"], timeout=20)
                add_to_sent_cache(item["id"])
                success_count += 1
                time.sleep(0.5)  # تاخیر بسیار کم فقط برای رعایت قوانین دلیوری تلگرام
            except Exception as e:
                print(f"⚠️ Image stream failed for id {item['id']}: {e}")
                continue
        
        if success_count == 0:
            bot.send_message(message.chat.id, "❌ **Error sending images via URL stream.**\nContact: @ItsShaah", parse_mode="Markdown")
    else:
        error_msg = "❌ **No new images found for this tag.**" if status == "no_new_media" or status == "no_posts" else "🚨 **Server connection error.**"
        bot.edit_message_text(error_msg, message.chat.id, waiting_msg.message_id, parse_mode="Markdown")


# 🎬 Handler: Send 1 Random Video (High Speed Stream, Supports up to 200MB)
@bot.message_handler(commands=["vid34"])
def send_video(message):
    text_parts = message.text.split(" ", 1)
    if len(text_parts) < 2:
        bot.reply_to(message, "⚠️ **Please provide a tag!**\n*Example:* `/vid34 aki`", parse_mode="Markdown")
        return

    tag = text_parts[1].strip()
    waiting_msg = bot.reply_to(message, f"🔍 **Searching & streaming video for** `#{tag}`**...**", parse_mode="Markdown")
    media_list, status = fetch_media_from_api(tag, mode="vid")

    if media_list and status == "success":
        success = False
        
        for item in media_list[:5]:
            try:
                bot.send_video(message.chat.id, item["url"], timeout=120)
                add_to_sent_cache(item["id"])
                success = True
                break
            except Exception as e:
                print(f"⚠️ Stream failed for id {item['id']}: {e}")
                continue

        if success:
            try:
                bot.delete_message(message.chat.id, waiting_msg.message_id)
            except:
                pass
        else:
            bot.edit_message_text("❌ **Failed to stream video.**\n*The file might be over 200MB or link is broken.*", message.chat.id, waiting_msg.message_id, parse_mode="Markdown")
    else:
        error_msg = "❌ **No new videos found for this tag.**" if status == "no_new_media" or status == "no_posts" else "🚨 **Server connection error.**"
        bot.edit_message_text(error_msg, message.chat.id, waiting_msg.message_id, parse_mode="Markdown")


# ----------------- Keep Alive Layer -----------------
def start_bot_polling():
    print("🚀 Bot Polling Started...")
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
