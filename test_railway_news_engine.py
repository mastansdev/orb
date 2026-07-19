from railway_news_engine import RailwayNewsEngine
import time

engine = RailwayNewsEngine()

print("=" * 80)
print("FIRST POLL")
print("=" * 80)
engine.run()

print("\nWaiting 10 seconds...\n")
time.sleep(10)

print("=" * 80)
print("SECOND POLL")
print("=" * 80)
engine.run()