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

Consumes ImpactResult objects produced by ImpactEngine.
"""

from copy import deepcopy
from datetime import datetime

from news.impact_rules import (
    REGIME_NEUTRAL,
    REGIME_RISK_ON,
    REGIME_RISK_OFF,
    REGIME_VOLATILE,
)
from news.news_models import ImpactResult


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

    def update(
        self,
        impact: ImpactResult
    ):

        impact = deepcopy(impact)

        regime = impact.market_regime_hint

        if regime is None:
            return self.current()

        matched_rule = impact.rule_name

        if matched_rule:

            if matched_rule not in self._active_catalysts:
                self._active_catalysts.append(
                    matched_rule
                )

        previous = self._environment

        self._environment = self._calculate_environment(impact)

        self._confidence = max(
            self._confidence,
            impact.confidence
        )

        self._market_score += impact.market_score

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

    def _calculate_environment(
        self,
        impact: ImpactResult
    ):

        regime = impact.market_regime_hint

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

    def current(self) -> dict:

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

    def history(self) -> list:

        return list(self._history)

    # --------------------------------------------------
    # Snapshot
    # --------------------------------------------------

    def get_snapshot(self) -> dict:
        """
        Return a read-only snapshot for
        IntelligenceEngine.
        """

        return {

            "environment": self._environment,

            "confidence": self._confidence,

            "market_score": self._market_score,

            "active_catalysts": list(
                self._active_catalysts
            ),

            "history_count": len(self._history),
        }

    # --------------------------------------------------

    def stats(self) -> dict:

        return {

            "updates": self._updates,

            "environment": self._environment,

            "changes": self._environment_changes,

            "active_catalysts": len(
                self._active_catalysts
            ),
        }