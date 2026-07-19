import re
import pandas as pd

MARKET_DATABASE = "data/market_database.csv"
SECTOR_DATABASE = "Masterdata/sector_database.csv"

OUTPUT_FILE = "Masterdata/symbol_mapping.csv"


def normalize_name(name):
    if pd.isna(name):
        return ""

    name = str(name).upper()
    name = name.replace("&", " AND ")

    words_to_remove = [
        "LIMITED",
        "LTD",
        "LIMITED.",
        "PVT",
        "PRIVATE",
        "COMPANY",
        "CO",
        "CORPORATION",
        "CORP",
        "INDIA",
    ]

    for word in words_to_remove:
        name = name.replace(word, " ")

    name = re.sub(r"[^A-Z0-9 ]", " ", name)
    name = re.sub(r"\s+", " ", name)

    return name.strip()


class SymbolNormalizer:

    def __init__(self):
        self.market = pd.read_csv(MARKET_DATABASE, dtype=str).fillna("")
        self.master = pd.read_csv(SECTOR_DATABASE, dtype=str).fillna("")

        self.market["Symbol"] = (
            self.market["Symbol"].str.strip().str.upper()
        )

        self.market["CompanyName"] = (
            self.market["CompanyName"].str.strip().str.upper()
        )

        self.master["CompanyName"] = (
            self.master["CompanyName"].str.strip().str.upper()
        )

        self.master["Symbol"] = (
            self.master["Symbol"].str.strip().str.upper()
        )

        self.output = []

    # ------------------------------------------------

    def build_exact_matches(self):
        sector_lookup = {}
        for _, row in self.master.iterrows():
            sector_lookup[row["Symbol"]] = row

        company_lookup = {}
        for _, row in self.master.iterrows():
            company_lookup[normalize_name(row["CompanyName"])] = row

        exact = 0
        company_count = 0
        missing = 0

        for _, row in self.market.iterrows():
            symbol = row["Symbol"]

            if symbol in sector_lookup:
                s = sector_lookup[symbol]
                self.output.append({
                    "SecurityID": row["SecurityID"],
                    "DhanSymbol": symbol,
                    "MasterSymbol": s["Symbol"],
                    "CompanyName": row["CompanyName"],
                    "Sector": s["Sector"],
                    "Industry": s["Industry"],
                    "MatchType": "EXACT"
                })
                exact += 1

            else:
                company = normalize_name(row["CompanyName"])

                if company in company_lookup:
                    s = company_lookup[company]
                    self.output.append({
                        "SecurityID": row["SecurityID"],
                        "DhanSymbol": symbol,
                        "MasterSymbol": s["Symbol"],
                        "CompanyName": s["CompanyName"],
                        "Sector": s["Sector"],
                        "Industry": s["Industry"],
                        "MatchType": "COMPANY"
                    })
                    company_count += 1

                else:
                    self.output.append({
                        "SecurityID": row["SecurityID"],
                        "DhanSymbol": symbol,
                        "MasterSymbol": "",
                        "CompanyName": row["CompanyName"],
                        "Sector": "",
                        "Industry": "",
                        "MatchType": "UNMATCHED"
                    })
                    missing += 1

        print()
        print("=" * 60)
        print("SYMBOL MAPPING REPORT")
        print("=" * 60)
        print(f"Universe        : {len(self.market)}")
        print(f"Exact Match     : {exact}")
        print(f"Company Match   : {company_count}")
        print(f"Unmatched       : {missing}")
        print(f"Total Mapped    : {exact + company_count}")

    # ------------------------------------------------

    def save(self):
        pd.DataFrame(self.output).to_csv(OUTPUT_FILE, index=False)
        print()
        print(f"Saved : {OUTPUT_FILE}")


if __name__ == "__main__":
    engine = SymbolNormalizer()
    engine.build_exact_matches()
    engine.save()