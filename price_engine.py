from master_loader import master_loader


class PriceEngine:

    def __init__(self):
        self.prices = {}
        for symbol in master_loader.get_all_symbols():
            self.prices[symbol] = {
                "ltp": None,
                "previous_close": None,
                "change": 0.0,
                "open": None,
                "high": None,
                "low": None,
                "last_update": None,
            }

    # --------------------------------------------------
    def update(self, symbol, ltp, last_update=None):
        symbol = str(symbol).strip().upper()

        if symbol not in self.prices:
            return

        stock = self.prices[symbol]
        ltp = float(ltp)

        stock["ltp"] = ltp
        stock["last_update"] = last_update

        if stock["open"] is None:
            stock["open"] = ltp

        if stock["high"] is None or ltp > stock["high"]:
            stock["high"] = ltp

        if stock["low"] is None or ltp < stock["low"]:
            stock["low"] = ltp

        previous_close = stock["previous_close"]
        if previous_close and previous_close > 0:
            stock["change"] = round(
                ((ltp - previous_close) / previous_close) * 100, 2
            )

    # --------------------------------------------------
    def set_previous_close(self, symbol, previous_close):
        symbol = str(symbol).strip().upper()

        if symbol not in self.prices:
            return

        self.prices[symbol]["previous_close"] = float(previous_close)

    # --------------------------------------------------
    def get_stock(self, symbol):
        """Helper method to safely fetch a symbol's dictionary."""
        symbol = str(symbol).strip().upper()
        return self.prices.get(symbol)

    # --------------------------------------------------
    def get_ltp(self, symbol):
        stock = self.get_stock(symbol)
        if stock is None:
            return None
        return stock["ltp"]

    # --------------------------------------------------
    def get_change(self, symbol):
        stock = self.get_stock(symbol)
        if stock is None:
            return 0.0
        return stock["change"]

    # --------------------------------------------------
    def get_previous_close(self, symbol):
        stock = self.get_stock(symbol)
        if stock is None:
            return None
        return stock["previous_close"]

    # --------------------------------------------------
    def get_open(self, symbol):
        stock = self.get_stock(symbol)
        if stock is None:
            return None
        return stock["open"]

    # --------------------------------------------------
    def get_high(self, symbol):
        stock = self.get_stock(symbol)
        if stock is None:
            return None
        return stock["high"]

    # --------------------------------------------------
    def get_low(self, symbol):
        stock = self.get_stock(symbol)
        if stock is None:
            return None
        return stock["low"]

    # --------------------------------------------------
    def get_last_update(self, symbol):
        stock = self.get_stock(symbol)
        if stock is None:
            return None
        return stock["last_update"]

    # --------------------------------------------------
    def has_price(self, symbol):
        stock = self.get_stock(symbol)
        if stock is None:
            return False
        return stock["ltp"] is not None

    # --------------------------------------------------
    def get_snapshot(self, symbol):
        stock = self.get_stock(symbol)

        if stock is None:
            return {"price": None}

        return {
            "price": {
                "ltp": stock["ltp"],
                "change": stock["change"],
                "previous_close": stock["previous_close"],
                "open": stock["open"],
                "high": stock["high"],
                "low": stock["low"],
                "last_update": stock["last_update"],
            }
        }

    # --------------------------------------------------
    def reset(self):
        """Resets daily values at the start of a trading day, keeping previous_close."""
        for stock in self.prices.values():
            stock["ltp"] = None
            stock["change"] = 0.0
            stock["open"] = None
            stock["high"] = None
            stock["low"] = None
            stock["last_update"] = None

    # --------------------------------------------------
    def total_updated(self):
        """Returns the total number of symbols that have active price updates."""
        return sum(
            1 for stock in self.prices.values() if stock["ltp"] is not None
        )


# Singleton instance
price_engine = PriceEngine()