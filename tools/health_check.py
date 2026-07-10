import os
import sys
import socket

from dotenv import load_dotenv
from dhanhq import DhanContext, dhanhq

from config import (
    CAPITAL,
    RISK_PER_TRADE,
    RISK_REWARD,
    MIN_QTY,
    MIN_TRADE_VALUE,
    ENTRY_BUFFER,
    ORB_BUFFER,
    TRADE_LOG_FILE,
    UNIVERSE_FILE,
    TRADE_MODE,
    BOT_NAME,
    VERSION
)

load_dotenv()


# ==========================================================
# HELPERS
# ==========================================================

passed = 0
failed = 0


def check(title, status, value=""):

    global passed, failed

    if status:
        passed += 1
        print(f"{title:<30}: ✓ PASS {value}")
    else:
        failed += 1
        print(f"{title:<30}: ✗ FAIL {value}")


def internet_available():

    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except Exception:
        return False
    
# ==========================================================
# HEADER
# ==========================================================

print("=" * 60)
print("        ORB AUTO TRADER - SYSTEM HEALTH CHECK")
print("=" * 60)
print()


# ==========================================================
# SYSTEM
# ==========================================================

check(
    "Python Version",
    sys.version_info >= (3, 10),
    f"({sys.version.split()[0]})"
)

check(
    ".env File",
    os.path.exists(".env")
)

check(
    "config.py",
    os.path.exists("config.py")
)


# ==========================================================
# ENVIRONMENT VARIABLES
# ==========================================================

CLIENT_ID = os.getenv("DHAN_CLIENT_ID")
ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

check("Dhan Client ID", bool(CLIENT_ID))
check("Dhan Access Token", bool(ACCESS_TOKEN))
check("Telegram Bot Token", bool(BOT_TOKEN))
check("Telegram Chat ID", bool(CHAT_ID))


# ==========================================================
# FILES
# ==========================================================

check(
    "Universe File",
    os.path.exists(UNIVERSE_FILE)
)

check(
    "Trade Log",
    os.path.exists(TRADE_LOG_FILE)
)

check(
    "Logs Folder",
    os.path.exists("logs")
)

# ==========================================================
# CONFIG
# ==========================================================

print()
print("-" * 60)
print("TRADING CONFIGURATION")
print("-" * 60)

print(f"Capital                  : ₹{CAPITAL:,.2f}")
print(f"Risk Per Trade           : {RISK_PER_TRADE * 100:.2f}%")
print(f"Risk Reward              : 1:{RISK_REWARD}")
print(f"Minimum Qty              : {MIN_QTY}")
print(f"Minimum Trade Value      : ₹{MIN_TRADE_VALUE:,.2f}")
print(f"Entry Buffer             : {ENTRY_BUFFER}")
print(f"ORB Buffer               : {ORB_BUFFER}")


# ==========================================================
# UNIVERSE
# ==========================================================

print()
print("-" * 60)
print("UNIVERSE")
print("-" * 60)

if os.path.exists(UNIVERSE_FILE):

    try:

        with open(UNIVERSE_FILE, "r", encoding="utf-8") as file:

            universe_count = sum(1 for _ in file) - 1

        check(
            "Universe Stocks",
            universe_count > 0,
            f"({universe_count})"
        )

    except Exception:

        check("Universe Stocks", False)

else:

    check("Universe Stocks", False)


# ==========================================================
# INTERNET
# ==========================================================

print()
print("-" * 60)
print("CONNECTIVITY")
print("-" * 60)

check(
    "Internet Connection",
    internet_available()
)


# ==========================================================
# DHAN REST API
# ==========================================================

try:

    context = DhanContext(
        CLIENT_ID,
        ACCESS_TOKEN
    )

    dhan = dhanhq(context)

    response = dhan.get_fund_limits()

    if response["status"] == "success":

        check(
            "Dhan REST API",
            True
        )

        balance = response["data"]["availabelBalance"]

        print(f"Available Balance        : ₹{balance}")

    else:

        check(
            "Dhan REST API",
            False
        )

except Exception:

    check(
        "Dhan REST API",
        False
    )

# ==========================================================
# SUMMARY
# ==========================================================

print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)

print(f"Total Checks             : {passed + failed}")
print(f"Passed                   : {passed}")
print(f"Failed                   : {failed}")

print()

if failed == 0:

    print("=" * 60)
    print("STATUS : READY TO TRADE")
    print("=" * 60)

else:

    print("=" * 60)
    print("STATUS : NOT READY")
    print("=" * 60)

print()

print("Current Configuration")
print("-" * 60)
print(f"Bot                      : {BOT_NAME}")
print(f"Version                  : {VERSION}")
print(f"Mode                     : {TRADE_MODE}")
print("Strategy                 : ORB 15 Minutes")
print("Exchange                 : NSE")
print(f"Capital                  : ₹{CAPITAL:,.2f}")
print(f"Universe                 : {universe_count if 'universe_count' in locals() else 0} Stocks")
print()

print("=" * 60)