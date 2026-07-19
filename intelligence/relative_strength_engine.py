from typing import Dict, Any, Optional

from core.master_loader import master_loader


class RelativeStrengthEngine:

    def __init__(self):

        self.relative_strength: Dict[str, Dict[str, Any]] = {}

        self._initialize()

    # --------------------------------------------------

    def _get_default_data(self):

        return {

            "status": "UNKNOWN",

            "score": 0,

            "vs_nifty": 0.0,

            "vs_sector": 0.0,

            "vs_industry": 0.0,

            "ltp": 0.0,

            "change": 0.0,

            "rank": None,

            "percentile": None,

            "is_leader": False,

            "last_update": None,
                        

        }

    # --------------------------------------------------

    def _initialize(self):

        for raw_symbol in master_loader.get_all_symbols():

            symbol = str(raw_symbol).strip().upper()

            self.relative_strength[symbol] = self._get_default_data()

        print("\n========================================")
        print("RELATIVE STRENGTH ENGINE INITIALIZED")
        print("========================================")
        print(f"Stocks Loaded : {len(self.relative_strength)}")
        print("========================================")

    # --------------------------------------------------

    def update(
        self,
        symbol,
        ltp=None,
        change=None
    ):

        symbol = str(symbol).strip().upper()

        if symbol not in self.relative_strength:
            return

        data = self.relative_strength[symbol]

        if change is not None:
            data["change"] = float(change)

        if ltp is not None:
            data["ltp"] = float(ltp)

        self._update_rankings()

    # --------------------------------------------------

    def _update_rankings(self):

        # ---------------------------------
        # Sector Relative Strength
        # ---------------------------------

        for symbol, data in self.relative_strength.items():

            sector = master_loader.get_sector(symbol)

            if not sector:
                continue

            sector_symbols = master_loader.get_sector_symbols(
                sector
            )

            if not sector_symbols:
                continue

            total_change = 0.0
            valid_stocks = 0

            for peer in sector_symbols:

                peer_data = self.relative_strength.get(peer)

                if peer_data is None:
                    continue

                total_change += peer_data["change"]
                valid_stocks += 1

            if valid_stocks == 0:
                continue

            sector_average = (
                total_change / valid_stocks
            )

            data["vs_sector"] = (
                data["change"] - sector_average
            )

        # ---------------------------------
        # Industry Relative Strength
        # ---------------------------------

        for symbol, data in self.relative_strength.items():

            industry = master_loader.get_industry(symbol)

            if not industry:
                continue

            industry_symbols = master_loader.get_industry_symbols(
                industry
            )

            if not industry_symbols:
                continue

            total_change = 0.0
            valid_stocks = 0

            for peer in industry_symbols:

                peer_data = self.relative_strength.get(peer)

                if peer_data is None:
                    continue

                total_change += peer_data["change"]
                valid_stocks += 1

            if valid_stocks == 0:
                continue

            industry_average = (
                total_change / valid_stocks
            )

            data["vs_industry"] = (
                data["change"] - industry_average
            )

        # ---------------------------------
        # Combined Relative Strength Score
        # ---------------------------------

        for data in self.relative_strength.values():

            data["score"] = (

                data["vs_sector"]

                +

                data["vs_industry"]

            ) / 2

        # ---------------------------------
        # Relative Strength Ranking
        # ---------------------------------

        ranked_stocks = sorted(

            self.relative_strength.items(),

            key=lambda item: item[1]["score"],

            reverse=True

        )

        for rank, (symbol, data) in enumerate(

            ranked_stocks,

            start=1

        ):

            data["rank"] = rank

        # ---------------------------------
        # Relative Strength Percentile
        # ---------------------------------

        total_stocks = len(ranked_stocks)

        for data in self.relative_strength.values():

            if data["rank"] is None:
                continue

            data["percentile"] = (

                (total_stocks - data["rank"] + 1)

                / total_stocks

            ) * 100

        # ---------------------------------
        # Leader Detection
        # ---------------------------------

        for data in self.relative_strength.values():

            data["is_leader"] = (
                data["percentile"] >= 95
            )

        # ---------------------------------
        # Relative Strength Status
        # ---------------------------------

        for data in self.relative_strength.values():

            if data["percentile"] >= 95:

                data["status"] = "STRONG"

            elif data["percentile"] >= 50:

                data["status"] = "NEUTRAL"

            else:

                data["status"] = "WEAK"

    # --------------------------------------------------

    def get_snapshot(self, symbol):

        symbol = str(symbol).strip().upper()

        return {

            "relative_strength":

            self.relative_strength.get(symbol)

        }

    # --------------------------------------------------

    def get(self, symbol):

        symbol = str(symbol).strip().upper()

        return self.relative_strength.get(symbol)

    # --------------------------------------------------

    def reset(self):

        for symbol in self.relative_strength:

            self.relative_strength[symbol] = self._get_default_data()