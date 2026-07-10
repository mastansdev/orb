import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from news_engine import NewsEngine
from collectors.news_rss_collector import NewsRSSCollector


engine = NewsEngine()

engine.register_collector(
    NewsRSSCollector()
)

print("=" * 60)
print("Collecting News...")
print("=" * 60)

count = engine.collect()

print(f"Collected : {count}")
print(f"Queue Size : {engine.queue_size()}")

processed = engine.process()

print(f"Processed : {len(processed)}")