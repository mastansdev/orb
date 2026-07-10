from threading import Lock


class BotState:

    def __init__(self):

        self._lock = Lock()

        # Engine
        self.engine_running = False
        self.market_connected = False
        self.mode = "PAPER"

        # Universe
        self.universe = 0

        # Trading
        self.open_positions = 0
        self.closed_positions = 0

        self.total_trades = 0
        self.wins = 0
        self.losses = 0

        # Capital
        self.capital_used = 0.0
        self.available_capital = 0.0

        # PnL
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0

    # -----------------------------------------

    def set_engine_running(self, status):

        with self._lock:
            self.engine_running = status

    def set_market_connected(self, status):

        with self._lock:
            self.market_connected = status

    def set_universe(self, count):

        with self._lock:
            self.universe = count

    # -----------------------------------------

    def get_status(self):

        with self._lock:

            return {

                "engine_running": self.engine_running,
                "market_connected": self.market_connected,
                "mode": self.mode,
                "universe": self.universe,

                "open_positions": self.open_positions,
                "closed_positions": self.closed_positions,

                "total_trades": self.total_trades,

                "wins": self.wins,
                "losses": self.losses,

                "capital_used": self.capital_used,
                "available_capital": self.available_capital,

                "realized_pnl": self.realized_pnl,
                "unrealized_pnl": self.unrealized_pnl
            }


bot_state = BotState()