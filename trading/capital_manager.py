from config import CAPITAL, MIS_LEVERAGE, TRADING_MODE


class CapitalManager:
    """
    Capital & margin manager.

    Tracks EQUITY (your real money) but blocks MARGIN,
    exactly like an MIS intraday account at Dhan/Kite:

        buying power = equity × leverage
        margin blocked per trade = trade value ÷ leverage

    So a ₹1,00,000 position on 5× leverage blocks only
    ₹20,000 of equity — letting the bot understand true
    capital requirements in paper mode.

    PnL is always on the FULL position value (leverage
    amplifies both directions).
    """

    def __init__(self):

        self.starting_capital = CAPITAL
        self.available_capital = CAPITAL   # free equity/margin
        self.blocked_capital = 0           # margin blocked
        self.realized_pnl = 0
        self._floating_mtm = 0.0

        # LIVE always uses real broker leverage; PAPER
        # simulates it. Either way, model it.
        self.leverage = max(1, MIS_LEVERAGE)
        self.mode = TRADING_MODE

    # --------------------------------------------------

    def _margin(self, trade_value):
        """Margin required for a given full trade value."""
        return trade_value / self.leverage

    # --------------------------------------------------

    def buying_power(self):
        """Free deployable exposure = free equity × leverage."""
        return round(self.available_capital * self.leverage, 2)

    # --------------------------------------------------

    def can_buy(self, trade_value):
        """Can we afford the MARGIN for this trade value?"""
        if trade_value <= 0:
            return False

        return self._margin(trade_value) <= self.available_capital

    # --------------------------------------------------

    def block(self, trade_value):
        """
        Block margin for a position of `trade_value`
        (full value, not margin — conversion is internal).
        """
        if not self.can_buy(trade_value):
            return False

        margin = self._margin(trade_value)

        self.available_capital -= margin
        self.blocked_capital += margin

        return True

    # --------------------------------------------------

    def release(self, trade_value, pnl):
        """
        Release the margin blocked for `trade_value` and
        credit realized PnL (on full position).
        """
        margin = min(
            self._margin(trade_value),
            self.blocked_capital
        )

        self.blocked_capital -= margin
        self.available_capital += margin + pnl
        self.realized_pnl += pnl

    # --------------------------------------------------

    def settle_day(self):

        self.starting_capital = round(self.available_capital, 2)
        self._floating_mtm = 0.0
        self.realized_pnl = 0.0
        self.blocked_capital = 0

    # --------------------------------------------------

    def available(self):
        """Free equity / free margin."""
        return round(self.available_capital, 2)

    # --------------------------------------------------

    def blocked(self):
        """Margin currently blocked."""
        return round(self.blocked_capital, 2)

    # --------------------------------------------------

    def exposure(self):
        """Gross position value currently deployed."""
        return round(self.blocked_capital * self.leverage, 2)

    # --------------------------------------------------

    def pnl(self):

        return round(self.realized_pnl, 2)

    # --------------------------------------------------

    def capital(self):

        return round(self.starting_capital, 2)

    # --------------------------------------------------

    def reset(self):

        self.available_capital = self.starting_capital
        self.blocked_capital = 0
        self.realized_pnl = 0.0
        self._floating_mtm = 0.0

    # --------------------------------------------------

    def set_floating_mtm(self, mtm):

        self._floating_mtm = round(mtm, 2)

    # --------------------------------------------------

    def floating_mtm(self):

        return round(self._floating_mtm, 2)

    # --------------------------------------------------

    def net_pnl(self):

        return round(
            self.realized_pnl + self._floating_mtm,
            2
        )
