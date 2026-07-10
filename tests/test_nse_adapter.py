"""
Standalone Test
NSE Adapter

This test is completely isolated from
the trading bot.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from adapters.nse_adapter import NSEAdapter



def main():

    print("=" * 60)
    print("NSE ADAPTER TEST")
    print("=" * 60)

    adapter = NSEAdapter()

    print("\nConnecting...")

    adapter.connect()

    print("Connected :", adapter.connected())

    print("\nPolling RSS...\n")

    events = adapter.poll()

    print(f"Events Received : {len(events)}")

    if events:

        print("\nFirst Event")
        print("-" * 60)

        first = events[0]

        for key, value in first.items():

            print(f"{key:15}: {value}")

    else:

        print("\nNo events returned.")

    print("\nHealth")
    print("-" * 60)

    print(adapter.health())

    print("\nStatistics")
    print("-" * 60)

    print(adapter.statistics())

    print("\nDisconnecting...")

    adapter.disconnect()

    print("Connected :", adapter.connected())

    print("\nTEST COMPLETED")


if __name__ == "__main__":

    main()