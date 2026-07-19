import os
import csv

from trading.trade_logger import TradeLogger
from config import TRADE_LOG_FILE

print("=" * 60)
print("      ORB AUTO TRADER - TRADE LOGGER TEST")
print("=" * 60)

logger = TradeLogger()

logger.log_trade(
    trade_date="2026-06-28",
    entry_time="10:15:20",
    exit_time="10:48:10",

    symbol="SBIN",

    sector="Banking",
    industry="Private Bank",
    theme="Financial Services",

    qty=25,

    entry_price=1027.00,
    exit_price=1055.00,

    pnl=700.00,

    exit_reason="TARGET",

    conviction=92,
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