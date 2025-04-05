import os
from flask import Flask, request
import telebot
import yfinance as yf

# === Your Bot Token ===
TOKEN = "7663257272:AAHR20ai1-4WQme-GYzazQ9QjhVr4biOb3c"
bot = telebot.TeleBot(TOKEN)

# === Flask App ===
app = Flask(__name__)

# === Telegram Message Handler ===
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        print(f"✅ Received message: {message.text}")  # Log incoming messages

        symbol = message.text.strip().upper()
        if not (symbol.endswith(".NS") or symbol.endswith(".BO")):
            symbol += ".NS"

        df = yf.Ticker(symbol).history(period="1d")
        if df.empty:
            bot.reply_to(message, f"⚠️ No data found for {symbol}")
            return

        price = df["Close"].iloc[-1]
        bot.reply_to(message, f"📈 *{symbol}*\nCurrent Price: ₹{price:.2f}", parse_mode="Markdown")

    except Exception as e:
        print("❌ Error:", e)
        bot.reply_to(message, f"❌ Error: {e}")

# === Web Routes ===
@app.route('/')
def home():
    return "Bot is running!"

@app.route('/set_webhook')
def set_webhook():
    webhook_url = f"https://naitikbot.onrender.com/{TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    return f"Webhook set to {webhook_url}"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_data = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_data)
    bot.process_new_updates([update])
    return "OK", 200

# === Start Flask App ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
