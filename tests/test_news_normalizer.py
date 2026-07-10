"""
Standalone Test

News Normalizer

This test does NOT interact with the
trading engine.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from news_normalizer import NewsNormalizer


def print_separator():

    print("=" * 70)


def main():

    print_separator()
    print("NEWS NORMALIZER TEST")
    print_separator()

    normalizer = NewsNormalizer()

    # ==================================================
    # Test 1
    # ==================================================

    print("\nTEST 1 : VALID EVENT")
    print("-" * 70)

    valid_event = {

        "id": "NSE001",

        "source": "NSE",

        "title": "Board Meeting Scheduled",

        "link": "https://example.com",

        "published_at": "2026-07-09T12:00:00",

    }

    result = normalizer.normalize(valid_event)

    print(result)

    # ==================================================
    # Test 2
    # ==================================================

    print("\nTEST 2 : MISSING FIELD")
    print("-" * 70)

    invalid_event = {

        "source": "NSE",

        "title": "Missing ID",

        "link": "https://example.com",

        "published_at": "2026-07-09",

    }

    result = normalizer.normalize(invalid_event)

    print(result)

    # ==================================================
    # Test 3
    # ==================================================

    print("\nTEST 3 : EMPTY TITLE")
    print("-" * 70)

    invalid_event = {

        "id": "NSE002",

        "source": "NSE",

        "title": "",

        "link": "https://example.com",

        "published_at": "2026-07-09",

    }

    result = normalizer.normalize(invalid_event)

    print(result)

    # ==================================================
    # Statistics
    # ==================================================

    print("\nSTATISTICS")
    print("-" * 70)

    print(normalizer.statistics())

    # ==================================================
    # Reset
    # ==================================================

    print("\nRESET")
    print("-" * 70)

    normalizer.reset()

    print(normalizer.statistics())

    print()
    print_separator()
    print("TEST COMPLETED")
    print_separator()


if __name__ == "__main__":

    main()