from industry_engine import IndustryEngine

engine = IndustryEngine()

print("=" * 60)
print("TOTAL INDUSTRIES")
print(len(engine.industries))

print("=" * 60)
print("RANKINGS")
print(len(engine.get_rankings()))

print("=" * 60)
print("TOP 5")
for rank, (industry, data) in enumerate(engine.get_top_industries(5), start=1):
    print(rank, industry)

print("=" * 60)
print("BOTTOM 5")
for rank, (industry, data) in enumerate(engine.get_bottom_industries(5), start=1):
    print(rank, industry)

print("=" * 60)
print("INFY INDUSTRY")
industry = engine.get_industry("INFY")
print(industry)

print("=" * 60)
print("SUMMARY")
print(engine.get_industry_summary(industry))