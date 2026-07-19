from core.master_loader import master_loader


class IndustryEngine:

    def __init__(self):
        self.industries = {}
        self.rankings = []
        self._initialize()

    # --------------------------------------------------
    def _initialize(self):
        stock_count = 0
        for symbol in master_loader.get_all_symbols():
            industry = master_loader.get_industry(symbol)
            if not industry:
                continue

            if industry not in self.industries:
                self.industries[industry] = {
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

            self.industries[industry]["stocks"][symbol] = {
                "ltp": None,
                "change": 0.0
            }
            stock_count += 1

        self._update_rankings()

        print("\n========================================")
        print("INDUSTRY ENGINE INITIALIZED")
        print("========================================")
        print(f"Industries Loaded : {len(self.industries)}")
        print(f"Stocks Loaded     : {stock_count}")
        print("========================================")

    # --------------------------------------------------
    def update(self, symbol, ltp, change):
        industry = master_loader.get_industry(symbol)
        if industry is None or industry not in self.industries:
            return

        stocks = self.industries[industry]["stocks"]
        if symbol not in stocks:
            return

        stock = stocks[symbol]

        # Remove previous state if it was already updated
        if stock["ltp"] is not None:
            previous_change = stock["change"]
            if previous_change > 0:
                self.industries[industry]["green"] -= 1
            elif previous_change < 0:
                self.industries[industry]["red"] -= 1
            else:
                self.industries[industry]["neutral"] -= 1

        # Store latest values
        stock["ltp"] = ltp
        stock["change"] = change

        # Update counters
        if change > 0:
            self.industries[industry]["green"] += 1
        elif change < 0:
            self.industries[industry]["red"] += 1
        else:
            self.industries[industry]["neutral"] += 1

        self._recalculate_industry(industry)

    # --------------------------------------------------
    def _recalculate_industry(self, industry):
        data = self.industries[industry]
        total_change = 0.0
        leader = None
        leader_change = float("-inf")
        laggard = None
        laggard_change = float("inf")

        updated = sum(
            1 for stock in data["stocks"].values() if stock["ltp"] is not None
        )
        data["updated"] = updated

        if updated == 0:
            data["average_change"] = 0.0
            data["participation"] = 0.0
            data["leader"] = None
            data["leader_change"] = 0.0
            data["laggard"] = None
            data["laggard_change"] = 0.0
            data["status"] = "UNKNOWN"
            self._update_rankings()
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

        data["average_change"] = round(total_change / updated, 2)
        data["participation"] = round((data["green"] / updated) * 100, 2)
        data["leader"] = leader
        data["leader_change"] = round(leader_change, 2) if leader is not None else 0.0
        data["laggard"] = laggard
        data["laggard_change"] = round(laggard_change, 2) if laggard is not None else 0.0

        # Industry Status Assignment
        if data["participation"] >= 70 and data["average_change"] > 0:
            data["status"] = "STRONG"
        elif data["participation"] <= 30 and data["average_change"] < 0:
            data["status"] = "WEAK"
        else:
            data["status"] = "NEUTRAL"

        self._update_rankings()

    # --------------------------------------------------
    def _update_rankings(self):
        self.rankings = sorted(
            self.industries.items(),
            key=lambda x: (
                x[1]["average_change"],
                x[1]["participation"],
                x[1]["updated"]
            ),
            reverse=True
        )

        for rank, (industry, data) in enumerate(self.rankings, start=1):
            data["rank"] = rank

    # --------------------------------------------------
    def get_stock_data(self, symbol):
        industry = master_loader.get_industry(symbol)
        if industry is None:
            return None
        return self.industries[industry]["stocks"].get(symbol)

    # --------------------------------------------------
    def get_industry_stocks(self, industry):
        data = self.industries.get(industry)
        return data["stocks"] if data is not None else {}

    # --------------------------------------------------
    def get_industry_summary(self, industry):
        data = self.industries.get(industry)
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
    def get_snapshot(self, symbol):
        industry = self.get_industry(symbol)
        if industry is None:
            return {
                "industry": None
            }

        summary = self.get_industry_summary(industry)
        if summary is None:
            return {
                "industry": None
            }

        return {
            "industry": {
                "name": industry,
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

    # --------------------------------------------------
    def get_industry_statistics(self, industry):
        return self.industries.get(industry)

    # --------------------------------------------------
    def get_industry(self, symbol):
        return master_loader.get_industry(symbol)

    # --------------------------------------------------
    def get_industry_data(self, industry):
        return self.industries.get(industry)

    # --------------------------------------------------
    def get_rankings(self):
        return self.rankings

    # --------------------------------------------------
    def get_top_industries(self, limit=10):
        return self.rankings[:limit]

    # --------------------------------------------------
    def get_bottom_industries(self, limit=10):
        return list(reversed(self.rankings[-limit:]))

    # --------------------------------------------------
    def is_industry_strong(self, industry):
        data = self.industries.get(industry)
        return data["status"] == "STRONG" if data is not None else False

    # --------------------------------------------------
    def print_rankings(self):
        rankings = self.get_rankings()

        print("\n")
        print("=" * 90)
        print("                    INDUSTRY RANKINGS")
        print("=" * 90)
        print(
            f"{'Rank':<6}"
            f"{'Industry':<35}"
            f"{'Avg %':>10}"
            f"{'Part %':>10}"
            f"{'Status':>12}"
        )
        print("-" * 90)

        for rank, (industry, data) in enumerate(rankings, start=1):
            print(
                f"{rank:<6}"
                f"{industry:<35}"
                f"{data['average_change']:>10.2f}"
                f"{data['participation']:>10.2f}"
                f"{data['status']:>12}"
            )

        print("=" * 90)