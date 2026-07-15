from collectors.bse_corporate_collector import BSECorporateCollector

collector = BSECorporateCollector()

news = collector.collect()

print("=" * 80)
print(f"News Collected : {len(news)}")
print("=" * 80)

for item in news:
    print(item.headline)