from railway_news_engine import RailwayNewsEngine

engine = RailwayNewsEngine()

print("=" * 80)
print("STARTING RAILWAY TEST")
print("=" * 80)

stats = engine.run()

print()
print("Returned Statistics")
print(stats)