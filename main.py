import os
import logging
from flask import Flask, request, Response
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)
from yt_dlp import YoutubeDL
from dotenv import load_dotenv
import asyncio

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = Bot(token=TOKEN)

# ساخت Application
application = ApplicationBuilder().token(TOKEN).build()

# مقداردهی اولیه Application (یک بار در شروع برنامه)
async def initialize_app():
    await application.initialize()
    await application.start()

asyncio.run(initialize_app())

# گزینه‌های yt-dlp برای دانلود ویدیو/عکس
ydl_opts = {
    'format': 'mp4/best',
    'outtmpl': '/tmp/%(id)s.%(ext)s',  # ذخیره در مسیر موقت برای محیط‌های کلود
    'quiet': True,
    'no_warnings': True,
    'ignoreerrors': True,
    'nocheckcertificate': True,
}

# هندلر دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! لینک اینستاگرام ارسال کن، من عکس یا ویدیو رو برات می‌فرستم."
    )

# هندلر دریافت پیام (لینک اینستاگرام)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "instagram.com" not in url:
        await update.message.reply_text("لطفاً فقط لینک‌های معتبر اینستاگرام ارسال کن.")
        return

    msg = await update.message.reply_text("⏳ در حال دانلود و آماده‌سازی...")

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                await msg.edit_text("❌ نتوانستم محتوایی برای این لینک پیدا کنم.")
                return

            filepath = ydl.prepare_filename(info)

        with open(filepath, "rb") as media_file:
            # تشخیص نوع محتوا و ارسال مناسب
            ext = info.get('ext', '').lower()
            if ext in ('mp4', 'mkv', 'webm'):
                await bot.send_video(chat_id=update.message.chat_id, video=media_file)
            else:
                await bot.send_photo(chat_id=update.message.chat_id, photo=media_file)

        os.remove(filepath)
        await msg.edit_text("✅ کار با موفقیت انجام شد!")

    except Exception as e:
        logger.error("خطا در دانلود یا ارسال محتوا:", exc_info=True)
        await msg.edit_text(
            "❌ خطایی رخ داد. مطمئن شو لینک اینستاگرام درست باشه و دوباره تلاش کن."
        )

# ثبت هندلرها
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

# ایجاد یک event loop اختصاصی برای webhook
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# مسیر webhook (مطابق توکن)
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    try:
        loop.run_until_complete(application.process_update(update))
    except Exception as e:
        logger.error(f"خطا در پردازش آپدیت: {e}", exc_info=True)
    return Response("OK", status=200)

# مسیر برای Ping (آپتایم ربات)
@app.route("/ping", methods=["GET"])
def ping():
    return Response("pong", status=200)

# مسیر روت برای چک کردن وضعیت سرور
@app.route("/", methods=["GET"])
def home():
    return Response("ربات تلگرام در حال اجراست!", status=200)

# توجه: نیازی به اجرای سرور داخل main.py نیست، gunicorn آن را انجام می‌دهد