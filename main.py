import os
import logging
from fastapi import FastAPI, Request, Response
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)
from yt_dlp import YoutubeDL
from dotenv import load_dotenv
import asyncio

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = FastAPI()
bot = Bot(token=TOKEN)

application = ApplicationBuilder().token(TOKEN).build()

# مقداردهی اولیه Application
@app.on_event("startup")
async def startup_event():
    await application.initialize()
    await application.start()

@app.on_event("shutdown")
async def shutdown_event():
    await application.stop()
    await application.shutdown()

ydl_opts = {
    'format': 'mp4/best',
    'outtmpl': '/tmp/%(id)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
    'ignoreerrors': True,
    'nocheckcertificate': True,
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! لینک اینستاگرام بفرست.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "instagram.com" not in url:
        await update.message.reply_text("لطفاً لینک معتبر اینستاگرام بفرست.")
        return

    msg = await update.message.reply_text("⏳ در حال دانلود...")
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                await msg.edit_text("❌ نتوانستم محتوایی پیدا کنم.")
                return

            filepath = ydl.prepare_filename(info)

        with open(filepath, "rb") as f:
            ext = info.get("ext", "").lower()
            if ext in ("mp4", "mkv", "webm"):
                await bot.send_video(chat_id=update.message.chat_id, video=f)
            else:
                await bot.send_photo(chat_id=update.message.chat_id, photo=f)

        os.remove(filepath)
        await msg.edit_text("✅ ارسال با موفقیت انجام شد!")

    except Exception as e:
        logger.error("Error:", exc_info=True)
        await msg.edit_text("❌ خطا رخ داد. لطفاً دوباره تلاش کن.")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

@app.post(f"/{TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot)
    await application.process_update(update)
    return Response(content="OK", status_code=200)

@app.get("/ping")
def ping():
    return {"status": "pong"}

@app.get("/")
def read_root():
    return {"message": "ربات تلگرام در حال اجراست!"}