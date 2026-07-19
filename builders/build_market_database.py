import pandas as pd

from config import (
    UNIVERSE_FILE,
    API_SCRIP_MASTER_FILE,
    MARKET_DATABASE_FILE
)

MASTER_FILE = "Masterdata/master_stocks_data.xlsx"

# --------------------------------------------------

print("Loading Universe...")

universe = pd.read_csv(
    UNIVERSE_FILE,
    dtype=str
)

universe["SecurityID"] = (
    universe["SecurityID"]
    .astype(str)
    .str.strip()
)

print(f"Universe Stocks : {len(universe)}")

# --------------------------------------------------

print("Loading Dhan Master...")

master = pd.read_csv(
    API_SCRIP_MASTER_FILE,
    low_memory=False,
    dtype=str
)

master = master[
    (master["SEM_EXM_EXCH_ID"] == "NSE") &
    (master["SEM_SERIES"] == "EQ") &
    (master["SEM_EXCH_INSTRUMENT_TYPE"] == "ES")
].copy()

master["SEM_SMST_SECURITY_ID"] = (
    master["SEM_SMST_SECURITY_ID"]
    .astype(str)
    .str.strip()
)

print(f"NSE EQ Stocks   : {len(master)}")

# --------------------------------------------------

print("Loading Master Stocks...")

master_stock = pd.read_excel(
    MASTER_FILE,
    dtype=str
).fillna("")

master_stock["Symbol"] = (
    master_stock["Symbol"]
    .str.strip()
    .str.upper()
)

print(f"Master Stocks  : {len(master_stock)}")

# --------------------------------------------------

database = universe.merge(
    master,
    left_on="SecurityID",
    right_on="SEM_SMST_SECURITY_ID",
    how="left",
    indicator=True
)

print()
print(database["_merge"].value_counts())

# --------------------------------------------------

output = pd.DataFrame({
    "SecurityID": database["SecurityID"],
    "Symbol": database["SEM_TRADING_SYMBOL"],
    "CompanyName": database["SEM_CUSTOM_SYMBOL"]
})

output["Symbol"] = (
    output["Symbol"]
    .fillna("")
    .str.strip()
    .str.upper()
)

# Merge Sector and Industry from Master Stock
output = output.merge(
    master_stock[[
        "Symbol",
        "Sector",
        "Industry"
    ]],
    on="Symbol",
    how="left"
)

# Initialize remaining columns
output["BasicIndustry"] = ""
output["MarketCap"] = ""
output["PreviousClose"] = ""
output["FNO"] = ""

# --------------------------------------------------

mapped = output["Sector"].notna().sum()

print()
print("=" * 60)
print("SECTOR MAPPING REPORT")
print("=" * 60)
print(f"Universe        : {len(output)}")
print(f"Sector Mapped   : {mapped}")
print(f"Sector Missing  : {len(output) - mapped}")

output.to_csv(
    MARKET_DATABASE_FILE,
    index=False
)

print()
print("Market Database Created Successfully.")
print(f"Records : {len(output)}")
print(f"Saved To : {MARKET_DATABASE_FILE}")