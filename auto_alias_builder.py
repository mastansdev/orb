import re
import pandas as pd

MASTER_FILE = "Masterdata/master_stocks_data.xlsx"
API_MASTER = "data/api-scrip-master.csv"
UNIVERSE_FILE = "data/universe.csv"

def normalize(text):
    text = str(text).upper()
    text = text.replace("&", "AND")

    remove_words = [
        "LIMITED",
        "LTD",
        "LIMITED.",
        "PRIVATE",
        "PVT",
        "COMPANY",
        "CO",
    ]

    for word in remove_words:
        text = text.replace(word, "")

    text = re.sub(r"[^A-Z0-9]", "", text)
    return text.strip()


print("=" * 60)
print("AUTO ALIAS BUILDER")
print("=" * 60)

master = pd.read_excel(
    MASTER_FILE,
    dtype=str
).fillna("")

api = pd.read_csv(
    API_MASTER,
    dtype=str,
    low_memory=False
).fillna("")

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

api = api[
    (api["SEM_EXM_EXCH_ID"] == "NSE") &
    (api["SEM_SERIES"] == "EQ") &
    (api["SEM_EXCH_INSTRUMENT_TYPE"] == "ES")
].copy()

api["SEM_SMST_SECURITY_ID"] = (
    api["SEM_SMST_SECURITY_ID"]
    .astype(str)
    .str.strip()
)

api = api.merge(
    universe,
    left_on="SEM_SMST_SECURITY_ID",
    right_on="SecurityID",
    how="inner"
)

master_lookup = {}
for _, row in master.iterrows():
    key = normalize(row["CompanyName"])
    master_lookup[key] = row

matches = []
matched = 0

for _, row in api.iterrows():
    company = normalize(row["SEM_CUSTOM_SYMBOL"])
    if company in master_lookup:
        m = master_lookup[company]
        
        if matched < 20:
            print(
                row["SEM_TRADING_SYMBOL"],
                "->",
                m["Symbol"]
            )

        matches.append({
            "SecurityID": row["SEM_SMST_SECURITY_ID"],
            "DhanSymbol": row["SEM_TRADING_SYMBOL"],
            "MasterSymbol": m["Symbol"],
            "CompanyName": m["CompanyName"],
            "Sector": m["Sector"],
            "Industry": m["Industry"]
        })
        matched += 1

print()
print("API Universe :", len(api))
print("Master Stocks:", len(master))

print()
print(f"Company Matches : {matched}")

pd.DataFrame(matches).to_csv(
    "Masterdata/company_matches.csv",
    index=False
)

print("Saved : Masterdata/company_matches.csv")