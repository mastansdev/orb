"""
Impact Engine

Responsibilities
----------------
Convert classified news into structured market impact
using the institutional Impact Rules knowledge base.

Owns:
    • Rule Lookup
    • Rule Evaluation
    • Rule Merge
    • Evaluation Statistics

Does NOT:
    • Collect News
    • Classify News
    • Predict Market
    • Trigger Trades
    • Execute Orders
    • Manage Portfolio

This module is a thin interpreter over the
Impact Rules knowledge base.
"""

from copy import deepcopy

from impact_rules import (
    IMPACT_RULES,
    IMPACT_LOW,
    REGIME_NEUTRAL,
)


class ImpactEngine:

    def __init__(self):
        self.reset()

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def reset(self):

        self._evaluated = 0
        self._matched = 0
        self._unmatched = 0

    # --------------------------------------------------
    # Public
    # --------------------------------------------------

    def evaluate(self, news):

        news = deepcopy(news)

        rule_name, rule = self._find_rule(news)

        if rule is None:

            self._apply_default(news)

            self._unmatched += 1

        else:

            self._apply_rule(
                news,
                rule_name,
                rule,
            )

            self._matched += 1

        self._evaluated += 1

        return news

    # --------------------------------------------------
    # Rule Lookup
    # --------------------------------------------------

    def _find_rule(self, news):

        category = news.get("category")
        sub_category = news.get("sub_category")
        event_type = news.get("event_type")

        for rule_name, rule in IMPACT_RULES.items():

            if rule["category"] != category:
                continue

            if rule["sub_category"] != sub_category:
                continue

            if rule["event_type"] != event_type:
                continue

            return rule_name, rule

        return None, None

    # --------------------------------------------------
    # Apply Rule
    # --------------------------------------------------

    def _apply_rule(
        self,
        news,
        rule_name,
        rule,
    ):

        news["impact_found"] = True

        news["matched_rule"] = rule_name

        news["market_impact"] = rule["market_impact"]

        news["market_score"] = rule["market_score"]
        news["sector_score"] = rule["sector_score"]
        news["stock_score"] = rule["stock_score"]

        news["confidence"] = rule["confidence"]
        news["confidence_source"] = rule["confidence_source"]

        news["market_regime_hint"] = rule["market_regime_hint"]

        news["expected_duration"] = rule["expected_duration"]

        news["direct_assets"] = list(
            rule["direct_assets"]
        )

        news["indirect_assets"] = list(
            rule["indirect_assets"]
        )

        news["bullish_sectors"] = list(
            rule["bullish_sectors"]
        )

        news["bearish_sectors"] = list(
            rule["bearish_sectors"]
        )

        news["historical_winners"] = list(
            rule["historical_winners"]
        )

        news["historical_losers"] = list(
            rule["historical_losers"]
        )

    # --------------------------------------------------
    # Default
    # --------------------------------------------------

    def _apply_default(self, news):

        news["impact_found"] = False

        news["matched_rule"] = None

        news["market_impact"] = IMPACT_LOW

        news["market_score"] = 0
        news["sector_score"] = 0
        news["stock_score"] = 0

        news["confidence"] = 0
        news["confidence_source"] = None

        news["market_regime_hint"] = REGIME_NEUTRAL

        news["expected_duration"] = None

        news["direct_assets"] = []
        news["indirect_assets"] = []

        news["bullish_sectors"] = []
        news["bearish_sectors"] = []

        news["historical_winners"] = []
        news["historical_losers"] = []

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    def stats(self):

        return {

            "evaluated": self._evaluated,

            "matched": self._matched,

            "unmatched": self._unmatched,
        }