import os
from flask import Flask, request
import telebot
import yfinance as yf

TOKEN = "7663257272:AAHR20ai1-4WQme-GYzazQ9QjhVr4biOb3c"
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# Bot reply logic
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    symbol = message.text.strip().upper()
    if not (symbol.endswith(".NS") or symbol.endswith(".BO")):
        symbol += ".NS"

    try:
        data = yf.Ticker(symbol).history(period='1d')
        price = data['Close'].iloc[-1]
        bot.reply_to(message, f"📈 {symbol}\nCurrent Price: ₹{price:.2f}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

# Routes
@app.route("/")
def index():
    return "Bot is running!"

@app.route("/set_webhook")
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"https://naitikbot.onrender.com/{TOKEN}")
    return "Webhook set!"

@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
