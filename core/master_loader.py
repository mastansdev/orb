from collections import defaultdict
import re
import pandas as pd

from dhanhq import MarketFeed

MASTER_DATABASE = "Masterdata/master_database.xlsx"


class MasterLoader:

    def __init__(self):
        print("\nLoading Master Database...")

        # Read excel file and ensure everything is treated as a string
        df = pd.read_excel(MASTER_DATABASE, dtype=str).fillna("")

        # Standardize column names (strip, uppercase, and collapse multiple spaces)
        df.columns = (
            df.columns
            .str.strip()
            .str.upper()
            .str.replace(r"\s+", " ", regex=True)
        )

        # 1. Validate required columns exist before processing
        required_columns = [
            "SECURITY ID",
            "SYMBOL",
            "COMPANY NAME",
            "CORE BUSINESS",
            "SECTOR",
            "INDUSTRY",
            "KEYWORDS",
            "FNO",
            "LOT SIZE",
            "THEMES",
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing Columns : {missing}")

        # Clean string spaces uniformly across the dataframe
        for col in df.columns:
            df[col] = df[col].str.strip()

        # Enforce uppercase format for all symbols
        df["SYMBOL"] = df["SYMBOL"].str.upper()

        # 2. Check for duplicate Symbols
        if df["SYMBOL"].duplicated().any():
            duplicates = df[df["SYMBOL"].duplicated()]["SYMBOL"].tolist()
            raise ValueError(f"Duplicate Symbols Found: {duplicates}")

        # 3. Check for duplicate Security IDs
        if df["SECURITY ID"].duplicated().any():
            duplicates = df[df["SECURITY ID"].duplicated()]["SECURITY ID"].tolist()
            raise ValueError(f"Duplicate Security IDs Found: {duplicates}")

        # Vectorized dictionary generation
        self.security_to_symbol = df.set_index("SECURITY ID")["SYMBOL"].to_dict()
        self.symbol_to_security = df.set_index("SYMBOL")["SECURITY ID"].to_dict()

        self.symbol_to_company = df.set_index("SYMBOL")["COMPANY NAME"].to_dict()
        self.symbol_to_sector = df.set_index("SYMBOL")["SECTOR"].to_dict()
        self.symbol_to_industry = df.set_index("SYMBOL")["INDUSTRY"].to_dict()

        # Core business dictionary
        self.symbol_to_business = (
            df.set_index("SYMBOL")["CORE BUSINESS"].to_dict()
        )

        # Keywords parsing
        self.symbol_to_keywords = {}
        for _, row in df.iterrows():
            keywords = [
                k.strip().upper()
                for k in re.split(r"[|,]", str(row["KEYWORDS"]))
                if k.strip()
            ]
            self.symbol_to_keywords[row["SYMBOL"]] = keywords

        # Themes parsing
        self.symbol_to_themes = {}
        for _, row in df.iterrows():
            themes = [
                theme.strip().upper()
                for theme in str(row["THEMES"]).split("|")
                if theme.strip()
            ]
            self.symbol_to_themes[row["SYMBOL"]] = themes

        # Build Reverse Indexes for O(1) lookups
        self.sector_to_symbols = defaultdict(list)
        self.industry_to_symbols = defaultdict(list)
        self.keyword_to_symbols = defaultdict(list)
        self.theme_to_symbols = defaultdict(list)

        for _, row in df.iterrows():
            symbol = row["SYMBOL"]
            sector = row["SECTOR"]
            industry = row["INDUSTRY"]

            self.sector_to_symbols[sector].append(symbol)
            self.industry_to_symbols[industry].append(symbol)

            for keyword in self.symbol_to_keywords[symbol]:
                self.keyword_to_symbols[keyword].append(symbol)

            for theme in self.symbol_to_themes[symbol]:
                self.theme_to_symbols[theme].append(symbol)

        # Boolean mapping for F&O status
        df["is_fno_bool"] = df["FNO"].str.upper() == "YES"
        self.symbol_to_fno = df.set_index("SYMBOL")["is_fno_bool"].to_dict()

        # Integer mapping for Lot Size
        df["clean_lot"] = pd.to_numeric(df["LOT SIZE"], errors="coerce").fillna(0).astype(int)
        self.symbol_to_lot = df.set_index("SYMBOL")["clean_lot"].to_dict()

        # Pre-calculating metadata metrics
        fno_count = df["is_fno_bool"].sum()
        total_stocks_count = len(self.security_to_symbol)

        # Build Dhan MarketFeed subscription list.
        #
        # Fix (2026-07-21): was MarketFeed.Ticker for all 750
        # stocks -- Ticker mode is LTP-only, so the live bot has
        # NEVER had real-time volume data, at all, for anything.
        # Confirmed via a live diagnostic run today
        # (tests/Test_premarket_feed.py, see
        # premarket_feed_test_20260721_085953.log): Quote mode
        # carries volume/total_buy_quantity/total_sell_quantity
        # plus OHLC, and is also what reveals the genuine
        # pre-open discovered price (see
        # intelligence/premarket_snapshot.py). Switched to Quote
        # for the whole universe -- still one field per
        # instrument tuple, same subscription mechanics, just a
        # richer packet per tick.
        self.instruments = [
            (
                MarketFeed.NSE,
                security_id,
                MarketFeed.Quote
            )
            for security_id in df["SECURITY ID"]
        ]
            
        print("=" * 45)
        print("MASTER DATABASE LOADED (v2)")
        print("=" * 45)
        print(f"Stocks Loaded : {total_stocks_count}")
        print(f"F&O Stocks    : {fno_count}")
        print(f"Cash Stocks   : {total_stocks_count - fno_count}")
        print(f"Sectors       : {df['SECTOR'].nunique()}")
        print(f"Industries    : {df['INDUSTRY'].nunique()}")
        print(f"Themes        : {len(self.theme_to_symbols)}")
        print("=" * 45)

    # --------------------------------------------------

    def get_symbol(self, security_id):
        return self.security_to_symbol.get(str(security_id).strip())

    # --------------------------------------------------

    def get_security_id(self, symbol):
        symbol = str(symbol).strip().upper()
        return self.symbol_to_security.get(symbol)

    # --------------------------------------------------

    def get_company_name(self, symbol):
        symbol = str(symbol).strip().upper()
        return self.symbol_to_company.get(symbol)

    # --------------------------------------------------

    def get_sector(self, symbol):
        symbol = str(symbol).strip().upper()
        return self.symbol_to_sector.get(symbol)

    # --------------------------------------------------

    def get_industry(self, symbol):
        symbol = str(symbol).strip().upper()
        return self.symbol_to_industry.get(symbol)

    # --------------------------------------------------

    def get_core_business(self, symbol):
        symbol = str(symbol).strip().upper()
        return self.symbol_to_business.get(symbol, "")

    # --------------------------------------------------

    def get_keywords(self, symbol):
        symbol = str(symbol).strip().upper()
        return self.symbol_to_keywords.get(symbol, [])

    # --------------------------------------------------

    def get_themes(self, symbol):
        symbol = str(symbol).strip().upper()
        return self.symbol_to_themes.get(symbol, [])

    # --------------------------------------------------

    def get_sector_symbols(self, sector):
        return self.sector_to_symbols.get(sector, [])

    # --------------------------------------------------

    def get_industry_symbols(self, industry):
        return self.industry_to_symbols.get(industry, [])

    # --------------------------------------------------

    def get_theme_symbols(self, theme):
        theme = str(theme).strip().upper()
        return self.theme_to_symbols.get(theme, [])

    # --------------------------------------------------

    def search_keyword(self, keyword):
        keyword = str(keyword).strip().upper()
        return self.keyword_to_symbols.get(keyword, [])

    # --------------------------------------------------

    def get_peer_stocks(self, symbol):
        industry = self.get_industry(symbol)
        if not industry:
            return []
        peers = self.get_industry_symbols(industry)
        return [s for s in peers if s != symbol]

    # --------------------------------------------------

    def is_fno(self, symbol):
        symbol = str(symbol).strip().upper()
        return self.symbol_to_fno.get(symbol, False)

    # --------------------------------------------------

    def get_lot_size(self, symbol):
        symbol = str(symbol).strip().upper()
        return self.symbol_to_lot.get(symbol, 0)

    # --------------------------------------------------

    def has_symbol(self, symbol):
        symbol = str(symbol).strip().upper()
        return symbol in self.symbol_to_security

    # --------------------------------------------------

    def has_security_id(self, security_id):
        security_id = str(security_id).strip()
        return security_id in self.security_to_symbol

    # --------------------------------------------------

    def total_stocks(self):
        return len(self.security_to_symbol)

    # --------------------------------------------------

    def total_sectors(self):
        return len(self.sector_to_symbols)

    # --------------------------------------------------

    def total_industries(self):
        return len(self.industry_to_symbols)

    # --------------------------------------------------

    def total_themes(self):
        return len(self.theme_to_symbols)

    # --------------------------------------------------

    def get_stock_profile(self, symbol):
        symbol = str(symbol).strip().upper()
        return {
            "security_id": self.get_security_id(symbol),
            "symbol": symbol,
            "company": self.get_company_name(symbol),
            "sector": self.get_sector(symbol),
            "industry": self.get_industry(symbol),
            "core_business": self.get_core_business(symbol),
            "keywords": self.get_keywords(symbol),
            "themes": self.get_themes(symbol),
            "fno": self.is_fno(symbol),
            "lot_size": self.get_lot_size(symbol),
        }

    # --------------------------------------------------

    def get_all_symbols(self):
        return list(self.symbol_to_security.keys())

    # --------------------------------------------------

    def get_all_security_ids(self):
        return list(self.security_to_symbol.keys())

    # --------------------------------------------------

    def get_all_instruments(self):
        return self.instruments


# --------------------------------------------------
# Singleton Instance Initialization
# --------------------------------------------------
master_loader = MasterLoader()