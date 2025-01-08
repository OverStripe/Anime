import telegram
from telegram.ext import Updater, CommandHandler, JobQueue
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from PIL import Image, ImageDraw, ImageFont
import requests
import random
import os

# Your bot token from BotFather
BOT_TOKEN = '7881791180:AAHiz6A3NDwwkdhlPNwxoWu1L0kgkJOIMSU'

# Default fallback quote
DEFAULT_QUOTE = "\"Stay positive, work hard, and make it happen.\""

# Font configuration
FONT_PATH = "arial.ttf"  # Ensure this font file exists in the script directory
FONT_SIZE = 24

# Sticker output path
STICKER_FILE = "quote_sticker.webp"

# Set to track subscribed users
SUBSCRIBED_USERS = set()

# ------------------------------
# Quote Fetching Functions
# ------------------------------

def get_quote_from_quotable():
    """Fetch a random quote from Quotable API."""
    try:
        response = requests.get("https://api.quotable.io/random", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return f"\"{data['content']}\""
    except (requests.exceptions.RequestException, KeyError) as e:
        print(f"Quotable API Error: {e}")
    return None

def get_quote_from_zenquotes():
    """Fetch a random quote from ZenQuotes API."""
    try:
        response = requests.get("https://zenquotes.io/api/random", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return f"\"{data[0]['q']}\""
    except (requests.exceptions.RequestException, KeyError) as e:
        print(f"ZenQuotes API Error: {e}")
    return None

def get_random_quote():
    """Get a random quote with fallback."""
    quote = get_quote_from_quotable()
    if quote:
        return quote
    
    quote = get_quote_from_zenquotes()
    if quote:
        return quote
    
    return DEFAULT_QUOTE

# ------------------------------
# Multi-Color Gradient Background
# ------------------------------

def generate_multicolor_gradient():
    """Generate a multi-color gradient background."""
    try:
        img = Image.new('RGBA', (512, 512), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Generate 3 random gradient colors
        colors = [
            tuple(random.randint(180, 255) for _ in range(3)),
            tuple(random.randint(150, 255) for _ in range(3)),
            tuple(random.randint(200, 255) for _ in range(3))
        ]
        
        for y in range(512):
            ratio1 = y / 512
            ratio2 = 1 - ratio1
            r = int(colors[0][0] * ratio2 + colors[1][0] * ratio1)
            g = int(colors[0][1] * ratio2 + colors[1][1] * ratio1)
            b = int(colors[0][2] * ratio2 + colors[1][2] * ratio1)
            draw.line([(0, y), (512, y)], fill=(r, g, b))
        
        # Diagonal blend
        for x in range(512):
            ratio1 = x / 512
            ratio2 = 1 - ratio1
            r = int(colors[1][0] * ratio2 + colors[2][0] * ratio1)
            g = int(colors[1][1] * ratio2 + colors[2][1] * ratio1)
            b = int(colors[1][2] * ratio2 + colors[2][2] * ratio1)
            draw.line([(x, 0), (x, 512)], fill=(r, g, b), width=1)
        
        return img
    except Exception as e:
        print(f"Gradient Generation Error: {e}")
        return Image.new('RGBA', (512, 512), (255, 255, 255, 255))

# ------------------------------
# Sticker Generation
# ------------------------------

def generate_sticker(quote):
    """Generate a sticker image with a quote."""
    try:
        # Generate multi-color gradient background
        img = generate_multicolor_gradient()
        draw = ImageDraw.Draw(img)
        
        # Load font
        try:
            font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        except:
            font = ImageFont.load_default()
        
        # Text wrapping
        lines = []
        words = quote.split()
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if draw.textlength(test_line, font=font) < 450:
                line = test_line
            else:
                lines.append(line)
                line = word
        lines.append(line)
        
        # Draw text on the image
        y = 180
        for line in lines:
            draw.text((30, y), line, font=font, fill=(0, 0, 0))
            y += 40
        
        # Save as WEBP
        img.save(STICKER_FILE, "WEBP")
    except Exception as e:
        print(f"Sticker Generation Error: {e}")

# ------------------------------
# Bot Command Handlers
# ------------------------------

def start(update, context):
    update.message.reply_text(
        "🎉 Welcome to the Quote Bot!\n\nUse /subscribe to receive hourly quotes as stickers.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Dev", url="https://t.me/Philowise")]
        ])
    )

def subscribe(update, context):
    SUBSCRIBED_USERS.add(update.message.chat_id)
    update.message.reply_text("✅ Subscribed to hourly quote stickers!")

def unsubscribe(update, context):
    SUBSCRIBED_USERS.discard(update.message.chat_id)
    update.message.reply_text("❌ Unsubscribed from hourly quote stickers.")

def send_hourly_quote(context):
    for chat_id in SUBSCRIBED_USERS:
        quote = get_random_quote()
        generate_sticker(quote)
        context.bot.send_sticker(chat_id=chat_id, sticker=open(STICKER_FILE, 'rb'))

# ------------------------------
# Main Bot Function
# ------------------------------

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("subscribe", subscribe))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe))
    updater.job_queue.run_repeating(send_hourly_quote, interval=3600, first=0)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
          
