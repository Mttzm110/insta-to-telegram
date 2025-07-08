import os
import telebot
from yt_dlp import YoutubeDL
from flask import Flask, request

TOKEN = "602979258:AAFk4uz0m-PGm-xpr84whpGs7Dj-31neT6w"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

def download_media(url):
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        ext = info.get('ext', '')
    return filename, ext

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    if update.message and update.message.text:
        chat_id = update.message.chat.id
        text = update.message.text

        if "instagram.com" in text:
            try:
                file_path, ext = download_media(text)
                with open(file_path, 'rb') as f:
                    if ext in ['mp4', 'mkv', 'webm']:
                        bot.send_video(chat_id, f)
                    elif ext in ['jpg', 'jpeg', 'png', 'gif']:
                        bot.send_photo(chat_id, f)
                    else:
                        bot.send_message(chat_id, f"نوع فایل پشتیبانی نمی‌شود: {ext}")
                os.remove(file_path)
            except Exception as e:
                bot.send_message(chat_id, f"خطا در دانلود یا ارسال: {e}")
        else:
            bot.send_message(chat_id, "لطفا لینک اینستاگرام بفرست.")

    return "OK", 200

@app.route("/")
def index():
    return "ربات اینستا به تلگرام در حال اجراست."

if __name__ == "__main__":
    if not os.path.exists('downloads'):
        os.mkdir('downloads')
    app.run(host="0.0.0.0", port=5000)