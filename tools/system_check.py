import os
import sys
import socket
from dotenv import load_dotenv

load_dotenv()


def check(name, condition):

    status = "✓ PASS" if condition else "✗ FAIL"

    print(f"{name:<25}: {status}")

    return condition


print()
print("=" * 60)
print("          ORB AUTO TRADER - SYSTEM HEALTH CHECK")
print("=" * 60)
print()

results = []

# -------------------------------------------------
# Python
# -------------------------------------------------

results.append(
    check(
        "Python Version",
        sys.version_info >= (3, 10)
    )
)

# -------------------------------------------------
# Environment
# -------------------------------------------------

results.append(
    check(
        ".env File",
        os.path.exists(".env")
    )
)

results.append(
    check(
        "Dhan Client ID",
        bool(os.getenv("DHAN_CLIENT_ID"))
    )
)

results.append(
    check(
        "Dhan Access Token",
        bool(os.getenv("DHAN_ACCESS_TOKEN"))
    )
)

results.append(
    check(
        "Telegram Bot Token",
        bool(os.getenv("TELEGRAM_BOT_TOKEN"))
    )
)

results.append(
    check(
        "Telegram Chat ID",
        bool(os.getenv("TELEGRAM_CHAT_ID"))
    )
)

# -------------------------------------------------
# Files
# -------------------------------------------------

results.append(
    check(
        "Universe File",
        os.path.exists("data/universe.csv")
    )
)

results.append(
    check(
        "Trade Log",
        os.path.exists("trade_log.csv")
    )
)

# -------------------------------------------------
# Internet
# -------------------------------------------------

try:

    socket.create_connection(("8.8.8.8", 53), timeout=3)

    internet = True

except Exception:

    internet = False

results.append(
    check(
        "Internet Connection",
        internet
    )
)

print()
print("=" * 60)

if all(results):

    print("STATUS : READY TO TRADE")

else:

    print("STATUS : CHECK FAILED")

print("=" * 60)
print()