import os
import pandas as pd

INPUT_FILE = "Masterdata/master_stocks_data.xlsx"
OUTPUT_FILE = "Masterdata/sector_database.csv"

REQUIRED_COLUMNS = [
    "Symbol",
    "CompanyName",
    "Sector",
    "Industry"
]


def main():

    print("=" * 60)
    print("Building Sector Database")
    print("=" * 60)

    if not os.path.exists(INPUT_FILE):
        print(f"\nERROR : File not found\n{INPUT_FILE}")
        return

    df = pd.read_excel(INPUT_FILE)

    missing = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing:
        print(f"\nMissing Columns : {missing}")
        return

    df = df[REQUIRED_COLUMNS].copy()

    df["Symbol"] = (
        df["Symbol"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["CompanyName"] = (
    df["CompanyName"]
    .astype(str)
    .str.strip()
    .str.upper()
    )

    df["Sector"] = (
        df["Sector"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["Industry"] = (
        df["Industry"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    before = len(df)

    df = (
        df
        .drop_duplicates(subset="Symbol")
        .sort_values("Symbol")
        .reset_index(drop=True)
    )

    after = len(df)

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(f"Loaded Records      : {before}")
    print(f"Duplicate Removed   : {before - after}")
    print(f"Final Records       : {after}")
    print(f"Saved               : {OUTPUT_FILE}")

    print("\nSector Database Built Successfully.")


if __name__ == "__main__":
    main()