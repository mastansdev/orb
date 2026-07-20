"""
==========================================================
Symbol Matcher
==========================================================

Mission
-------
Match news headlines/descriptions against the stock
universe (Masterdata/master_database.xlsx) to identify
which specific stock symbols a news item affects.

This is intentionally lightweight and has NO dependency
on dhanhq or anything Dhan-related, since this module is
used by the News Intelligence service, which must stay
fully decoupled from the trading/broker layer.

Responsibilities
----------------
1. Load SYMBOL, COMPANY NAME, KEYWORDS from the master
   stock database
2. Build a reverse keyword -> symbol index
3. Match free text against that index using word-boundary
   matching to avoid partial-word false positives
   (e.g. "SBI" should not match inside an unrelated word)

Does NOT
--------
- Classify news
- Score news
- Trade
- Touch Dhan in any way

Author : H&M ORB AUTO TRADER
==========================================================
"""

import re
from collections import defaultdict

import pandas as pd

MASTER_DATABASE = "Masterdata/master_database.xlsx"

# --------------------------------------------------
# Exchange-name blacklist
#
# "BSE" is both a stock ticker (BSE Ltd, the exchange operator)
# and the near-universal way news/regulatory text refers to the
# trading VENUE ("dealing in Illiquid Stock Options on BSE",
# "listed on BSE", etc.). The venue usage vastly outnumbers
# genuine BSE-Ltd-the-company news, and because BSE Ltd's own
# company name collapses to "BSE" after stripping LIMITED/LTD,
# there's no clean textual way to tell the two apart. Rather than
# let every venue mention register as a false symbol match, we
# blacklist these bare exchange-name keywords entirely. NSE isn't
# itself listed, so it should never resolve to a symbol anyway --
# blacklisting it here is just a safety net in case it's present
# in the KEYWORDS column for some other row.
# --------------------------------------------------
BLACKLISTED_KEYWORDS = {"BSE", "NSE"}


class SymbolMatcher:

    def __init__(self):
        print("\n[SYMBOL MATCHER] Loading stock universe...")

        df = pd.read_excel(
            MASTER_DATABASE,
            dtype=str,
            usecols=["SYMBOL", "COMPANY NAME", "KEYWORDS"],
        ).fillna("")

        df.columns = (
            df.columns
            .str.strip()
            .str.upper()
        )

        for col in df.columns:
            df[col] = df[col].str.strip()

        df["SYMBOL"] = df["SYMBOL"].str.upper()

        # --------------------------------------------------
        # Build keyword -> [symbols] reverse index
        # --------------------------------------------------
        self.keyword_to_symbols = defaultdict(list)

        for _, row in df.iterrows():
            symbol = row["SYMBOL"]

            keywords = [
                k.strip().upper()
                for k in re.split(r"[|,]", row["KEYWORDS"])
                if k.strip()
            ]

            # Always include the symbol itself and the company
            # name as implicit keywords, in addition to whatever
            # is explicitly listed in the KEYWORDS column.
            keywords.append(symbol)

            company_name = row["COMPANY NAME"].upper()
            company_name_clean = re.sub(
                r"\b(LIMITED|LTD)\.?\b", "", company_name
            ).strip()
            if company_name_clean:
                keywords.append(company_name_clean)

            for keyword in set(keywords):
                if keyword in BLACKLISTED_KEYWORDS:
                    continue
                if keyword and symbol not in self.keyword_to_symbols[keyword]:
                    self.keyword_to_symbols[keyword].append(symbol)

        # Sort keywords longest-first so multi-word company names
        # get checked before short, more ambiguous keywords.
        self._sorted_keywords = sorted(
            self.keyword_to_symbols.keys(),
            key=len,
            reverse=True,
        )

        print(
            f"[SYMBOL MATCHER] Loaded {len(df)} stocks, "
            f"{len(self.keyword_to_symbols)} unique keywords"
        )

    # --------------------------------------------------

    def match(self, text):
        """
        Return the list of stock symbols whose keywords
        appear (as whole words) in the given text.
        """
        if not text:
            return []

        text_upper = text.upper()
        matched_symbols = []

        for keyword in self._sorted_keywords:
            # Word-boundary match avoids "SBI" matching inside
            # an unrelated longer word.
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, text_upper):
                for symbol in self.keyword_to_symbols[keyword]:
                    if symbol not in matched_symbols:
                        matched_symbols.append(symbol)

        return matched_symbols


# --------------------------------------------------
# Singleton instance
# --------------------------------------------------
symbol_matcher = SymbolMatcher()