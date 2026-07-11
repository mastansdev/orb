"""
Market Memory

Responsibilities
----------------
Maintain a historical memory of market catalysts.

Owns:
    • Catalyst Timeline
    • Active Catalysts
    • Historical Memory
    • Catalyst Statistics

Does NOT:
    • Collect News
    • Classify News
    • Calculate Impact
    • Determine Market Environment
    • Trigger Trades
    • Execute Orders

Consumes ImpactResult objects produced by ImpactEngine.

This module is the persistent memory layer of the
Market Intelligence pipeline.
"""

from copy import deepcopy
from datetime import datetime
from news_models import ImpactResult


class MarketMemory:

    def __init__(self):
        self.reset()

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def reset(self):
        self._history = []
        self._active = {}
        self._remembered = 0
        self._forgotten = 0
        self._expired = 0

    # --------------------------------------------------
    # Remember
    # --------------------------------------------------

    def remember(
        self,
        impact: ImpactResult
    ):
        impact = deepcopy(impact)
        rule = impact.rule_name
        
        if not rule or rule == "UNKNOWN":
            return False

        event = {
            "timestamp": datetime.now(),
            "rule": impact.rule_name,
            "category": impact.category,
            "sub_category": impact.subcategory,
            "event_type": impact.event_type,
            "market_regime": impact.market_regime_hint,
            "market_impact": impact.market_impact,
            "market_score": impact.market_score,
            "confidence": impact.confidence,
            "confidence_source": impact.confidence_source,
            "active": True,
        }

        self._history.append(event)
        self._active[rule] = event
        self._remembered += 1

        return True

    # --------------------------------------------------
    # Forget
    # --------------------------------------------------

    def forget(
        self,
        rule: str
    ):
        event = self._active.pop(rule, None)

        if event is None:
            return False

        event["active"] = False
        self._forgotten += 1

        return True

    # --------------------------------------------------
    # Expire
    # --------------------------------------------------

    def expire(
        self,
        rule: str
    ):
        event = self._active.pop(rule, None)

        if event is None:
            return False

        event["active"] = False
        self._expired += 1

        return True

    # --------------------------------------------------
    # Read Only
    # --------------------------------------------------

    def active(self):
        return deepcopy(self._active)

    # --------------------------------------------------

    def history(self):
        return deepcopy(self._history)

    # --------------------------------------------------

    def active_rules(self):
        return list(self._active.keys())

    # --------------------------------------------------

    def is_active(
        self,
        rule: str
    ) -> bool:
        return rule in self._active

    # --------------------------------------------------
    # Snapshot
    # --------------------------------------------------

    def get_snapshot(self) -> dict:
        """
        Return a read-only snapshot for
        IntelligenceEngine.
        """

        return {

            "active": deepcopy(self._active),

            "active_rules": self.active_rules(),

            "history_count": len(self._history),

            "remembered": self._remembered,
        }

    # --------------------------------------------------

    def stats(self):
        return {
            "remembered": self._remembered,
            "active": len(self._active),
            "forgotten": self._forgotten,
            "expired": self._expired,
            "history": len(self._history),
        }