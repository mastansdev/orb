from dhanhq import dhanhq
from config import CLIENT_ID, ACCESS_TOKEN

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

print(dhan.ticker_data(
    securities={
        "NSE_EQ": [1333]   # HDFCBANK
    }
))