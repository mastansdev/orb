"""
Standalone Test

Position Intelligence

This test does NOT interact with the
trading engine.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from trading.position_intelligence import PositionIntelligenceEngine


def main():

    print("=" * 70)
    print("POSITION INTELLIGENCE TEST")
    print("=" * 70)

    engine = PositionIntelligenceEngine()

    # --------------------------------------------------
    # Sample Open Positions
    # --------------------------------------------------

    open_positions = {

        "1001": {

            "symbol": "DRREDDY",

            "qty": 75,

            "entry": 1346.00,

        },

        "1002": {

            "symbol": "HAL",

            "qty": 20,

            "entry": 5250.00,

        },

        "1003": {

            "symbol": "BEL",

            "qty": 150,

            "entry": 405.50,

        },

    }

    # --------------------------------------------------
    # Sample Intelligence Event
    # --------------------------------------------------

    event = {

        "symbol": "DRREDDY",

        "classification": "NEGATIVE",

        "severity": 9,

        "confidence": 95,

        "headline": "USFDA issues observations."

    }

    # --------------------------------------------------

    result = engine.process_event(

        event,

        open_positions,

    )

    print()

    print("Result")

    print("-" * 70)

    for key, value in result.items():

        print(f"{key:20}: {value}")

    print()

    print("Statistics")

    print("-" * 70)

    print(engine.statistics())

    print()

    print("TEST COMPLETED")


if __name__ == "__main__":

    main()