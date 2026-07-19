"""
Execution Layer

Single execution gateway for the entire ORB Auto Trader.

The Engine never knows whether it is running in
PAPER or LIVE mode.

All BUY / SELL requests flow through this module.
"""

from config import TRADING_MODE

from trading.paper_execution import PaperExecution
from trading.live_execution import LiveExecution


class Execution:

    def __init__(self):

        if TRADING_MODE.upper() == "LIVE":
            self.executor = LiveExecution()
            self.mode = "LIVE"
            print("Execution Mode : LIVE")

        else:
            self.executor = PaperExecution()
            self.mode = "PAPER"
            print("Execution Mode : PAPER")

    # --------------------------------------------------

    def buy(
        self,
        security_id,
        symbol,
        price,
        qty,
        segment=None
    ):

        return self.executor.buy(
            security_id,
            symbol,
            price,
            qty,
            segment=segment
        )

    # --------------------------------------------------

    def sell(
        self,
        security_id,
        symbol,
        price,
        qty,
        segment=None
    ):

        return self.executor.sell(
            security_id,
            symbol,
            price,
            qty,
            segment=segment
        )