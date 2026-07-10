from copy import deepcopy
from datetime import datetime


class MarketMoodEngine:
    """
    Maintains the current market environment snapshot.

    Responsibility:
        • Store normalized market mood intelligence
        • Provide a consistent snapshot
        • Accept updates from future intelligence engines

    This engine NEVER:
        • predicts markets
        • selects trades
        • manages positions
        • executes orders
    """

    def __init__(self):

        self._snapshot = self._default_snapshot()

    # --------------------------------------------------

    def _default_snapshot(self):

        return {

            "mood": "UNKNOWN",

            "confidence": 0,

            "trend": "UNKNOWN",

            "participation": "UNKNOWN",

            "volatility": "UNKNOWN",

            "risk_state": "UNKNOWN",

            "event_driven": False,

            "last_update": None

        }

    # --------------------------------------------------

    def update(self, **kwargs):

        for key, value in kwargs.items():

            if (
                key in self._snapshot
                and value is not None
            ):

                self._snapshot[key] = value

        self._snapshot["last_update"] = (
            datetime.now().isoformat()
        )

    # --------------------------------------------------

    def get_snapshot(self, symbol=None):

        return {

            "market_mood": deepcopy(
                self._snapshot
            )

        }

    # --------------------------------------------------

    def reset(self):

        self._snapshot = self._default_snapshot()