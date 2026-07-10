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

Consumes evidence from ImpactEngine.
"""

from copy import deepcopy
from datetime import datetime


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

    def activate(self, news):

        news = deepcopy(news)

        rule = news.get("matched_rule")

        if not rule:
            return False

        catalyst = {

            "rule": rule,

            "activated_at": datetime.now(),

            "category": news.get("category"),

            "sub_category": news.get("sub_category"),

            "event_type": news.get("event_type"),

            "market_regime": news.get("market_regime_hint"),

            "market_impact": news.get("market_impact"),

            "market_score": news.get("market_score"),

            "sector_score": news.get("sector_score"),

            "stock_score": news.get("stock_score"),

            "confidence": news.get("confidence"),

            "strength": news.get("market_score", 0),

            "priority": news.get("market_score", 0),

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

    def update(self, news):

        news = deepcopy(news)

        rule = news.get("matched_rule")

        if not rule:
            return False

        if rule not in self._active:
            return self.activate(news)

        catalyst = self._active[rule]

        catalyst["strength"] = news.get(
            "market_score",
            catalyst["strength"],
        )

        catalyst["confidence"] = news.get(
            "confidence",
            catalyst["confidence"],
        )

        catalyst["market_impact"] = news.get(
            "market_impact",
            catalyst["market_impact"],
        )

        catalyst["market_regime"] = news.get(
            "market_regime_hint",
            catalyst["market_regime"],
        )

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

    def deactivate(self, rule):

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

    def is_active(self, rule):

        return rule in self._active

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