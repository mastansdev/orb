"""
Market Catalyst

Responsibilities
----------------
Manage the lifecycle of active market catalysts.

Owns:
    • Active Catalyst Registry
    • Catalyst Activation
    • Catalyst Deactivation
    • Catalyst Strength
    • Catalyst Priority
    • Catalyst Statistics

Does NOT:
    • Collect News
    • Classify News
    • Calculate Impact
    • Determine Market Environment
    • Trigger Trades
    • Execute Orders

Consumes ImpactResult objects produced by ImpactEngine.
"""

from copy import deepcopy
from datetime import datetime
from news_models import ImpactResult


class MarketCatalyst:

    def __init__(self):
        self.reset()

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def reset(self):

        self._active = {}

        self._history = []

        self._activation_count = 0
        self._deactivation_count = 0
        self._update_count = 0

    # --------------------------------------------------
    # Activate
    # --------------------------------------------------

    def activate(
        self,
        impact: ImpactResult
    ):

        impact = deepcopy(impact)

        rule = impact.rule_name

        if not rule or rule == "UNKNOWN":
            return False

        catalyst = {

            "rule": impact.rule_name,

            "activated_at": datetime.now(),

            "category": impact.category,

            "sub_category": impact.subcategory,

            "event_type": impact.event_type,

            "market_regime": impact.market_regime_hint,

            "market_impact": impact.market_impact,

            "market_score": impact.market_score,

            "sector_score": impact.sector_score,

            "stock_score": impact.stock_score,

            "confidence": impact.confidence,

            "strength": impact.market_score,

            "priority": impact.market_score,

            "active": True,
        }

        self._active[rule] = catalyst

        self._history.append({

            "timestamp": datetime.now(),

            "action": "ACTIVATE",

            "rule": rule,
        })

        self._activation_count += 1

        return True

    # --------------------------------------------------
    # Update
    # --------------------------------------------------

    def update(
        self,
        impact: ImpactResult
    ):

        impact = deepcopy(impact)

        rule = impact.rule_name

        if not rule or rule == "UNKNOWN":
            return False

        if rule not in self._active:
            return self.activate(impact)

        catalyst = self._active[rule]

        catalyst["strength"] = impact.market_score
        catalyst["confidence"] = impact.confidence
        catalyst["market_impact"] = impact.market_impact
        catalyst["market_regime"] = impact.market_regime_hint
        catalyst["market_score"] = impact.market_score
        catalyst["sector_score"] = impact.sector_score
        catalyst["stock_score"] = impact.stock_score

        self._history.append({

            "timestamp": datetime.now(),

            "action": "UPDATE",

            "rule": rule,
        })

        self._update_count += 1

        return True

    # --------------------------------------------------
    # Deactivate
    # --------------------------------------------------

    def deactivate(
        self,
        rule: str
    ):

        catalyst = self._active.pop(rule, None)

        if catalyst is None:
            return False

        catalyst["active"] = False

        catalyst["deactivated_at"] = datetime.now()

        self._history.append({

            "timestamp": datetime.now(),

            "action": "DEACTIVATE",

            "rule": rule,
        })

        self._deactivation_count += 1

        return True

    # --------------------------------------------------
    # Read Only
    # --------------------------------------------------

    def active(self):

        return deepcopy(self._active)

    # --------------------------------------------------

    def strongest(self):

        if not self._active:
            return None

        return max(

            self._active.values(),

            key=lambda catalyst: catalyst["strength"]

        )

    # --------------------------------------------------

    def history(self):

        return deepcopy(self._history)

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

            "strongest": self.strongest(),

            "active_count": len(self._active),

            "history_count": len(self._history),
        }

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    def stats(self):

        return {

            "active": len(self._active),

            "activations": self._activation_count,

            "updates": self._update_count,

            "deactivations": self._deactivation_count,

            "history": len(self._history),
        }