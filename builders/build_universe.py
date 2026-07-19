import os
import csv
import time
from dotenv import load_dotenv

from dhanhq import dhanhq, DhanContext
from core.instrument_loader import InstrumentLoader

load_dotenv()

context = DhanContext(
    os.getenv("DHAN_CLIENT_ID"),
    os.getenv("DHAN_ACCESS_TOKEN")
)

dhan = dhanhq(context)

loader = InstrumentLoader()

MIN_PRICE = 200
BATCH_SIZE = 20
MAX_RETRIES = 3

stocks = []

# ----------------------------------------
# Load NSE EQ Stocks
# ----------------------------------------

for _, row in loader.df.iterrows():

    if (
        str(row["SEM_EXM_EXCH_ID"]).strip() == "NSE"
        and str(row["SEM_SERIES"]).strip() == "EQ"
        and str(row["SEM_EXCH_INSTRUMENT_TYPE"]).strip() == "ES"
    ):

        stocks.append({
            "symbol": str(row["SEM_TRADING_SYMBOL"]).strip(),
            "security_id": str(row["SEM_SMST_SECURITY_ID"]).strip()
        })

print(f"\nNSE EQ Stocks : {len(stocks)}")

selected = []

total_batches = 0
success_batches = 0
failed_batches = 0

# ----------------------------------------
# Fetch Quotes
# ----------------------------------------

for i in range(0, len(stocks), BATCH_SIZE):

    total_batches += 1

    batch = stocks[i:i + BATCH_SIZE]

    security_ids = [
        int(stock["security_id"])
        for stock in batch
    ]

    response = None

    for attempt in range(MAX_RETRIES):

        response = dhan.quote_data(
            {
                "NSE_EQ": security_ids
            }
        )

        if response.get("status") == "success":
            break

        print(
            f"Retry {attempt+1}/{MAX_RETRIES} "
            f"for batch {total_batches}"
        )

        time.sleep(1)

    if response.get("status") != "success":

        failed_batches += 1

        print(
            f"Skipped batch {total_batches}"
        )

        continue

    success_batches += 1

    data = response["data"]["data"]["NSE_EQ"]
    
    for stock in batch:

        sid = stock["security_id"]

        # --- Updated Block 1: Check for Missing Quotes ---
        quote = data.get(sid)

        if quote is None:
            print(f"NO QUOTE : {stock['symbol']}")
            continue
        # -------------------------------------------------

        ltp = quote["last_price"]
        volume = quote.get("volume", 0)

        # --- Updated Block 2: Early Exits & Detailed Filtering Logs ---
        if ltp < MIN_PRICE:
            continue

        if volume < 100000:
            print(f"LOW VOLUME : {stock['symbol']} ({volume})")
            continue

        selected.append({
            "symbol": stock["symbol"],
            "security_id": sid,
            "ltp": ltp
        })
        # -------------------------------------------------------------

    print(
        f"Processed {min(i+BATCH_SIZE,len(stocks))}/{len(stocks)}"
    )

# ----------------------------------------
# Save CSV
# ----------------------------------------

os.makedirs("data", exist_ok=True)

with open(
    "data/universe.csv",
    "w",
    newline=""
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "Symbol",
        "SecurityID",
        "LTP"
    ])

    for stock in selected:

        writer.writerow([
            stock["symbol"],
            stock["security_id"],
            stock["ltp"]
        ])

print("\n==============================")
print(f"Total Batches     : {total_batches}")
print(f"Success Batches   : {success_batches}")
print(f"Failed Batches    : {failed_batches}")
print(f"Selected Stocks   : {len(selected)}")
print("==============================")
print("Universe saved to data/universe.csv")