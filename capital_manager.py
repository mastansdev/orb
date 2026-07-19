from config import CAPITAL


class CapitalManager:

    def __init__(self):

        self.starting_capital = CAPITAL
        self.available_capital = CAPITAL
        self.blocked_capital = 0
        self.realized_pnl = 0
        self._floating_mtm = 0.0

    # --------------------------------------------------

    def can_buy(self, amount):

        return (
            amount > 0
            and amount <= self.available_capital
        )

    # --------------------------------------------------

    def block(self, amount):

        if not self.can_buy(amount):
            return False

        self.available_capital -= amount
        self.blocked_capital += amount

        return True

    # --------------------------------------------------

    def release(self, invested_amount, pnl):

        invested_amount = min(
            invested_amount,
            self.blocked_capital
        )

        self.blocked_capital -= invested_amount
        self.available_capital += invested_amount + pnl
        self.realized_pnl += pnl

    # --------------------------------------------------

    def settle_day(self):

        self.starting_capital = round(self.available_capital, 2)
        self._floating_mtm = 0.0
        self.realized_pnl = 0.0
        self.blocked_capital = 0

    # --------------------------------------------------

    def available(self):

        return round(self.available_capital, 2)

    # --------------------------------------------------

    def blocked(self):

        return round(self.blocked_capital, 2)

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