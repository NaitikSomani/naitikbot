import os
from flask import Flask, request
import telebot

# Telegram Bot Token
TOKEN = "7663257272:AAHR20ai1-4WQme-GYzazQ9QjhVr4biOb3c"
bot = telebot.TeleBot(TOKEN)

# Flask App
app = Flask(__name__)

# Telegram Webhook Route
@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
    return "OK", 200

# Home Route
@app.route("/")
def index():
    return "Bot is up!"

# Webhook Setup Route
@app.route("/set_webhook")
def set_webhook():
    webhook_url = f"https://naitikbot.onrender.com/{TOKEN}"
    bot.remove_webhook()
    success = bot.set_webhook(url=webhook_url)
    return f"Webhook set: {success}"

# Message Handler
@bot.message_handler(func=lambda message: True)
def echo(message):
    print(f"➡️ Received: {message.text}")
    bot.reply_to(message, f"🔁 You said: {message.text}")

# Run Flask App
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
