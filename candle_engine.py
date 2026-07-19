from collections import deque

from master_loader import master_loader


class CandleEngine:
    """
    Candle Engine

    Responsibilities
    ----------------
    • Build 1-minute OHLC candles from live ticks
    • Maintain current building candle
    • Maintain completed candle history

    Does NOT
    --------
    • Detect ORB
    • Calculate ATR
    • Detect patterns
    • Generate signals
    • Manage trades
    """

    MAX_HISTORY = 500

    def __init__(self):

        self.candles = {}

        self._initialize()

    # --------------------------------------------------

    def _initialize(self):

        for symbol in master_loader.get_all_symbols():

            self.candles[symbol] = {

                "current": None,

                "history": deque(
                    maxlen=self.MAX_HISTORY
                )

            }

    # --------------------------------------------------

    def update(
        self,
        symbol,
        ltp,
        timestamp
    ):
        symbol = str(symbol).strip().upper()

        if symbol not in self.candles:
            return

        data = self.candles[symbol]

        # ---------------------------------
        # Timestamp Validation
        # ---------------------------------

        if not timestamp:
            return

        ltp = float(ltp)

        minute = timestamp[:5]

        current = data["current"]

        # ---------------------------------
        # First candle
        # ---------------------------------

        if current is None:

            data["current"] = {

                "minute": minute,

                "open": ltp,

                "high": ltp,

                "low": ltp,

                "close": ltp

            }

            return

        # ---------------------------------
        # Same minute
        # ---------------------------------

        if current["minute"] == minute:

            current["close"] = ltp

            if ltp > current["high"]:
                current["high"] = ltp

            if ltp < current["low"]:
                current["low"] = ltp

            return

        # ---------------------------------
        # Minute changed
        # ---------------------------------

        data["history"].append(
            current.copy()
        )

        data["current"] = {

            "minute": minute,

            "open": ltp,

            "high": ltp,

            "low": ltp,

            "close": ltp

        }

    # --------------------------------------------------

    def get_current(
        self,
        symbol
    ):

        data = self.candles.get(symbol)

        if data is None:
            return None

        if data["current"] is None:
            return None

        return dict(
            data["current"]
        )

    # --------------------------------------------------

    def get_latest(
        self,
        symbol
    ):

        data = self.candles.get(symbol)

        if data is None:
            return None

        if not data["history"]:
            return None

        return dict(
            data["history"][-1]
        )

    # --------------------------------------------------

    def get_previous(
        self,
        symbol
    ):

        history = self.get_history(
            symbol,
            limit=2
        )

        if len(history) < 2:
            return None

        return history[-2]

    # --------------------------------------------------

    def get_history(
        self,
        symbol,
        limit=20
    ):

        data = self.candles.get(symbol)

        if data is None:
            return []

        return [
            dict(candle)
            for candle in list(data["history"])[-limit:]
        ]

    # --------------------------------------------------

    def reset(self):

        self.candles.clear()

        self._initialize()


candle_engine = CandleEngine()