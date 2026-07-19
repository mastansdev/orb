from sector_strength import SectorStrength

engine = SectorStrength()

print("=" * 60)
print("SECTOR STRENGTH TEST")
print("=" * 60)

print()
print(f"Sectors Loaded : {len(engine.sector_stocks)}")
print(f"Stocks Loaded  : {len(engine.stock_sector)}")

# ----------------------------------------

engine.update("HDFCBANK", 2010, 1980)
engine.update("ICICIBANK", 1485, 1450)
engine.update("SBIN", 835, 820)

engine.update("MARUTI", 12750, 12600)
engine.update("M&M", 3145, 3090)

engine.update("SUNPHARMA", 1725, 1710)

engine.update("TCS", 3510, 3550)

# ----------------------------------------

print()
print("=" * 60)
print("SECTOR RANKING")
print("=" * 60)

ranking = engine.get_strength()

for sector, strength, adv, decl, total in ranking:

    print(
        f"{sector:25}"
        f"A:{adv:>2} "
        f"D:{decl:>2} "
        f"T:{total:>2} "
        f"{strength*100:8.2f}%"
    )