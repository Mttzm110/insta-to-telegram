import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters
from yt_dlp import YoutubeDL
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
bot = Bot(TOKEN)
dp = Dispatcher(bot, None, workers=0, use_context=True)

ydl_opts = {
    'archive': False,
    'format': 'mp4',
    'outtmpl': '%(id)s.%(ext)s',
}

@dp.message_handler(filters.TEXT & (~filters.COMMAND))
def handle_message(update: Update, context):
    url = update.message.text.strip()
    if "instagram.com" not in url:
        update.message.reply_text("لطفاً یک لینک معتبر از اینستاگرام بفرستید.")
        return

    msg = update.message.reply_text("⏳ در حال دانلود...")
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)

        with open(filepath, "rb") as f:
            if info.get("ext") in ("mp4", "mkv", "webm"):
                bot.send_video(chat_id=update.message.chat_id, video=f)
            else:
                bot.send_photo(chat_id=update.message.chat_id, photo=f)

        os.remove(filepath)
        msg.edit_text("✅ دانلود و ارسال با موفقیت انجام شد!")
    except Exception as e:
        logging.exception(e)
        msg.edit_text("❌ مشکلی پیش اومد! مطمئن باش لینک صحیح باشه.")

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    dp.process_update(Update.de_json(request.get_json(force=True), bot))
    return "OK", 200

@app.route("/ping", methods=["GET"])
def ping():
    return "pong", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!", 200

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=PORT)