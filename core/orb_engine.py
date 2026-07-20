from datetime import datetime


class ORBEngine:

    def __init__(self):

        self.orb_data = {}

        # Fix (2026-07-20): re-entry bug -- entry_taken lives on
        # orb_data, which is wiped clean on every restart. Without
        # this, a symbol that already traded (and even closed
        # profitably) today looks freshly eligible again the
        # moment the engine restarts, causing a real duplicate
        # same-day trade (confirmed live: BANKINDIA and BHARATFORG
        # both re-entered this way). This set is populated ONCE at
        # startup via load_already_traded(), from whatever already
        # has a trade today (open or closed) -- BEFORE any ticks
        # start building fresh orb_data entries.
        self.already_traded_today = set()

    # --------------------------------------------------
    # Startup Reconciliation
    # --------------------------------------------------

    def load_already_traded(self, security_ids):
        """
        Called once at startup (or restart) with every security_id
        that already has a trade today -- open or closed -- so a
        fresh orb_data entry for that symbol is born already
        marked entry_taken=True instead of defaulting to False.
        """
        self.already_traded_today = set(security_ids)

    # --------------------------------------------------
    # Load ORB from Historical API
    # --------------------------------------------------

    def load_historical_orb(self, security_id, high, low):

        today = datetime.now().strftime("%Y-%m-%d")

        self.orb_data[security_id] = {
            "high": float(high),
            "low": float(low),
            "completed": True,
            "entry_taken": (
                security_id in self.already_traded_today
            ),
            "date": today
        }

    # --------------------------------------------------
    # Build ORB Live (09:15 - 09:30)
    # --------------------------------------------------

    def update(self, security_id, ltp, ltt):

        today = datetime.now().strftime("%Y-%m-%d")

        if security_id in self.orb_data:

            if self.orb_data[security_id]["date"] != today:
                del self.orb_data[security_id]

        hour = int(ltt[0:2])
        minute = int(ltt[3:5])

        if hour < 9 or (hour == 9 and minute < 15):
            return

        if security_id not in self.orb_data:

            if hour == 9 and 15 <= minute <= 29:

                self.orb_data[security_id] = {
                    "high": ltp,
                    "low": ltp,
                    "completed": False,
                    "entry_taken": (
                        security_id in self.already_traded_today
                    ),
                    "date": today
                }

            return

        orb = self.orb_data[security_id]

        if orb["completed"]:
            return

        if hour == 9 and 15 <= minute <= 29:

            if ltp > orb["high"]:
                orb["high"] = ltp

            if ltp < orb["low"]:
                orb["low"] = ltp

        elif hour > 9 or (hour == 9 and minute >= 30):

            orb["completed"] = True

    # --------------------------------------------------

    def get_orb(self, security_id):

        return self.orb_data.get(security_id)

    # --------------------------------------------------

    def set_entry_taken(self, security_id):

        orb = self.orb_data.get(security_id)

        if orb:
            orb["entry_taken"] = True

    # --------------------------------------------------

    def completed_count(self):

        return sum(
            1
            for orb in self.orb_data.values()
            if orb["completed"]
        )