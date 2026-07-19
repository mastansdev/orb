from datetime import datetime


class ORBEngine:

    def __init__(self):

        self.orb_data = {}

    # --------------------------------------------------
    # Load ORB from Historical API
    # --------------------------------------------------

    def load_historical_orb(self, security_id, high, low):

        today = datetime.now().strftime("%Y-%m-%d")

        self.orb_data[security_id] = {
            "high": float(high),
            "low": float(low),
            "completed": True,
            "entry_taken": False,
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
                    "entry_taken": False,
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