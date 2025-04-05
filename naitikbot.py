import os
import logging
from flask import Flask, request
import telebot
import yfinance as yf

# === Logging Setup ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Telegram Bot Token ===
TOKEN = "7663257272:AAHR20ai1-4WQme-GYzazQ9QjhVr4biOb3c"
bot = telebot.TeleBot(TOKEN)

# === Flask App Setup ===
app = Flask(__name__)

# === Telegram Bot Message Handler ===
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    symbol = message.text.strip().upper()
    logger.info(f"📩 Received message: {symbol} from user: {message.chat.id}")

    # Add suffix if missing
    if not (symbol.endswith(".NS") or symbol.endswith(".BO")):
        symbol += ".NS"

    try:
        df = yf.Ticker(symbol).history(period="1d")
        if df.empty:
            raise ValueError("No data found for that symbol.")
        price = df["Close"].iloc[-1]
        response = f"📈 *{symbol}*\nCurrent Price: ₹{price:.2f}"
        bot.reply_to(message, response, parse_mode="Markdown")
    except Exception as e:
        error_msg = f"⚠️ Error: {str(e)}"
        logger.error(error_msg)
        bot.reply_to(message, error_msg)

# === Flask Routes ===
@app.route('/')
def home():
    return "✅ Bot is Live!"

@app.route('/set_webhook')
def set_webhook():
    webhook_url = f"https://naitikbot.onrender.com/{TOKEN}"
    bot.remove_webhook()
    success = bot.set_webhook(url=webhook_url)
    logger.info(f"🔗 Webhook set: {success} to {webhook_url}")
    return f"Webhook set: {success}"

@app.route(f"/{TOKEN}", methods=['POST'])
def receive_update():
    try:
        json_str = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        logger.info("✅ Update processed")
    except Exception as e:
        logger.error(f"❌ Webhook processing error: {e}")
    return "OK", 200

# === Run the App ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Starting app on port {port}")
    app.run(host="0.0.0.0", port=port)
