import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collectors.bse_corporate_collector import BSECorporateCollector

collector = BSECorporateCollector()

news = collector.collect()

print("=" * 80)
print(f"News Collected : {len(news)}")
print("=" * 80)

for item in news:
    print(item.headline)