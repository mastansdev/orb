import os
import time

from dotenv import load_dotenv

from notifications.telegram_notifier import TelegramNotifier

load_dotenv()

telegram = TelegramNotifier(
    os.getenv("TELEGRAM_BOT_TOKEN"),
    os.getenv("TELEGRAM_CHAT_ID")
)

telegram.send(
    "🧪 ORB Telegram Diagnostic Test"
)

print("Waiting 10 seconds...")

time.sleep(10)

print("Test Finished")