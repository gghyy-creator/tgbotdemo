import os
import json
import urllib.request
from http.server import BaseHTTPRequestHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")


def telegram(method, data):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read())


def send_message(chat_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if keyboard:
        data["reply_markup"] = keyboard

    return telegram("sendMessage", data)


def handle_message(message):
    chat_id = message["chat"]["id"]
    user = message.get("from", {})
    first_name = user.get("first_name", "Friend")
    text = message.get("text", "").strip()

    if text.startswith("/start"):
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "👤 My ID", "callback_data": "my_id"},
                    {"text": "ℹ️ Help", "callback_data": "help"}
                ]
            ]
        }

        send_message(
            chat_id,
            f"👋 Hello <b>{first_name}</b>!\n\n"
            "Welcome to my Python Telegram bot.\n\n"
            "Choose an option below!",
            keyboard
        )

    elif text.startswith("/help"):
        send_message(
            chat_id,
            "📚 <b>Available Commands</b>\n\n"
            "/start - Start the bot\n"
            "/help - Show help\n"
            "/id - Get your Telegram ID"
        )

    elif text.startswith("/id"):
        send_message(
            chat_id,
            f"🆔 Your Telegram ID:\n<code>{chat_id}</code>"
        )

    elif text:
        send_message(
            chat_id,
            f"💬 You said: {text}\n\n"
            "I'm a Python bot. Send /help to see my commands."
        )


def handle_callback(callback):
    chat_id = callback["message"]["chat"]["id"]
    message_id = callback["message"]["message_id"]
    data = callback.get("data")

    telegram("answerCallbackQuery", {
        "callback_query_id": callback["id"]
    })

    if data == "my_id":
        send_message(
            chat_id,
            f"🆔 Your Telegram ID: <code>{chat_id}</code>"
        )

    elif data == "help":
        send_message(
            chat_id,
            "📚 Commands:\n\n"
            "/start - Start\n"
            "/help - Help\n"
            "/id - Your ID"
        )


class handler(BaseHTTPRequestHandler):

    def respond(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        self.respond(200, {
            "status": "online",
            "message": "Telegram bot is running!"
        })

    def do_POST(self):

        if not BOT_TOKEN or not WEBHOOK_SECRET:
            self.respond(500, {"error": "Missing environment variables"})
            return

        secret = self.headers.get(
            "X-Telegram-Bot-Api-Secret-Token"
        )

        if secret != WEBHOOK_SECRET:
            self.respond(403, {"error": "Unauthorized"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            update = json.loads(self.rfile.read(length))

            if "message" in update:
                handle_message(update["message"])

            elif "callback_query" in update:
                handle_callback(update["callback_query"])

            self.respond(200, {"ok": True})

        except Exception as error:
            print("Bot error:", error)
            self.respond(200, {"ok": False})
