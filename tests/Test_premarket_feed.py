"""
==========================================================
PRE-MARKET FEED DIAGNOSTIC (standalone, safe, temporary)
==========================================================

Purpose
-------
Answer one question empirically: does Dhan's WebSocket feed
send ANYTHING during NSE's 09:00-09:08 pre-open order-collection
window, and if so, what does it look like?

This is completely isolated from your production bot:
    - Does NOT import engine.py, market_data.py, or anything
      from your live codebase.
    - Does NOT place orders, size positions, or touch capital.
    - Subscribes to just 5 well-known liquid stocks (RELIANCE,
      TCS, HDFCBANK, INFY, SBIN) in BOTH Ticker and Quote mode,
      so you also get a bonus look at what a Quote-mode packet
      actually contains (relevant to the separate Volume-data
      question).
    - Prints every single packet received, with wall-clock
      arrival time and packet type, to both the console and a
      timestamped log file so you can review it after the fact
      even if you're not watching the terminal live.

How to use
----------
1. Run this a few minutes before 9:00 AM:
       py test_premarket_feed.py
2. Let it run through market open (past 9:15).
3. Ctrl+C to stop whenever you're satisfied -- it does nothing
   destructive, so there's no risk in stopping it at any point.
4. Check the printed summary (or the log file) for exactly when
   the first packet arrived and what packet types showed up
   before vs. after 9:00, 9:08, and 9:15.

Safe to delete after you're done -- this is a one-time
diagnostic, not part of the permanent codebase.
==========================================================
"""

import os
import time
from datetime import datetime

from dotenv import load_dotenv
from dhanhq import DhanContext, MarketFeed

load_dotenv()

LOG_FILE = f"premarket_feed_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# A handful of well-known, highly liquid stocks -- if pre-open
# data exists for ANY stock, it's most likely to show up here
# first, since these have the deepest order books.
TEST_STOCKS = {
    "2885": "RELIANCE",
    "11536": "TCS",
    "1333": "HDFCBANK",
    "1594": "INFY",
    "3045": "SBIN",
}

context = DhanContext(
    os.getenv("DHAN_CLIENT_ID"),
    os.getenv("DHAN_ACCESS_TOKEN"),
)

instruments = []
for security_id in TEST_STOCKS:
    instruments.append((MarketFeed.NSE, security_id, MarketFeed.Ticker))
    instruments.append((MarketFeed.NSE, security_id, MarketFeed.Quote))

packet_count = 0
first_packet_time = None
milestones_logged = set()  # tracks which time-window messages we've already printed


def log(line):
    """Print to console AND append to the log file."""
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check_milestone(now):
    """Print a one-time marker each time we cross a key NSE session boundary."""
    t = now.strftime("%H:%M")

    milestones = {
        "09:00": "=== 09:00 -- NSE pre-open order collection begins ===",
        "09:08": "=== 09:08 -- order collection closing / matching begins ===",
        "09:12": "=== 09:12 -- buffer period begins ===",
        "09:15": "=== 09:15 -- NORMAL MARKET OPENS ===",
    }

    if t in milestones and t not in milestones_logged:
        milestones_logged.add(t)
        log("\n" + milestones[t] + "\n")


def on_connect(instance):
    log(f"[{datetime.now().strftime('%H:%M:%S')}] Connected to Dhan MarketFeed")
    log(f"Subscribed: {list(TEST_STOCKS.values())} (Ticker + Quote mode)")
    log(f"Logging to: {LOG_FILE}")
    log("Waiting for packets... (Ctrl+C to stop at any time)\n")


def on_error(instance, error):
    log(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {error}")


def on_message(instance, tick):
    global packet_count, first_packet_time

    now = datetime.now()
    check_milestone(now)

    if tick is None:
        return

    packet_count += 1
    if first_packet_time is None:
        first_packet_time = now
        log(f"\n>>> FIRST PACKET EVER RECEIVED at {now.strftime('%H:%M:%S')} <<<\n")

    security_id = str(tick.get("security_id", "?"))
    symbol = TEST_STOCKS.get(security_id, security_id)
    tick_type = tick.get("type", "?")

    log(
        f"[{now.strftime('%H:%M:%S.%f')[:-3]}] "
        f"{symbol:<10} type={tick_type:<18} raw={tick}"
    )


feed = MarketFeed(
    context,
    instruments,
    "v2",
    on_connect=on_connect,
    on_message=on_message,
    on_error=on_error,
)

log(f"Starting pre-market feed diagnostic at {datetime.now().strftime('%H:%M:%S')}")
log("This does NOT touch your live bot, place orders, or use capital.\n")

try:
    feed.run()
except KeyboardInterrupt:
    log(f"\n\nStopped by user at {datetime.now().strftime('%H:%M:%S')}")
    log(f"Total packets received: {packet_count}")
    if first_packet_time:
        log(f"First packet arrived at: {first_packet_time.strftime('%H:%M:%S')}")
    else:
        log("No packets were ever received.")
    log(f"\nFull log saved to: {LOG_FILE}")
    feed.close_connection()