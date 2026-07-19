from intelligence_engine import IntelligenceEngine

engine = IntelligenceEngine()

print("=" * 70)
print("INTELLIGENCE ENGINE UNIT TEST")
print("=" * 70)

print("\nHEALTH")
print(engine.health())

print("\nCHANGE")
print(engine.get_change("INFY"))

print("\nSECTOR")
print(engine.get_sector("INFY"))

print("\nINDUSTRY")
print(engine.get_industry("INFY"))

print("\nSECTOR SUMMARY")
print(engine.get_sector_summary("INFY"))

print("\nINDUSTRY SUMMARY")
print(engine.get_industry_summary("INFY"))

print("\nUPDATING INFY...")

engine.update(
    symbol="INFY",
    ltp=1850.00,
    ltt="09:30:01"
)

print("\nCHANGE AFTER UPDATE")
print(engine.get_change("INFY"))

print("\nSECTOR SUMMARY AFTER UPDATE")
print(engine.get_sector_summary("INFY"))

print("\nINDUSTRY SUMMARY AFTER UPDATE")
print(engine.get_industry_summary("INFY"))

print("\nTOP 5 SECTORS")
for rank, (sector, data) in enumerate(
    engine.sector_engine.get_top_sectors(5),
    start=1
):
    print(rank, sector)

print("\nTOP 5 INDUSTRIES")
for rank, (industry, data) in enumerate(
    engine.industry_engine.get_top_industries(5),
    start=1
):
    print(rank, industry)

print("\nUNIT TEST COMPLETED")
print("=" * 70)