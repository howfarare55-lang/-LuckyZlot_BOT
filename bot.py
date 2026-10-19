import os
import json
import urllib.request
import urllib.parse
import time

# Get token from Railway environment variables
TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    print("ERROR: BOT_TOKEN variable is not set in Railway!")
    exit(1)

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


def make_request(method, data=None):
    """Sends HTTP requests directly to the Telegram API"""
    url = f"{BASE_URL}/{method}"
    try:
        if data:
            payload = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(
                url, data=payload, headers={'Content-Type': 'application/json'}
            )
        else:
            req = urllib.request.Request(url)

        with urllib.request.urlopen(req, timeout=35) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"API Request Error ({method}): {e}")
        return None


def get_updates(offset=None):
    """Fetch unread messages from Telegram"""
    method = f"getUpdates?timeout=30" + (f"&offset={offset}" if offset else "")
    result = make_request(method)
    return result.get("result", []) if result else []


def send_welcome(chat_id):
    """Sends the main football interactive menu"""
    data = {
        "chat_id": chat_id,
        "text": (
            "⚽ *Welcome to Football Companion Bot!*\n\n"
            "Select an option below to view real-time scores, fixtures, and statistics:"
        ),
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "⚽ Live Scores", "callback_data": "live_scores"},
                    {"text": "📅 Fixtures", "callback_data": "fixtures"}
                ],
                [
                    {"text": "📊 Standings", "callback_data": "standings"},
                    {"text": "🔔 Goal Alerts", "callback_data": "alerts"}
                ]
            ]
        }
    }
    make_request("sendMessage", data)


def handle_callback(callback_query):
    """Handles interactive button presses from users"""
    query_id = callback_query["id"]
    chat_id = callback_query["message"]["chat"]["id"]
    message_id = callback_query["message"]["message_id"]
    data = callback_query["data"]

    # Stop button spinner on Telegram
    make_request("answerCallbackQuery", {"callback_query_id": query_id})

    if data == "live_scores":
        text = "🔴 *Live Football Scores*\n\n• Real Madrid 1 - 0 Barcelona (55')\n• Man City 2 - 1 Arsenal (78')\n\n_Updated live!_"
    elif data == "fixtures":
        text = "📅 *Upcoming Fixtures*\n\n• Chelsea vs Liverpool — 20:00 UTC\n• Bayern vs Dortmund — Tomorrow 17:30 UTC"
    elif data == "standings":
        text = "📊 *Premier League Top Standings*\n\n1. Arsenal - 48 pts\n2. Man City - 46 pts\n3. Liverpool - 43 pts"
    elif data == "alerts":
        text = "🔔 *Goal Alerts*\n\nYou are now subscribed to live goal notifications!"
    elif data == "main_menu":
        send_welcome(chat_id)
        return

    # Update existing message with selected content and add a back button
    update_data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "🔙 Back to Main Menu", "callback_data": "main_menu"}]
            ]
        }
    }
    make_request("editMessageText", update_data)


def main():
    print("Football Bot is active and polling for updates...")
    offset = None

    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1

            # Handle user commands (/start)
            if "message" in update and "text" in update["message"]:
                text = update["message"]["text"]
                chat_id = update["message"]["chat"]["id"]

                if text.startswith("/start"):
                    send_welcome(chat_id)
                else:
                    make_request("sendMessage", {
                        "chat_id": chat_id,
                        "text": "Send /start to view the football menu."
                    })

            # Handle button clicks
            elif "callback_query" in update:
                handle_callback(update["callback_query"])

        time.sleep(1)


if __name__ == "__main__":
    main()
