
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from trading.portfolio_intelligence_engine import (
    PortfolioIntelligenceEngine,
)



class Position:

    def __init__(
        self,
        symbol,
        conviction,
        holding_seconds=1200,
    ):
        self.symbol = symbol
        self.conviction = conviction
        self.holding_seconds = holding_seconds


class Opportunity:

    def __init__(
        self,
        symbol,
        conviction,
    ):
        self.symbol = symbol
        self.conviction = conviction


class Portfolio:

    def __init__(self, positions):
        self.positions = positions

    def weakest_position(self):
        return min(
            self.positions,
            key=lambda p: p.conviction
        )


engine = PortfolioIntelligenceEngine(
    replacement_threshold=15,
    minimum_hold_seconds=600,
)

print("=" * 70)
print("PORTFOLIO INTELLIGENCE ENGINE")
print("=" * 70)

# ----------------------------------------------------------
# TEST 1
# Better opportunity should replace weakest
# ----------------------------------------------------------

portfolio = Portfolio([
    Position("ABC", 72),
    Position("HAL", 91),
    Position("ABB", 96),
])

opportunities = [
    Opportunity("BHEL", 95),
]

result = engine.evaluate(
    portfolio,
    opportunities,
)

print()
print("TEST 1")
print(result)

assert result.action == "REPLACE"

# ----------------------------------------------------------
# TEST 2
# Gap too small
# ----------------------------------------------------------

portfolio = Portfolio([
    Position("ABC", 82),
    Position("HAL", 91),
])

opportunities = [
    Opportunity("BHEL", 90),
]

result = engine.evaluate(
    portfolio,
    opportunities,
)

print()
print("TEST 2")
print(result)

assert result.action == "KEEP"

# ----------------------------------------------------------
# TEST 3
# Minimum holding time not completed
# ----------------------------------------------------------

portfolio = Portfolio([
    Position(
        "ABC",
        70,
        holding_seconds=120,
    ),
])

opportunities = [
    Opportunity("ABB", 96),
]

result = engine.evaluate(
    portfolio,
    opportunities,
)

print()
print("TEST 3")
print(result)

assert result.action == "KEEP"

print()
print("=" * 70)
print("ALL TESTS PASSED")
print("=" * 70)