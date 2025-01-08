import logging
import requests
import random
import os
from PIL import Image, ImageDraw, ImageFont
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    JobQueue,
)

# ------------------------------
# Configuration
# ------------------------------

BOT_TOKEN = '7881791180:AAHiz6A3NDwwkdhlPNwxoWu1L0kgkJOIMSU'
DEFAULT_QUOTE = "\"Stay positive, work hard, and make it happen.\""
FONT_PATH = "arial.ttf"
FONT_SIZE = 24
STICKER_FILE = "quote_sticker.webp"
SUBSCRIBED_USERS = set()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------------------------
# Quote Fetching Functions
# ------------------------------

async def get_quote_from_quotable():
    """Fetch a random quote from Quotable API."""
    try:
        response = requests.get("https://api.quotable.io/random", timeout=5)
        response.raise_for_status()
        return f"\"{response.json()['content']}\""
    except Exception as e:
        logger.error(f"Quotable API Error: {e}")
    return None


async def get_quote_from_zenquotes():
    """Fetch a random quote from ZenQuotes API."""
    try:
        response = requests.get("https://zenquotes.io/api/random", timeout=5)
        response.raise_for_status()
        return f"\"{response.json()[0]['q']}\""
    except Exception as e:
        logger.error(f"ZenQuotes API Error: {e}")
    return None


async def get_random_quote():
    """Get a random quote with fallback."""
    quote = await get_quote_from_quotable()
    if quote:
        return quote

    quote = await get_quote_from_zenquotes()
    if quote:
        return quote

    return DEFAULT_QUOTE

# ------------------------------
# Sticker Generation Functions
# ------------------------------

def generate_multicolor_gradient():
    """Generate a random multi-color gradient background."""
    try:
        img = Image.new('RGBA', (512, 512), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Generate gradient colors
        colors = [
            tuple(random.randint(150, 255) for _ in range(3)),
            tuple(random.randint(200, 255) for _ in range(3)),
            tuple(random.randint(180, 255) for _ in range(3))
        ]

        # Vertical Gradient
        for y in range(512):
            ratio = y / 512
            r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
            g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
            b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
            draw.line([(0, y), (512, y)], fill=(r, g, b))

        # Diagonal Blend
        for x in range(512):
            ratio = x / 512
            r = int(colors[1][0] * (1 - ratio) + colors[2][0] * ratio)
            g = int(colors[1][1] * (1 - ratio) + colors[2][1] * ratio)
            b = int(colors[1][2] * (1 - ratio) + colors[2][2] * ratio)
            draw.line([(x, 0), (x, 512)], fill=(r, g, b), width=1)

        return img
    except Exception as e:
        logger.error(f"Gradient Generation Error: {e}")
        return Image.new('RGBA', (512, 512), (255, 255, 255, 255))


def generate_sticker(quote):
    """Generate a sticker with a multi-color gradient background."""
    try:
        img = generate_multicolor_gradient()
        draw = ImageDraw.Draw(img)

        font = ImageFont.truetype(FONT_PATH, FONT_SIZE) if os.path.exists(FONT_PATH) else ImageFont.load_default()

        y = 180
        for line in quote.split('. '):
            draw.text((30, y), line, font=font, fill=(0, 0, 0))
            y += 40

        img.save(STICKER_FILE, "WEBP")
    except Exception as e:
        logger.error(f"Sticker Generation Error: {e}")

# ------------------------------
# Bot Handlers
# ------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎉 Welcome to StickerSage!\nUse /subscribe to receive hourly quote stickers.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Dev", url="https://t.me/Philowise")]
        ])
    )

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    SUBSCRIBED_USERS.add(update.message.chat_id)
    await update.message.reply_text("✅ Subscribed to hourly quote stickers!")

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    SUBSCRIBED_USERS.discard(update.message.chat_id)
    await update.message.reply_text("❌ Unsubscribed from hourly quote stickers.")

async def send_hourly_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in SUBSCRIBED_USERS:
        quote = await get_random_quote()
        generate_sticker(quote)
        await context.bot.send_sticker(chat_id=chat_id, sticker=open(STICKER_FILE, 'rb'))

# ------------------------------
# Main Function
# ------------------------------

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))

    application.job_queue.run_repeating(send_hourly_quote, interval=3600, first=0)

    application.run_polling()

if __name__ == '__main__':
    main()
