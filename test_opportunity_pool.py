from opportunity_pool_engine import OpportunityPoolEngine

pool = OpportunityPoolEngine()

pool.add(
    symbol="RELIANCE",
    conviction=91,
    quality=91,
    orb={},
    intelligence={},
    evidence=[],
    brain_decision=None,
)

pool.add(
    symbol="ABB",
    conviction=96,
    quality=96,
    orb={},
    intelligence={},
    evidence=[],
    brain_decision=None,
)

print()

print("=" * 60)
print("OPPORTUNITY POOL")
print("=" * 60)

for opportunity in pool.ranked():

    print(
        opportunity.symbol,
        opportunity.conviction
    )

print("=" * 60)

print(pool.best().symbol)