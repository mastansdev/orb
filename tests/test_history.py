from core.historical_data import HistoricalData

h = HistoricalData()

response = h.dhan.intraday_minute_data(
    security_id="1333",
    exchange_segment="NSE_EQ",
    instrument_type="EQUITY",
    from_date="2026-06-26",
    to_date="2026-06-26",
    interval=15
)

print(response)
print(h.dhan.get_fund_limits())