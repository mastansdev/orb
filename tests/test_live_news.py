"""
Standalone Live News Test

Institutional Grade ORB Auto Trading Bot

Purpose
-------
• Connect to one adapter
• Poll live news
• Print received events
• Print adapter statistics

No Trading
No Collector
No Brain
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from adapters.nse_adapter import NSEAdapter


def separator():

    print("=" * 100)


def main():

    separator()
    print("LIVE NEWS TEST")
    separator()

    adapter = NSEAdapter()

    print("\nConnecting...")

    adapter.connect()

    print("Connected :", adapter.connected())

    print("\nPolling...\n")

    events = adapter.poll()

    print(f"Events Received : {len(events)}")

    if events:

        separator()

        for index, event in enumerate(events, start=1):

            print(f"NEWS #{index}")

            print("-" * 100)

            print(f"Source        : {event.get('source')}")

            print(f"Title         : {event.get('title')}")

            print(f"Published     : {event.get('published_at')}")

            print(f"Link          : {event.get('link')}")

            print()

    else:

        print("\nNo news received.\n")

    separator()

    print("Adapter Statistics")

    print("-" * 100)

    print(adapter.statistics())

    print()

    print("Disconnecting...")

    adapter.disconnect()

    print("Connected :", adapter.connected())

    separator()

    print("LIVE NEWS TEST COMPLETED")

    separator()


if __name__ == "__main__":

    main()