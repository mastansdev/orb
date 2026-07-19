from opportunity_pool_engine import (
    opportunity_pool,
)

from capital_allocation_engine import (
    CapitalAllocationEngine,
)

# --------------------------------------------

opportunity_pool.clear()

# --------------------------------------------

opportunity_pool.add(
    symbol="RELIANCE",
    conviction=91,
    quality=91,
    orb={},
    intelligence={},
    evidence=[],
    brain_decision=None,
)

opportunity_pool.add(
    symbol="ABB",
    conviction=97,
    quality=97,
    orb={},
    intelligence={},
    evidence=[],
    brain_decision=None,
)

opportunity_pool.add(
    symbol="HAL",
    conviction=95,
    quality=95,
    orb={},
    intelligence={},
    evidence=[],
    brain_decision=None,
)

# --------------------------------------------

engine = CapitalAllocationEngine()

print()

print("=" * 60)
print("CAPITAL ALLOCATION")
print("=" * 60)

while True:

    opportunity = engine.allocate()

    if opportunity is None:
        break

    print(
    opportunity.symbol,
    opportunity.conviction,
    opportunity.state,
    )

    engine.confirm_execution(
    opportunity.symbol
    )

print("=" * 60)

print(engine.stats())