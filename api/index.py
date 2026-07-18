import os
import telebot
from flask import Flask, request

TOKEN = "8528439651:AAG21xs7Zyhp-jK3fM2ZDLJURV3JqWCqqmI"
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Invalid Request', 403

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Rιყα_ϝϝ_BOT is Live on Vercel! 🚀\nLevel: 2 | Season: 0")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"You said: {message.text}")

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    # Vercel URL variable automatic catch karega ya manual set kar sakte hain
    domain = request.host_url.replace("http://", "https://")
    s = bot.set_webhook(url=domain)
    if s:
        return f"Webhook setup successful on {domain}", 200
    else:
        return "Webhook setup failed", 500
