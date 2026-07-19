"""
SECTOR ENGINE

Status : STABLE
Architecture : STANDALONE

Responsibilities
----------------
- Track sector breadth
- Track participation
- Track leaders / laggards
- Maintain sector rankings

Does NOT
---------
- Read Excel
- Read CSV
- Execute trades
- Manage capital

Dependencies
------------
MasterLoader
PriceEngine (Integration Phase)
"""

from master_loader import master_loader


class SectorEngine:

    def __init__(self):

        self.sectors = {}

        self.rankings = []

        self._initialize()

    # --------------------------------------------------

    def _initialize(self):

        stock_count = 0

        for symbol in master_loader.get_all_symbols():

            sector = master_loader.get_sector(symbol)

            if not sector:
                continue

            if sector not in self.sectors:

                self.sectors[sector] = {

                    "stocks": {},

                    "green": 0,
                    "red": 0,
                    "neutral": 0,

                    "updated": 0,

                    "participation": 0.0,
                    "average_change": 0.0,

                    "leader": None,
                    "leader_change": 0.0,

                    "laggard": None,
                    "laggard_change": 0.0,

                    "rank": 0,

                    "status": "UNKNOWN"

                }

            self.sectors[sector]["stocks"][symbol] = {

                "ltp": None,
                "change": 0.0

            }

            stock_count += 1

        self._update_rankings()

        print("\n========================================")
        print("SECTOR ENGINE INITIALIZED")
        print("========================================")
        print(f"Sectors Loaded : {len(self.sectors)}")
        print(f"Stocks Loaded  : {stock_count}")
        print("========================================")

    # --------------------------------------------------

    def update(self, symbol, ltp, change):
        # DEBUG ONLY
        # print(f"SECTOR UPDATE -> {symbol}  Change={change}")

        sector = master_loader.get_sector(symbol)

        if sector is None:
            return

        if sector not in self.sectors:
            return

        stocks = self.sectors[sector]["stocks"]

        if symbol not in stocks:
            return

        stock = stocks[symbol]

        # ----------------------------------------
        # Manage previous state counters if updated before
        # ----------------------------------------

        if stock["ltp"] is not None:

            previous_change = stock["change"]

            if previous_change > 0:
                self.sectors[sector]["green"] -= 1

            elif previous_change < 0:
                self.sectors[sector]["red"] -= 1

            else:
                self.sectors[sector]["neutral"] -= 1

        # ----------------------------------------
        # Store latest values
        # ----------------------------------------

        stock["ltp"] = ltp
        stock["change"] = change

        # ----------------------------------------
        # Update counters
        # ----------------------------------------

        if change > 0:

            self.sectors[sector]["green"] += 1

        elif change < 0:

            self.sectors[sector]["red"] += 1

        else:

            self.sectors[sector]["neutral"] += 1

        # ----------------------------------------
        # Refresh sector calculations
        # ----------------------------------------

        self._recalculate_sector(sector)

    # --------------------------------------------------

    def _recalculate_sector(self, sector):

        data = self.sectors[sector]

        total_change = 0.0

        leader = None
        leader_change = float("-inf")

        laggard = None
        laggard_change = float("inf")

        updated = sum(
            1
            for stock in data["stocks"].values()
            if stock["ltp"] is not None
        )

        data["updated"] = updated

        if updated == 0:

            data["average_change"] = 0.0
            data["participation"] = 0.0
            return

        for symbol, stock in data["stocks"].items():

            if stock["ltp"] is None:
                continue

            change = stock["change"]

            total_change += change

            if change > leader_change:

                leader_change = change
                leader = symbol

            if change < laggard_change:

                laggard_change = change
                laggard = symbol

        data["average_change"] = round(
            total_change / updated,
            2
        )

        data["participation"] = round(
            (data["green"] / updated) * 100,
            2
        )

        data["leader"] = leader
        
        data["leader_change"] = (
            round(leader_change, 2)
            if leader is not None
            else 0.0
        )

        data["laggard"] = laggard
        
        data["laggard_change"] = (
            round(laggard_change, 2)
            if laggard is not None
            else 0.0
        )

        self._update_status(sector)

        self._update_rankings()

    # --------------------------------------------------

    def _update_status(self, sector):

        data = self.sectors[sector]

        participation = data["participation"]
        average_change = data["average_change"]

        # Updated evaluation criteria for sector strength thresholds
        if average_change >= 1.0 and participation >= 60:

            data["status"] = "STRONG"

        elif average_change <= -1.0 and participation <= 40:

            data["status"] = "WEAK"

        else:

            data["status"] = "NEUTRAL"

    # --------------------------------------------------

    def _update_rankings(self):

        self.rankings = sorted(

            self.sectors.items(),

            key=lambda x: (

                x[1]["average_change"],

                x[1]["participation"],

                x[1]["updated"]

            ),

            reverse=True

        )

        for rank, (sector, data) in enumerate(self.rankings, start=1):

            data["rank"] = rank

    # --------------------------------------------------

    def get_stock_data(self, symbol):

        sector = master_loader.get_sector(symbol)

        if sector is None:
            return None

        return self.sectors[sector]["stocks"].get(symbol)

    # --------------------------------------------------

    def get_sector_stocks(self, sector):

        data = self.sectors.get(sector)

        if data is None:
            return {}

        return data["stocks"]

    # --------------------------------------------------

    def get_sector_summary(self, sector):

        data = self.sectors.get(sector)

        if data is None:
            return None

        return {

            "green": data["green"],

            "red": data["red"],

            "neutral": data["neutral"],

            "updated": data["updated"],

            "participation": data["participation"],

            "average_change": data["average_change"],

            "leader": data["leader"],

            "leader_change": data["leader_change"],

            "laggard": data["laggard"],

            "laggard_change": data["laggard_change"],

            "rank": data["rank"],

            "status": data["status"]

        }

    # --------------------------------------------------

    def get_sector_statistics(self, sector):

        return self.sectors.get(sector)

    # --------------------------------------------------

    def get_sector(self, symbol):

        return master_loader.get_sector(symbol)

    # --------------------------------------------------

    def get_rankings(self):

        return self.rankings

    # --------------------------------------------------

    def get_top_sectors(self, limit=10):

        return self.rankings[:limit]

    # --------------------------------------------------

    def get_bottom_sectors(self, limit=10):

        return list(reversed(self.rankings[-limit:]))

    # --------------------------------------------------

    def is_sector_strong(self, sector):

        data = self.sectors.get(sector)

        if data is None:
            return False

        return data["status"] == "STRONG"

    # --------------------------------------------------

    def print_rankings(self):

        pass

    # --------------------------------------------------

    def get_snapshot(self, symbol):

        sector = self.get_sector(symbol)

        if sector is None:

            return {

                "sector": None

            }

        summary = self.get_sector_summary(sector)

        if summary is None:

            return {

                "sector": None

            }

        return {

            "sector": {

                "name": sector,

                "rank": summary["rank"],

                "status": summary["status"],

                "participation": summary["participation"],

                "average_change": summary["average_change"],

                "leader": summary["leader"],

                "leader_change": summary["leader_change"],

                "laggard": summary["laggard"],

                "laggard_change": summary["laggard_change"]

            }

        }