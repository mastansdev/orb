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

        available_capital = self.capital_manager.available()
        capital_qty = int(available_capital / entry_price)

        max_trade_qty = int(MAX_CAPITAL_PER_TRADE / entry_price)

        qty = min(
            risk_qty,
            capital_qty,
            max_trade_qty)

        if qty < MIN_QTY:
            return 0

        if qty * entry_price < MIN_TRADE_VALUE:
            return 0

        return qty

    # --------------------------------------------------

    def has_position(self, security_id):
        return security_id in self.positions

    # --------------------------------------------------

    def open_position(self, security_id, symbol, entry_price, stop_loss):

        qty = self.calculate_quantity(
            entry_price,
            stop_loss
        )

        if qty <= 0:
            return 0

        investment = qty * entry_price

        if not self.capital_manager.block(investment):
            return 0

        self.positions[security_id] = {
            "symbol": symbol,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "qty": qty,
            "investment": investment
        }

        return qty

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

    def close_position(self, security_id, pnl):

        position = self.positions.get(security_id)

        if position is None:
            return

        self.capital_manager.release(
            position["investment"],
            pnl
        )

        del self.positions[security_id]