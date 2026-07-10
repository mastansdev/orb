"""
Market Environment

Responsibilities
----------------
Maintain the current market environment by aggregating
active market catalysts.

Owns:
    • Current Environment
    • Active Catalysts
    • Environment History
    • Regime Changes
    • Statistics

Does NOT:
    • Collect News
    • Classify News
    • Calculate Impact
    • Trigger Trades
    • Execute Orders
    • Manage Portfolio

Consumes evidence from ImpactEngine.
"""

from copy import deepcopy
from datetime import datetime

from impact_rules import (
    REGIME_NEUTRAL,
    REGIME_RISK_ON,
    REGIME_RISK_OFF,
    REGIME_VOLATILE,
)


class MarketEnvironment:

    def __init__(self):
        self.reset()

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def reset(self):

        self._environment = REGIME_NEUTRAL

        self._confidence = 0

        self._market_score = 0

        self._active_catalysts = []

        self._history = []

        self._updates = 0

        self._environment_changes = 0

    # --------------------------------------------------
    # Update
    # --------------------------------------------------

    def update(self, news):

        news = deepcopy(news)

        regime = news.get("market_regime_hint")

        if regime is None:
            return self.current()

        matched_rule = news.get("matched_rule")

        if matched_rule:

            if matched_rule not in self._active_catalysts:
                self._active_catalysts.append(
                    matched_rule
                )

        previous = self._environment

        self._environment = self._calculate_environment(news)

        self._confidence = max(
            self._confidence,
            news.get("confidence", 0)
        )

        self._market_score += news.get(
            "market_score",
            0
        )

        changed = previous != self._environment

        if changed:

            self._environment_changes += 1

            self._history.append({

                "timestamp": datetime.now(),

                "previous": previous,

                "current": self._environment,

                "trigger": matched_rule,
            })

        self._updates += 1

        return self.current()

    # --------------------------------------------------
    # Internal
    # --------------------------------------------------

    def _calculate_environment(self, news):

        regime = news.get("market_regime_hint")

        if regime in (

            REGIME_RISK_ON,

            REGIME_RISK_OFF,

            REGIME_VOLATILE,

        ):

            return regime

        return REGIME_NEUTRAL

    # --------------------------------------------------
    # Read Only
    # --------------------------------------------------

    def current(self):

        return {

            "environment": self._environment,

            "confidence": self._confidence,

            "market_score": self._market_score,

            "active_catalysts": list(
                self._active_catalysts
            ),

            "last_update": (
                self._history[-1]["timestamp"]
                if self._history
                else None
            ),

            "regime_changed": (
                len(self._history) > 0
            ),
        }

    # --------------------------------------------------

    def history(self):

        return list(self._history)

    # --------------------------------------------------

    def stats(self):

        return {

            "updates": self._updates,

            "environment": self._environment,

            "changes": self._environment_changes,

            "active_catalysts": len(
                self._active_catalysts
            ),
        }