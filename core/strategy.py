from config import (
    ENTRY_BUFFER_PCT,
    MAX_BREAKOUT_PERCENT,
    ENTRY_CUTOFF_TIME,
)


class Strategy:

    def is_buy_signal(self, orb, current_time, last_closed_candle):
        """
        Entry signal now requires a CLOSED 1-minute candle above the
        ORB high + percentage buffer — not a single live tick touch.
        This filters out single-tick wick/fakeout entries.
        """

        if orb is None:
            return False

        if not orb["completed"]:
            return False

        if orb["entry_taken"]:
            return False

        # Global entry cutoff (MIS hard rule)
        if current_time >= ENTRY_CUTOFF_TIME + ":00":
            return False

        if orb["high"] <= orb["low"]:
            return False

        # No closed candle yet this session for this symbol
        if last_closed_candle is None:
            return False

        close_price = last_closed_candle["close"]

        breakout_price = orb["high"] * (1 + ENTRY_BUFFER_PCT / 100)

        if close_price < breakout_price:
            return False

        breakout_percent = (
            (close_price - orb["high"]) / orb["high"]
        ) * 100

        if breakout_percent > MAX_BREAKOUT_PERCENT:
            return False

        return True