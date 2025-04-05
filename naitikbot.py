import os
from flask import Flask, request
import telebot

# Your bot token
TOKEN = "7663257272:AAHR20ai1-4WQme-GYzazQ9QjhVr4biOb3c"
bot = telebot.TeleBot(TOKEN)

# Flask app
app = Flask(__name__)

# Message handler
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    print(f"➡️ Received: {message.text}")
    bot.reply_to(message, f"🔁 You said: {message.text}")

# Home route
@app.route('/')
def home():
    return "Bot is live!"

# Webhook setter
@app.route('/set_webhook')
def set_webhook():
    webhook_url = f"https://naitikbot.onrender.com/{TOKEN}"
    bot.remove_webhook()
    success = bot.set_webhook(url=webhook_url)
    return f"Webhook set: {success}"

# Webhook endpoint (Telegram will post here)
@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

# Run Flask app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
