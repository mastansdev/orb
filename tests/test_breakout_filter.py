import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
test_breakout_filter.py

Pulls today's real 1-minute candles for a symbol from Dhan's Historical Data API,
converts them into the tick format MarketReplay/Engine expect, and runs is_buy_signal()
minute-by-minute to see exactly when (if ever) a trade would have qualified —
under the CURRENT config, and optionally under a wider MAX_BREAKOUT_PERCENT.

This does NOT modify config.py permanently — it patches the value in-memory for
the test only, so your live bot's config is untouched.

Usage:
    python test_breakout_filter.py RELAXO
    python test_breakout_filter.py RELAXO --test-percent 3.0
"""

import os
import sys
import argparse
import requests
from datetime import datetime, date

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core.instrument_loader import InstrumentLoader
import config
from core.strategy import Strategy

BASE_URL = "https://api.dhan.co/v2"


def get_headers():
    return {
        "Content-Type": "application/json",
        "access-token": os.environ.get("DHAN_ACCESS_TOKEN"),
        "client-id": os.environ.get("DHAN_CLIENT_ID"),
    }


def fetch_today_candles(security_id: str) -> list[dict]:
    """Fetches today's 1-min OHLC candles for the given security_id."""
    today = date.today()
    resp = requests.post(
        f"{BASE_URL}/charts/intraday",
        headers=get_headers(),
        json={
            "securityId": security_id,
            "exchangeSegment": "NSE_EQ",
            "instrument": "EQUITY",
            "interval": "1",
            "oi": False,
            "fromDate": f"{today} 09:15:00",
            "toDate": f"{today} 15:30:00",
        },
        timeout=15,
    )
    if resp.status_code != 200:
        print(f"Dhan API error {resp.status_code}: {resp.text}")
        sys.exit(1)
    data = resp.json()

    # Response is column-oriented arrays; zip them into per-candle dicts
    timestamps = data.get("timestamp", [])
    closes = data.get("close", [])
    if not timestamps:
        print("No candle data returned — market may be closed or symbol has no data today.")
        sys.exit(1)

    candles = []
    for ts, close in zip(timestamps, closes):
        candles.append({
            "time": datetime.fromtimestamp(ts).strftime("%H:%M:%S"),
            "ltp": close,
        })
    return candles


def simulate(symbol: str, security_id: str, candles: list[dict], breakout_percent: float):
    """
    Rebuilds the opening range from the first 15 minutes of candles, then walks
    through the rest of the day checking is_buy_signal() minute by minute.
    """
    original_percent = config.MAX_BREAKOUT_PERCENT
    config.MAX_BREAKOUT_PERCENT = breakout_percent  # in-memory patch, test only

    strategy = Strategy()

    orb_high = None
    orb_low = None
    orb_complete = False
    entry_taken = False
    first_qualifying_time = None
    first_qualifying_price = None

    for candle in candles:
        t = candle["time"]
        ltp = candle["ltp"]

        # Build opening range from 09:15 to 09:30
        if t < "09:30:00":
            orb_high = ltp if orb_high is None else max(orb_high, ltp)
            orb_low = ltp if orb_low is None else min(orb_low, ltp)
            continue
        elif not orb_complete:
            orb_complete = True

        orb = {
            "completed": orb_complete,
            "entry_taken": entry_taken,
            "high": orb_high,
            "low": orb_low,
        }

        if strategy.is_buy_signal(ltp, orb, t):
            first_qualifying_time = t
            first_qualifying_price = ltp
            entry_taken = True
            break  # one trade per symbol per day, matches your live logic

    config.MAX_BREAKOUT_PERCENT = original_percent  # restore

    print(f"\n{symbol} | ORB High: {orb_high} | ORB Low: {orb_low} | "
          f"MAX_BREAKOUT_PERCENT tested: {breakout_percent}%")
    if first_qualifying_time:
        move_pct = ((first_qualifying_price - orb_high) / orb_high) * 100
        print(f"  -> WOULD HAVE ENTERED at {first_qualifying_time}, "
              f"price {first_qualifying_price} ({move_pct:.2f}% above ORB high)")
    else:
        print(f"  -> NO ENTRY all day at this threshold")

    return first_qualifying_time is not None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol")
    parser.add_argument("--test-percent", type=float, default=None,
                         help="Also test with this MAX_BREAKOUT_PERCENT for comparison")
    args = parser.parse_args()

    loader = InstrumentLoader()
    security_id = loader.get_security_id(args.symbol.upper())
    if security_id is None:
        print(f"'{args.symbol}' not found in instrument master.")
        sys.exit(1)

    candles = fetch_today_candles(str(security_id))

    print("=" * 60)
    print(f"TESTING: {args.symbol.upper()} — {len(candles)} candles fetched")
    print("=" * 60)

    # Always show current live config result first
    simulate(args.symbol.upper(), str(security_id), candles, config.MAX_BREAKOUT_PERCENT)

    if args.test_percent is not None:
        simulate(args.symbol.upper(), str(security_id), candles, args.test_percent)