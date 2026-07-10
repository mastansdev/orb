class PortfolioRiskManager:
    """
    Portfolio-level admission controller.

    Responsibilities:
        • Maximum open trades
        • Duplicate trade protection

    This module decides whether the portfolio may
    accept a new trade.

    It NEVER:
        • scores trades
        • sizes positions
        • manages exits
        • places orders
    """

    def __init__(
        self,
        max_open_trades=100
    ):
        self.max_open_trades = max_open_trades
        self.open_trades = set()

    # --------------------------------------------------
    # Portfolio State
    # --------------------------------------------------

    def add_trade(
        self,
        symbol
    ):
        self.open_trades.add(symbol)

    def remove_trade(
        self,
        symbol
    ):
        self.open_trades.discard(symbol)

    # --------------------------------------------------
    # Admission Check
    # --------------------------------------------------

    def can_take_trade(
        self,
        symbol,
        intelligence=None
    ):
        # ---------------------------------
        # Maximum Open Trades
        # ---------------------------------

        if len(self.open_trades) >= self.max_open_trades:

            return {
                "allowed": False,
                "reason": (
                    f"Maximum Open Trades "
                    f"Reached ({self.max_open_trades})"
                )
            }

        # ---------------------------------
        # Duplicate Trade Protection
        # ---------------------------------

        if symbol in self.open_trades:

            return {
                "allowed": False,
                "reason": (
                    f"{symbol} already exists "
                    "in portfolio"
                )
            }

        return {
            "allowed": True,
            "reason": "Approved"
        }