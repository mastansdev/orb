from config import ENTRY_BUFFER, MAX_BREAKOUT_PERCENT


class Strategy:

    def is_buy_signal(self, ltp, orb, current_time):

        if orb is None:
            return False

        if not orb["completed"]:
            return False

        if orb["entry_taken"]:
            return False

        if current_time >= "15:00:00":
            return False

        if orb["high"] <= orb["low"]:
            return False

        breakout_price = orb["high"] + ENTRY_BUFFER

        if ltp < breakout_price:
            return False

        breakout_percent = (
            (ltp - orb["high"]) / orb["high"]
        ) * 100

        if breakout_percent > MAX_BREAKOUT_PERCENT:
            return False

        return True