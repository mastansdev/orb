import os
import csv

from trade_logger import TradeLogger
from config import TRADE_LOG_FILE

print("=" * 60)
print("      ORB AUTO TRADER - TRADE LOGGER TEST")
print("=" * 60)

logger = TradeLogger()

logger.log_trade(
    "2026-06-28",
    "10:15:20",
    "SBIN",
    1027.00,
    1055.00,
    25,
    700.00,
    "TARGET"
)

print("✓ Dummy Trade Logged")

print()

if os.path.exists(TRADE_LOG_FILE):

    with open(TRADE_LOG_FILE, newline="", encoding="utf-8") as file:

        rows = list(csv.reader(file))

        print(f"Rows in Trade Log : {len(rows)}")

        print()

        print("Last Entry")

        print(rows[-1])

        print()

        print("✓ Trade Logger PASS")

else:

    print("✗ Trade Log File Missing")

print("=" * 60)