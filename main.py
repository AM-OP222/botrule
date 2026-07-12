import io
import os
import random
import time
import requests
import telebot
import xml.etree.ElementTree as ET

# ----------------- تنظیمات ربات -----------------
BOT_TOKEN = "8802789901:AAG6JKnANWXy-bRVRxIWf7xBqYET8HxZOIU"

USER_ID = "6501593"
API_KEY = "7177a4499703fedb969488fc7d60d5d90dd7a6b95e84d1683e8f560228c877108a497988d74be4f506c00b410ab193d4da9d2474db8456e6398041fca4b81901"

session = requests.Session()
session.trust_env = True
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})
# -------------------------------------------------

bot = telebot.TeleBot(BOT_TOKEN)

def get_five_photo_files(tag):
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
        response = session.get(url, params=params, timeout=15)
        if response.status_code == 200:
            if "Missing authentication" in response.text:
                return None, "auth_error"
            if not response.text.strip():
                return None, "no_posts"
                
            root = ET.fromstring(response.text)
            posts = root.findall('post')

            if posts and len(posts) > 0:
                photo_urls = []
                for p in posts:
                    media_url = p.get("file_url")
                    if media_url:
                        ext = media_url.split(".")[-1].lower().split("?")[0]
                        if ext in ["jpg", "jpeg", "png", "bmp", "webp"]:
                            photo_urls.append(media_url)

                if photo_urls:
                    random.shuffle(photo_urls)
                    selected_urls = photo_urls[:5]
                    
                    downloaded_files = []
                    for index, img_url in enumerate(selected_urls):
                        print(f"📥 Downloading image {index+1}/5: {img_url}")
                        img_res = session.get(img_url, timeout=20)
                        if img_res.status_code == 200:
                            bio = io.BytesIO(img_res.content)
                            ext = img_url.split(".")[-1].lower().split("?")[0]
                            bio.name = f"photo_{index}.{ext}"
                            downloaded_files.append(bio)
                    
                    if downloaded_files:
                        return downloaded_files, "success"
                    else:
                        return None, "download_failed"
                else:
                    return None, "no_photos_found"
            else:
                return None, "no_posts"
    except Exception as e:
        print(f"🚨 API Error: {e}")
    return None, "error"


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    welcome_text = (
        "🔮 **به ربات عکس خوش آمدید!**\n\n"
        "دستور `/get` را همراه با تگ بفرستید تا ۵ عکس تصادفی برای شما ارسال شود.\n\n"
        "**مثال:**\n"
        "`/get madara uchiha`"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")


@bot.message_handler(commands=["get"])
def send_media(message):
    text_parts = message.text.split(" ", 1)

    if len(text_parts) < 2:
        bot.reply_to(message, "⚠️ لطفاً یک تگ بنویسید!\nمثال: `/get madara uchiha`", parse_mode="Markdown")
        return

    tag = text_parts[1].strip()
    waiting_msg = bot.reply_to(message, f"🔍 در حال دانلود ۵ عکس برای تگ #{tag}...")

    files_list, status = get_five_photo_files(tag)

    if files_list and status == "success":
        # پاک کردن پیام لودینگ قبل از شروع ارسال برای خلوت شدن چت
        bot.delete_message(message.chat.id, waiting_msg.message_id)
        
        success_count = 0
        for i, file_obj in enumerate(files_list):
            try:
                print(f"📤 Uploading image {i+1}/5 to Telegram...")
                caption_text = f"📸 تگ: #{tag} ({i+1}/5)"
                
                # ارسال تکی تصاویر برای جلوگیری از کرش فیلترشکن
                bot.send_photo(message.chat.id, file_obj, caption=caption_text, timeout=60)
                success_count += 1
                
                # ایجاد وقفه ۲ ثانیه‌ای بین هر ارسال تا پهنای باند فیلترشکن خالی شود
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error uploading image {i+1}: {e}")

        if success_count == 0:
            bot.send_message(message.chat.id, "❌ متاسفانه به دلیل ضعف شدید فیلترشکن هیچ‌کدام از عکس‌ها آپلود نشدند.")
    else:
        if status == "auth_error":
            error_text = "🚨 خطای سرور: کلید امنیتی API وارد شده نامعتبر است."
        elif status == "no_photos_found":
            error_text = f"❌ در نتایج این تگ، عکسی پیدا نشد."
        elif status == "no_posts":
            error_text = f"❌ چیزی برای تگ `{tag}` پیدا نشد."
        else:
            error_text = "❌ خطایی در دانلود فایل‌ها رخ داد."

        bot.edit_message_text(error_text, message.chat.id, waiting_msg.message_id, parse_mode="Markdown")


if __name__ == "__main__":
    print("🚀 ربات با سیستم آپلود تکی و ضد ارور صبوری فیلترشکن روشن شد...")
    bot.infinity_polling()
