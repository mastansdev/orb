import os
import time

from dotenv import load_dotenv
from dhanhq import DhanContext, MarketFeed

from watchlist import get_instruments

load_dotenv()

print("=" * 60)
print("        ORB AUTO TRADER - MARKET FEED TEST")
print("=" * 60)

context = DhanContext(
    os.getenv("DHAN_CLIENT_ID"),
    os.getenv("DHAN_ACCESS_TOKEN")
)

instruments = get_instruments()

print(f"Instruments Loaded : {len(instruments)}")

feed = MarketFeed(
    context,
    instruments,
    "v2"
)

print("Connecting to Dhan...")

feed.run_forever()

print("Connected Successfully")
print()

print("Waiting for Market Tick...")

timeout = time.time() + 10

while time.time() < timeout:

    tick = feed.get_data()

    if tick:

        print("✓ Tick Received")
        print()
        print(tick)
        break

    time.sleep(0.05)

else:

    print("No Tick Received")
    print("Market may be closed.")

print()

print("=" * 60)