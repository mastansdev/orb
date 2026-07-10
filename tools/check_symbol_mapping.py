import pandas as pd

INPUT_FILE = "data/market_database.csv"
OUTPUT_FILE = "Masterdata/missing_sector_symbols.csv"

df = pd.read_csv(INPUT_FILE, dtype=str)
df.fillna("", inplace=True)

missing = df[df["Sector"].str.strip() == ""]

print("=" * 60)
print("SYMBOL MAPPING REPORT")
print("=" * 60)
print(f"Total Stocks     : {len(df)}")
print(f"Sector Mapped    : {len(df) - len(missing)}")
print(f"Sector Missing   : {len(missing)}")

missing[["SecurityID", "Symbol", "CompanyName"]].to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print(f"Saved : {OUTPUT_FILE}")