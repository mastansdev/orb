import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from intelligence.opportunity_pool_engine import (
    opportunity_pool,
)

from trading.allocation_trigger_engine import (
    AllocationTriggerEngine,
)

# ----------------------------------------

opportunity_pool.clear()

engine = AllocationTriggerEngine()

print()

print("=" * 60)
print("EMPTY POOL")
print("=" * 60)

print(

    engine.should_allocate(

        open_positions=0

    )

)

# ----------------------------------------

opportunity_pool.add(

    symbol="ABB",

    conviction=97,

    quality=97,

    orb={},

    intelligence={},

    evidence=[],

    brain_decision=None,

)

print()

print("=" * 60)
print("HIGH CONVICTION")
print("=" * 60)

print(

    engine.should_allocate(

        open_positions=0

    )

)