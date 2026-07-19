from config import (
    CAPITAL,
    RISK_PER_TRADE,
    MIN_QTY,
    MIN_TRADE_VALUE,
    MAX_CAPITAL_PER_TRADE
)


class PositionManager:

    def __init__(self, capital_manager):
        self.capital_manager = capital_manager
        self.positions = {}

    # --------------------------------------------------

    def calculate_quantity(self, entry_price, stop_loss):

        risk_amount = CAPITAL * RISK_PER_TRADE
        risk_per_share = abs(entry_price - stop_loss)

        if risk_per_share <= 0:
            return 0

        risk_qty = int(risk_amount / risk_per_share)

        # Quantity affordable given FREE MARGIN (buying
        # power = free equity × leverage), matching how
        # an MIS account actually gates size.
        buying_power = self.capital_manager.buying_power()
        capital_qty = int(buying_power / entry_price)

        max_trade_qty = int(MAX_CAPITAL_PER_TRADE / entry_price)

        qty = min(
            risk_qty,
            capital_qty,
            max_trade_qty)

        return qty
        
        
    # --------------------------------------------------

    def has_position(self, security_id):
        return security_id in self.positions

    # --------------------------------------------------

    def open_position(
        self,
        security_id,
        symbol,
        entry_price,
        stop_loss
    ):

        qty = self.calculate_quantity(
            entry_price,
            stop_loss
        )

        return qty

    # --------------------------------------------------

    def confirm_position(
        self,
        security_id,
        symbol,
        entry_price,
        stop_loss,
        qty
    ):

        investment = qty * entry_price

        if not self.capital_manager.block(investment):
            return False

        self.positions[security_id] = {
            "symbol": symbol,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "qty": qty,
            "investment": investment
        }

        return True

    # --------------------------------------------------

    def get_position(self, security_id):
        return self.positions.get(security_id)

    # --------------------------------------------------

    def recover_position(self, security_id, symbol, entry_price, stop_loss, qty):

        self.positions[security_id] = {
            "symbol": symbol,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "qty": qty,
            "investment": qty * entry_price
        }

    # --------------------------------------------------

    def remove_position(
        self,
        security_id
    ):
        """
        Remove a position after broker confirmation
        (manual exit / broker square-off).
        """

        position = self.positions.get(security_id)

        if position is None:
            return False

        self.capital_manager.release(
            position["investment"],
            0
        )

        del self.positions[security_id]

        return True

    # --------------------------------------------------

    def reduce_position(self, security_id, qty_sold, exit_price):
        """
        Partial profit booking: release the sold
        portion's capital + PnL, keep the remainder
        tracked correctly.
        """
        position = self.positions.get(security_id)

        if position is None or qty_sold <= 0:
            return False

        qty_sold = min(qty_sold, position["qty"])

        entry_price = position["entry_price"]
        released_investment = qty_sold * entry_price
        partial_pnl = (exit_price - entry_price) * qty_sold

        self.capital_manager.release(
            released_investment,
            partial_pnl
        )

        position["qty"] -= qty_sold
        position["investment"] -= released_investment

        if position["qty"] <= 0:
            del self.positions[security_id]

        return True

    # --------------------------------------------------

    def close_position(self, security_id, pnl):

        position = self.positions.get(security_id)

        if position is None:
            return

        self.capital_manager.release(
            position["investment"],
            pnl
        )

        del self.positions[security_id]