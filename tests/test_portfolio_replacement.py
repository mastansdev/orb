import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.portfolio_risk_manager import (
    PortfolioRiskManager,
    PortfolioOpportunity,
)

# ==========================================================
# Create Portfolio
# ==========================================================

manager = PortfolioRiskManager(
    max_open_trades=2
)

# Existing Portfolio

manager.add_trade(

    PortfolioOpportunity(

        symbol="ABC",

        conviction=70,

        quality=70,

    )

)

manager.add_trade(

    PortfolioOpportunity(

        symbol="XYZ",

        conviction=85,

        quality=85,

    )

)

print()
print("=" * 60)
print("TEST 1 : SMALL IMPROVEMENT")
print("=" * 60)

decision = manager.can_take_trade(

    PortfolioOpportunity(

        symbol="NEW1",

        conviction=74,

        quality=74,

    )

)

print(decision)

print()

print("=" * 60)
print("TEST 2 : LARGE IMPROVEMENT")
print("=" * 60)

decision = manager.can_take_trade(

    PortfolioOpportunity(

        symbol="NEW2",

        conviction=95,

        quality=95,

    )

)

print(decision)