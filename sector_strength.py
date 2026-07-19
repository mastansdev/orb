import pandas as pd

MARKET_DATABASE = "data/market_database.csv"


class SectorStrength:

    def __init__(self):

        df = pd.read_csv(MARKET_DATABASE)

        df = df.dropna(subset=["Sector"])
        df = df[df["Sector"] != ""]

        self.symbol_to_sector = {}
        self.prev_close = {}

        self.sectors = {}

        for _, row in df.iterrows():

            symbol = str(row["Symbol"]).strip()
            sector = str(row["Sector"]).strip()

            self.symbol_to_sector[symbol] = sector

            previous_close = None

            for col in (
                "PreviousClose",
                "Previous Close",
                "PrevClose",
                "Prev_Close",
                "Close",
            ):
                if col in row.index and pd.notna(row[col]):
                    previous_close = float(row[col])
                    break

            self.prev_close[symbol] = previous_close

            self.sectors.setdefault(
                sector,
                {
                    "stocks": {},
                    "green": 0,
                    "red": 0,
                    "neutral": 0,
                    "participation": 0.0,
                    "average_change": 0.0,
                    "leader": None,
                    "leader_change": -999,
                    "laggard": None,
                    "laggard_change": 999,
                    "status": "UNKNOWN",
                },
            )

            self.sectors[sector]["stocks"][symbol] = {
                "ltp": None,
                "change": 0.0,
            }

    # --------------------------------------------------

    def update(self, symbol, ltp):

        if symbol not in self.symbol_to_sector:
            return

        previous_close = self.prev_close.get(symbol)

        if previous_close is None or previous_close <= 0:
            return

        sector = self.symbol_to_sector[symbol]

        change = ((ltp - previous_close) / previous_close) * 100

        self.sectors[sector]["stocks"][symbol]["ltp"] = ltp
        self.sectors[sector]["stocks"][symbol]["change"] = change

        self._recalculate_sector(sector)

    # --------------------------------------------------

    def _recalculate_sector(self, sector):

        data = self.sectors[sector]

        green = 0
        red = 0
        neutral = 0

        total_change = 0.0
        updated = 0

        leader = None
        leader_change = -999

        laggard = None
        laggard_change = 999

        for symbol, stock in data["stocks"].items():

            if stock["ltp"] is None:
                continue

            updated += 1

            change = stock["change"]

            total_change += change

            if change > 0:
                green += 1
            elif change < 0:
                red += 1
            else:
                neutral += 1

            if change > leader_change:
                leader_change = change
                leader = symbol

            if change < laggard_change:
                laggard_change = change
                laggard = symbol

        if updated == 0:
            return

        participation = (green / updated) * 100
        average_change = total_change / updated

        data["green"] = green
        data["red"] = red
        data["neutral"] = neutral

        data["participation"] = round(participation, 2)
        data["average_change"] = round(average_change, 2)

        data["leader"] = leader
        data["leader_change"] = round(leader_change, 2)

        data["laggard"] = laggard
        data["laggard_change"] = round(laggard_change, 2)

        if participation >= 70 and average_change > 0:
            data["status"] = "STRONG"
        else:
            data["status"] = "WEAK"

    # --------------------------------------------------

    def get_sector(self, symbol):

        return self.symbol_to_sector.get(symbol)

    # --------------------------------------------------

    def get_sector_data(self, symbol):

        sector = self.get_sector(symbol)

        if sector is None:
            return None

        return self.sectors.get(sector)

    # --------------------------------------------------

    def is_sector_strong(self, symbol):

        sector = self.get_sector(symbol)

        if sector is None:
            return False

        return self.sectors[sector]["status"] == "STRONG"

    # --------------------------------------------------

    def rankings(self):

        ranking = []

        for sector, data in self.sectors.items():

            ranking.append(
                (
                    sector,
                    data["participation"],
                    data["average_change"],
                    data["status"],
                )
            )

        ranking.sort(key=lambda x: (x[1], x[2]), reverse=True)

        return ranking

    # --------------------------------------------------

    def print_rankings(self, top=10):

        print("\n========== SECTOR STRENGTH ==========")

        ranking = self.rankings()[:top]

        for sector, participation, avg_change, status in ranking:

            print(
                f"{sector:<25}"
                f"{participation:>6.1f}%   "
                f"{avg_change:>7.2f}%   "
                f"{status}"
            )

        print("=====================================\n")