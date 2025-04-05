import os
from flask import Flask, request
import telebot

TOKEN = "7663257272:AAHR20ai1-4WQme-GYzazQ9QjhVr4biOb3c"
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# ✅ Just one handler
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    print(f"➡️ Received from {message.chat.id}: {message.text}")
    bot.reply_to(message, f"🔁 You said: {message.text}")

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/set_webhook')
def set_webhook():
    webhook_url = f"https://naitikbot.onrender.com/{TOKEN}"
    bot.remove_webhook()
    success = bot.set_webhook(url=webhook_url)
    return f"Webhook set: {success}"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
