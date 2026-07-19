"""
THEME ENGINE

Status : STABLE
Architecture : STANDALONE

Responsibilities
----------------
- Track theme breadth
- Track participation
- Track leaders / laggards
- Maintain theme rankings

Does NOT
---------
- Read Excel
- Execute trades
- Manage capital
- Read news
- Read results

Dependencies
------------
MasterLoader
"""

from master_loader import master_loader


class ThemeEngine:

    def __init__(self):

        self.themes = {}

        self.rankings = []

        self._initialize()

    # --------------------------------------------------

    def _initialize(self):

        stock_count = 0

        for symbol in master_loader.get_all_symbols():

            themes = master_loader.get_themes(symbol)

            if not themes:
                continue

            for theme in themes:

                if theme not in self.themes:

                    self.themes[theme] = {

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

                self.themes[theme]["stocks"][symbol] = {

                    "ltp": None,
                    "change": 0.0

                }

                stock_count += 1

        self._update_rankings()

        print("\n========================================")
        print("THEME ENGINE INITIALIZED")
        print("========================================")
        print(f"Themes Loaded : {len(self.themes)}")
        print(f"Stock Entries : {stock_count}")
        print("========================================")

    # --------------------------------------------------

    def _update_rankings(self):

        self.rankings = sorted(

            self.themes.items(),

            key=lambda x: (

                x[1]["average_change"],

                x[1]["participation"],

                x[1]["updated"]

            ),

            reverse=True

        )

        for rank, (theme, data) in enumerate(self.rankings, start=1):

            data["rank"] = rank

    # --------------------------------------------------

    def _update_status(self, theme):

        data = self.themes[theme]

        participation = data["participation"]
        average_change = data["average_change"]

        if participation >= 70 and average_change > 0:

            data["status"] = "STRONG"

        elif participation <= 30 and average_change < 0:

            data["status"] = "WEAK"

        else:

            data["status"] = "NEUTRAL"

    # --------------------------------------------------

    def _recalculate_theme(self, theme):

        data = self.themes[theme]

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

        self._update_status(theme)

        self._update_rankings()

    # --------------------------------------------------

    def update(self, symbol, ltp, change):

        themes = master_loader.get_themes(symbol)

        if not themes:
            return

        for theme in themes:

            if theme not in self.themes:
                continue

            stocks = self.themes[theme]["stocks"]

            if symbol not in stocks:
                continue

            stock = stocks[symbol]

            # ----------------------------------------
            # Remove previous state counters
            # ----------------------------------------

            if stock["ltp"] is not None:

                previous_change = stock["change"]

                if previous_change > 0:

                    self.themes[theme]["green"] -= 1

                elif previous_change < 0:

                    self.themes[theme]["red"] -= 1

                else:

                    self.themes[theme]["neutral"] -= 1

            # ----------------------------------------
            # Store latest values
            # ----------------------------------------

            stock["ltp"] = ltp

            stock["change"] = change

            # ----------------------------------------
            # Update counters
            # ----------------------------------------

            if change > 0:

                self.themes[theme]["green"] += 1

            elif change < 0:

                self.themes[theme]["red"] += 1

            else:

                self.themes[theme]["neutral"] += 1

            self._recalculate_theme(theme)

    # --------------------------------------------------

    def get_theme_summary(self, theme):

        data = self.themes.get(theme)

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

    def get_theme_statistics(self, theme):

        return self.themes.get(theme)

    # --------------------------------------------------

    def get_theme(self, symbol):

        return master_loader.get_themes(symbol)

    # --------------------------------------------------

    def get_rankings(self):

        return self.rankings

    # --------------------------------------------------

    def get_top_themes(self, limit=10):

        return self.rankings[:limit]

    # --------------------------------------------------

    def get_bottom_themes(self, limit=10):

        return list(reversed(self.rankings[-limit:]))

    # --------------------------------------------------

    def is_theme_strong(self, theme):

        data = self.themes.get(theme)

        if data is None:
            return False

        return data["status"] == "STRONG"

    # --------------------------------------------------

    def get_snapshot(self, symbol):

        themes = master_loader.get_themes(symbol)

        snapshots = []

        for theme in themes:

            summary = self.get_theme_summary(theme)

            if summary is None:
                continue

            snapshots.append(

                {

                    "name": theme,

                    **summary

                }

            )

        return {

            "theme": snapshots

        }