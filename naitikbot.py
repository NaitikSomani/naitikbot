from flask import Flask, request
import telebot
import yfinance as yf
import pandas as pd
import io
import mplfinance as mpf
import matplotlib.dates as mdates
import os

TOKEN = "7663257272:AAHR20ai1-4WQme-GYzazQ9QjhVr4biOb3c"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Compute indicators, generate chart and analysis (same as you wrote)
# Just reuse your `compute_indicators()`, `get_stock_data()`, `generate_chart()`, etc. here

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    symbol = message.text.strip().upper()
    if not (symbol.endswith(".NS") or symbol.endswith(".BO")):
        symbol = f"{symbol}.NS"
    try:
        df = get_stock_data(symbol)
        chart = generate_chart(symbol, df)
        summary = generate_analysis(symbol, df)
        bot.send_photo(message.chat.id, chart, caption=summary)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

@app.route('/')
def index():
    return "Bot is running!"

@app.route('/set_webhook')
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"https://naitikbot.onrender.com/{TOKEN}")
    return "Webhook set successfully!"

@app.route(f"/{TOKEN}", methods=['POST'])
def receive_update():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
