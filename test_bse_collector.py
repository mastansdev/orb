from collectors.bse_corporate_collector import BSECorporateCollector

collector = BSECorporateCollector()

news = collector.collect()

print(f"Collected : {len(news)}")

for item in news:
    print(item)