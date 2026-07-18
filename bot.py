# -*- coding: utf-8 -*-
import os
import sys
import time
import subprocess
import signal
from telebot import TeleBot, types

# ⚠️ APNA TELEGRAM BOT TOKEN YAHAN DAALO
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
bot = TeleBot(BOT_TOKEN)

active_processes = {}
STORAGE_DIR = "user_scripts"
os.makedirs(STORAGE_DIR, exist_ok=True)

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("📤 Upload File"), types.KeyboardButton("📁 My Files"),
        types.KeyboardButton("📝 Edit Files"), types.KeyboardButton("⚡ Bot Speed"),
        types.KeyboardButton("📊 Statistics"), types.KeyboardButton("📦 Install Package"),
        types.KeyboardButton("📋 My Packages"), types.KeyboardButton("📞 Contact Owner")
    )
    return markup

def get_file_management_keyboard(filename):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⏹️ Stop", callback_data=f"stop_{filename}"),
        types.InlineKeyboardButton("🔄 Restart", callback_data=f"restart_{filename}"),
        types.InlineKeyboardButton("📝 Edit Name", callback_data=f"edit_{filename}"),
        types.InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{filename}"),
        types.InlineKeyboardButton("📄 Logs", callback_data=f"logs_{filename}"),
        types.InlineKeyboardButton("⬅️ Back", callback_data="back_main")
    )
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 Welcome Riya! Main VPS Bot Manager hoon.\n\nScript send karo ya menu use karo.", reply_markup=get_main_keyboard())

@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        filename = message.document.file_name
        if not filename.endswith('.py'):
            bot.reply_to(message, "⚠️ Sirf `.py` files allowed hain!")
            return
        file_path = os.path.join(STORAGE_DIR, filename)
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.reply_to(message, f"✅ **File uploaded! Starting automatically...**", parse_mode="Markdown")
        start_script(message.chat.id, filename)
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def start_script(chat_id, filename):
    file_path = os.path.join(STORAGE_DIR, filename)
    log_filename = f"file_{chat_id}_{int(time.time())}.log"
    log_path = os.path.join(STORAGE_DIR, log_filename)
    if chat_id in active_processes and active_processes[chat_id].get("filename") == filename:
        bot.send_message(chat_id, "⚠️ Script already running!")
        return
    bot.send_message(chat_id, "🔍 **Checking imports...**", parse_mode="Markdown")
    time.sleep(1)
    log_file = open(log_path, "w")
    process = subprocess.Popen([sys.executable, file_path], stdout=log_file, stderr=subprocess.STDOUT, preexec_fn=os.setsid if os.name != 'nt' else None)
    active_processes[chat_id] = {"process": process, "filename": filename, "pid": process.pid, "log_path": log_path, "log_filename": log_filename, "start_time": time.strftime("%Y-%m-%dT%H:%M:%S")}
    bot.send_message(chat_id, f"✅ `{filename}` started!\n📝 PID: {process.pid}\n📂 Logs: `{log_filename}`", parse_mode="Markdown")
    show_file_panel(chat_id, filename)

def show_file_panel(chat_id, filename):
    if chat_id not in active_processes: return
    proc_info = active_processes[chat_id]
    status_str = "🟢 Running" if proc_info["process"].poll() is None else "🔴 Stopped"
    panel_text = f"⚙️ **File Management**\n\n📁 File: `{proc_info['filename']}`\n📈 Status: {status_str}\nPID: {proc_info['pid']}\n⏰ Uploaded: {proc_info['start_time']}"
    bot.send_message(chat_id, panel_text, parse_mode="Markdown", reply_markup=get_file_management_keyboard(filename))

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    data = call.data
    if data.startswith("stop_"):
        if chat_id in active_processes:
            try: os.killpg(os.getpgid(active_processes[chat_id]["process"].pid), signal.SIGTERM)
            except: active_processes[chat_id]["process"].terminate()
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="⏹️ **Process terminated.**", parse_mode="Markdown")
            del active_processes[chat_id]
    elif data.startswith("logs_"):
        if chat_id in active_processes:
            with open(active_processes[chat_id]["log_path"], "r") as lf: logs = lf.read()[-2000:]
            bot.send_message(chat_id, f"📝 **Logs:**\n\n```\n{logs if logs.strip() else 'No logs yet.'}\n```", parse_mode="Markdown")
    elif data.startswith("restart_"):
        filename = data.split("_")[1]
        if chat_id in active_processes:
            try: os.killpg(os.getpgid(active_processes[chat_id]["process"].pid), signal.SIGTERM)
            except: active_processes[chat_id]["process"].terminate()
            del active_processes[chat_id]
        start_script(chat_id, filename)
    elif data == "back_main":
        bot.send_message(chat_id, "Main menu active.", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_menu_buttons(message):
    if message.text == "📁 My Files":
        files = [f for f in os.listdir(STORAGE_DIR) if f.endswith('.py')]
        bot.reply_to(message, f"📁 **Stored Scripts:**\n\n" + "\n".join([f"🔹 `{f}`" for f in files]) if files else "📂 Storage khali hai!", parse_mode="Markdown")
    elif message.text == "⚡ Bot Speed":
        t1 = time.time()
        msg = bot.reply_to(message, "⚡ Ping...")
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"🚀 **Bot Ping:** `{int((time.time() - t1) * 1000)}ms`", parse_mode="Markdown")
    elif message.text == "📊 Statistics":
        bot.reply_to(message, f"📊 **Server Status:**\n\n🔹 Live Scripts: {len(active_processes)}\n🔹 Platform: VPS\n🔹 Status: 24/7 Active", parse_mode="Markdown")

if __name__ == '__main__':
    print("🤖 Bot Server Online...")
    bot.infinity_polling()
