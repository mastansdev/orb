import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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