"""
Impact Engine

Responsibilities
----------------
Convert Market Stories into structured market impact
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

from impact_rules import (
    IMPACT_RULES,
    IMPACT_LOW,
    REGIME_NEUTRAL,
)
from news_models import (
    MarketStory,
    ImpactResult,
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

    def evaluate(
        self,
        story: MarketStory
    ) -> ImpactResult:

        rule_name, rule = self._find_rule(
            story
        )

        if rule is None:

            result = self._apply_default(
                story
            )

            self._unmatched += 1

        else:

            result = self._apply_rule(
                story,
                rule_name,
                rule
            )

            self._matched += 1

        self._evaluated += 1

        return result

    # --------------------------------------------------
    # Rule Lookup
    # --------------------------------------------------

    def _find_rule(
        self,
        story: MarketStory
    ):

        category = story.category
        subcategory = story.subcategory
        event_type = story.event_type

        for rule_name, rule in IMPACT_RULES.items():

            if rule["category"] != category:
                continue

            if rule["sub_category"] != subcategory:
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
        story: MarketStory,
        rule_name,
        rule,
    ) -> ImpactResult:

        return ImpactResult(

            story_id=story.story_id,
            
            rule_name=rule_name,

            category=story.category,

            subcategory=story.subcategory,

            event_type=story.event_type,


            market_impact=rule["market_impact"],

            market_score=rule["market_score"],

            sector_score=rule["sector_score"],

            stock_score=rule["stock_score"],

            expected_duration=rule["expected_duration"],

            confidence=rule["confidence"],

            confidence_source=rule["confidence_source"],

            market_regime_hint=rule["market_regime_hint"],

            bullish_sectors=list(rule["bullish_sectors"]),

            bearish_sectors=list(rule["bearish_sectors"]),

            direct_assets=list(rule["direct_assets"]),

            indirect_assets=list(rule["indirect_assets"]),

            historical_winners=list(rule["historical_winners"]),

            historical_losers=list(rule["historical_losers"]),

            notes=[
                f"Matched Rule={rule_name}"
            ]
        )

    # --------------------------------------------------
    # Default
    # --------------------------------------------------

    def _apply_default(
        self,
        story: MarketStory
    ) -> ImpactResult:

        return ImpactResult(

            story_id=story.story_id,

            rule_name="UNKNOWN",

            category=story.category,

            subcategory=story.subcategory,
            
            event_type=story.event_type,

            market_impact=IMPACT_LOW,

            market_score=0,

            sector_score=0,

            stock_score=0,

            expected_duration="UNKNOWN",

            confidence=0,

            confidence_source="UNKNOWN",

            market_regime_hint=REGIME_NEUTRAL,

            bullish_sectors=[],

            bearish_sectors=[],

            direct_assets=[],

            indirect_assets=[],

            historical_winners=[],

            historical_losers=[],

            notes=[
                "No matching impact rule."
            ]
        )

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    def stats(self):

        return {

            "evaluated": self._evaluated,

            "matched": self._matched,

            "unmatched": self._unmatched,
        }