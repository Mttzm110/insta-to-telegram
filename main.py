import os
import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
bot = Bot(token=TOKEN)

application = ApplicationBuilder().token(TOKEN).build()

ydl_opts = {
    'format': 'mp4',
    'outtmpl': '/tmp/%(id)s.%(ext)s',  # ذخیره تو /tmp برای جلوگیری از مشکل دسترسی نوشتن
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! لینک اینستاگرام بفرست تا عکس یا ویدیو رو برات ارسال کنم.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "instagram.com" not in url:
        await update.message.reply_text("لطفاً یک لینک معتبر از اینستاگرام بفرستید.")
        return

    msg = await update.message.reply_text("⏳ در حال دانلود...")
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)

        with open(filepath, "rb") as f:
            if info.get("ext") in ("mp4", "mkv", "webm"):
                await bot.send_video(chat_id=update.message.chat_id, video=f)
            else:
                await bot.send_photo(chat_id=update.message.chat_id, photo=f)

        os.remove(filepath)
        await msg.edit_text("✅ دانلود و ارسال با موفقیت انجام شد!")
    except Exception as e:
        logging.exception(e)
        await msg.edit_text("❌ مشکلی پیش اومد! مطمئن باش لینک صحیح باشه.")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    import asyncio
    try:
        asyncio.run(application.process_update(update))
    except Exception as e:
        logging.error(f"Error processing update: {e}", exc_info=True)
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