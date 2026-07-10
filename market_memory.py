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

This module is the persistent memory layer of the
Market Intelligence pipeline.
"""

from copy import deepcopy
from datetime import datetime


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

    def remember(self, news):

        news = deepcopy(news)

        rule = news.get("matched_rule")

        if not rule:
            return False

        event = {

            "timestamp": datetime.now(),

            "rule": rule,

            "category": news.get("category"),

            "sub_category": news.get("sub_category"),

            "event_type": news.get("event_type"),

            "market_regime": news.get("market_regime_hint"),

            "market_impact": news.get("market_impact"),

            "market_score": news.get("market_score"),

            "confidence": news.get("confidence"),

            "confidence_source": news.get(
                "confidence_source"
            ),

            "active": True,
        }

        self._history.append(event)

        self._active[rule] = event

        self._remembered += 1

        return True

    # --------------------------------------------------
    # Forget
    # --------------------------------------------------

    def forget(self, rule):

        event = self._active.pop(rule, None)

        if event is None:
            return False

        event["active"] = False

        self._forgotten += 1

        return True

    # --------------------------------------------------
    # Expire
    # --------------------------------------------------

    def expire(self, rule):

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

    def is_active(self, rule):

        return rule in self._active

    # --------------------------------------------------

    def stats(self):

        return {

            "remembered": self._remembered,

            "active": len(self._active),

            "forgotten": self._forgotten,

            "expired": self._expired,

            "history": len(self._history),
        }