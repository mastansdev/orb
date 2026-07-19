import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collectors.bse_corporate_collector import BSECorporateCollector

collector = BSECorporateCollector()

news = collector.collect()

print(f"Collected : {len(news)}")

for item in news:
    print(item)