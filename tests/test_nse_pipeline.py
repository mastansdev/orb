"""
Standalone Integration Test

NSE Adapter
        ↓
News Normalizer

No Trading
No Collector
No Brain
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from adapters.nse_adapter import NSEAdapter
from news_normalizer import NewsNormalizer


def print_separator():

    print("=" * 80)


def main():

    print_separator()
    print("NSE PIPELINE TEST")
    print_separator()

    adapter = NSEAdapter()

    normalizer = NewsNormalizer()

    print("\nConnecting to NSE...")

    adapter.connect()

    print("Connected :", adapter.connected())

    print("\nPolling RSS...\n")

    raw_events = adapter.poll()

    print(f"Raw Events Received : {len(raw_events)}")

    normalized_events = []

    for event in raw_events:

        normalized = normalizer.normalize(event)

        if normalized:

            normalized_events.append(normalized)

    print(f"Normalized Events  : {len(normalized_events)}")

    if normalized_events:

        print("\nFirst Normalized Event")
        print("-" * 80)

        first = normalized_events[0]

        for key, value in first.items():

            print(f"{key:20}: {value}")

    else:

        print("\nNo normalized events.")

    print("\nAdapter Statistics")
    print("-" * 80)

    print(adapter.statistics())

    print("\nNormalizer Statistics")
    print("-" * 80)

    print(normalizer.statistics())

    print("\nDisconnecting...")

    adapter.disconnect()

    print("Connected :", adapter.connected())

    print()
    print_separator()
    print("PIPELINE TEST COMPLETED")
    print_separator()


if __name__ == "__main__":

    main()