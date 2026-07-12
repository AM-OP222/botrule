import io
import os
import random
import time
from threading import Thread
import requests
import telebot
import xml.etree.ElementTree as ET


# ----------------- تنظیمات ربات با توکن‌های شما -----------------
BOT_TOKEN = "8969280684:AAF2C5mhjg5Am1S5trwxj75cM8ahgt6Hogg"
USER_ID = "6501593"
API_KEY = "7177a4499703fedb969488fc7d60d5d90dd7a6b95e84d1683e8f560228c877108a497988d74be4f506c00b410ab193d4da9d2474db8456e6398041fca4b81901"

session = requests.Session()
session.trust_env = True
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

# 🛠️ فعال‌سازی مولتی‌ثرد برای جلوگیری از فریز شدن ربات
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# ----------------- توابع کمکی دریافت مدیا -----------------
def fetch_media_from_api(tag, mode="pic"):
    url = "https://api.rule34.xxx/index.php"
    processed_tag = tag.lower().strip().replace(" ", "_")
    
    params = {
        "page": "dapi",
        "s": "post",
        "q": "index",
        "tags": processed_tag,
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
                urls = []
                for p in posts:
                    media_url = p.get("file_url")
                    if media_url:
                        ext = media_url.split(".")[-1].lower().split("?")[0]
                        if mode == "pic" and ext in ["jpg", "jpeg", "png", "bmp", "webp"]:
                            urls.append(media_url)
                        elif mode == "vid" and ext in ["mp4", "webm"]:
                            urls.append(media_url)

                if urls:
                    random.shuffle(urls)
                    return urls, "success"
                else:
                    return None, "no_media_found"
            else:
                return None, "no_posts"
    except Exception as e:
        print(f"🚨 API Error: {e}")
    return None, "error"

# ----------------- هندلرهای ربات تلگرام -----------------

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    welcome_text = (
        "🔮 **به ربات پیشرفته تصاویر و ویدیو خوش آمدید!**\n\n"
        "دستورات فعال ربات:\n"
        "📸 دریافت ۵ عکس تصادفی:\n"
        "`/pic34 madara uchiha`\n\n"
        "🎬 دریافت ۱ ویدیو تصادفی:\n"
        "`/vid34 madara uchiha`"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")


# 📸 بخش اول: هندلر ارسال عکس پنج تایی
@bot.message_handler(commands=["pic34"])
def send_pictures(message):
    text_parts = message.text.split(" ", 1)

    if len(text_parts) < 2:
        bot.reply_to(message, "⚠️ لطفاً یک تگ بنویسید!\nمثال: `/pic34 madara uchiha`", parse_mode="Markdown")
        return

    tag = text_parts[1].strip()
    waiting_msg = bot.reply_to(message, f"🔍 در حال دانلود ۵ عکس تصادفی برای #{tag}...")

    urls_list, status = fetch_media_from_api(tag, mode="pic")

    if urls_list and status == "success":
        selected_urls = urls_list[:10] # ۱۰ تا زاپاس
        downloaded_files = []
        
        for img_url in selected_urls:
            if len(downloaded_files) >= 5:
                break
            try:
                img_res = session.get(img_url, timeout=7)
                if img_res.status_code == 200:
                    bio = io.BytesIO(img_res.content)
                    ext = img_url.split(".")[-1].lower().split("?")[0]
                    bio.name = f"photo_{len(downloaded_files)}.{ext}"
                    downloaded_files.append(bio)
            except:
                continue

        if downloaded_files:
            try:
                bot.delete_message(message.chat.id, waiting_msg.message_id)
            except:
                pass
                
            success_count = 0
            for i, file_obj in enumerate(downloaded_files):
                try:
                    caption_text = f"📸 تگ: #{tag} ({i+1}/{len(downloaded_files)})"
                    bot.send_photo(message.chat.id, file_obj, caption=caption_text, timeout=45)
                    success_count += 1
                    time.sleep(1.5)
                except Exception as e:
                    print(f"❌ Error uploading picture {i+1}: {e}")
            
            if success_count == 0:
                bot.send_message(message.chat.id, "❌ خطایی در آپلود تصاویر به تلگرام رخ داد.")
        else:
            bot.edit_message_text("❌ خطایی در دانلود فایل‌های تصویری از سرور اصلی رخ داد.", message.chat.id, waiting_msg.message_id)
    else:
        error_msg = f"❌ چیزی پیدا نشد." if status == "no_media_found" or status == "no_posts" else "🚨 خطایی در ارتباط با سرور رخ داد."
        bot.edit_message_text(error_msg, message.chat.id, waiting_msg.message_id)


# 🎬 بخش دوم: هندلر ارسال تک ویدیو
@bot.message_handler(commands=["vid34"])
def send_video(message):
    text_parts = message.text.split(" ", 1)

    if len(text_parts) < 2:
        bot.reply_to(message, "⚠️ لطفاً یک تگ بنویسید!\nمثال: `/vid34 madara uchiha`", parse_mode="Markdown")
        return

    tag = text_parts[1].strip()
    waiting_msg = bot.reply_to(message, f"🔍 در حال جستجو و دانلود ویدیو برای #{tag}...\n(ویدیوها زمان بیشتری برای دانلود نیاز دارند)")

    urls_list, status = fetch_media_from_api(tag, mode="vid")

    if urls_list and status == "success":
        video_file = None
        video_caption = f"🎬 ویدیو تصادفی تگ: #{tag}"
        
        for vid_url in urls_list[:5]:
            try:
                vid_res = session.get(vid_url, timeout=35)
                if vid_res.status_code == 200:
                    video_file = io.BytesIO(vid_res.content)
                    ext = vid_url.split(".")[-1].lower().split("?")[0]
                    video_file.name = f"video.{ext}"
                    break
            except:
                continue

        if video_file:
            try:
                bot.delete_message(message.chat.id, waiting_msg.message_id)
                print(f"📤 Uploading video to Telegram...")
                bot.send_video(message.chat.id, video_file, caption=video_caption, timeout=90)
            except Exception as e:
                print(f"❌ Error uploading video: {e}")
                bot.send_message(message.chat.id, "❌ ویدیو دانلود شد اما آپلود آن به تلگرام ناموفق بود (احتمالاً حجم آن بالای ۵۰ مگابایت است).")
        else:
            bot.edit_message_text("❌ موفق به دانلود ویدیوهای پیدا شده نشدیم (احتمالاً حجم ویدیوها بسیار بالاست).", message.chat.id, waiting_msg.message_id)
    else:
        error_msg = f"❌ هیچ ویدیویی برای تگ #{tag} پیدا نشد!" if status == "no_media_found" or status == "no_posts" else "🚨 خطایی در ارتباط با سرور رخ داد."
        bot.edit_message_text(error_msg, message.chat.id, waiting_msg.message_id)


if __name__ == "__main__":
    # ۱. استارت سرور Flask در بک‌گراند برای اتصال به cron-job.org
    t = Thread(target=run_flask)
    t.start()
    
    # ۲. استارت ربات تلگرام
    print("🚀 ربات مالتی‌ثرد تصاویر و ویدیو به همراه سرور Flask روشن شد...")
    bot.infinity_polling()
