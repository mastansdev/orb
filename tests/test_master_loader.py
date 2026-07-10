from price_engine import price_engine

price_engine.set_previous_close("INFY", 1800)

price_engine.update(
    symbol="INFY",
    ltp=1850,
)

print("=" * 60)

print(price_engine.get_stock("INFY"))

print("=" * 60)

print(price_engine.get_ltp("INFY"))

print(price_engine.get_previous_close("INFY"))

print(price_engine.get_change("INFY"))

print(price_engine.get_open("INFY"))

print(price_engine.get_high("INFY"))

print(price_engine.get_low("INFY"))

print(price_engine.has_price("INFY"))