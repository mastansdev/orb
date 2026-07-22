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

import os
from datetime import datetime

from news.impact_rules import (
    IMPACT_RULES,
    IMPACT_LOW,
    REGIME_NEUTRAL,
)
from news.news_models import (
    MarketStory,
    ImpactResult,
)
from news.news_taxonomy import (
    SENTIMENT_KEYWORDS,
    RESULT_KEYWORDS,
)
from config import VERBOSE_CONSOLE

# Fix (2026-07-22, take 2): this per-story fallback/no-signal
# reasoning was flooding the terminal -- every single news item
# that didn't match a specific IMPACT_RULES entry printed a line,
# and most don't. User wants a clean terminal with only real
# results on screen. The "throw the reason so we can improve"
# requirement still matters, so the detail isn't dropped -- it
# always goes to logs/news_diagnostics.log, and only ALSO prints
# to the console when VERBOSE_CONSOLE=True (config.py).
_DIAG_LOG_PATH = os.path.join("logs", "news_diagnostics.log")


def _log_diagnostic(message):
    if VERBOSE_CONSOLE:
        print(message)
    try:
        os.makedirs("logs", exist_ok=True)
        with open(_DIAG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {message}\n")
    except Exception:
        pass


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
        # Fix (2026-07-22): visibility into how often the
        # generic keyword fallback fires vs a specific rule
        # match vs genuinely no signal found either way --
        # "throw the reason" instead of a silent flat zero.
        self._generic_fallback_used = 0
        self._no_signal_found = 0

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
    # Default / Generic Fallback (rewritten 2026-07-22)
    # --------------------------------------------------
    #
    # This used to always return flat zeros -- market_score,
    # sector_score, stock_score, confidence all 0 -- for ANY
    # story whose category/subcategory/event_type didn't
    # exactly match one of the ~30 hand-written IMPACT_RULES.
    # Confirmed live: 8 of the 12 categories the classifier can
    # detect (GOVERNMENT, ORDER, MERGER, ACQUISITION, PROMOTER,
    # MARKET, COMMODITY, MACRO) had zero rules, so a real,
    # market-moving story (today: a tariff announcement,
    # category=MACRO) was silently treated as if nothing had
    # happened. Now: scan the story's actual text for real
    # positive/negative market language before giving up. This
    # is deliberately lower-confidence than a specific matched
    # rule (see notes/confidence below) -- it's meant to catch
    # what the specific rules haven't been written for yet, not
    # to replace them.
    # --------------------------------------------------

    def _apply_default(
        self,
        story: MarketStory
    ) -> ImpactResult:

        net, hits = self._generic_sentiment(story)

        if net != 0:

            self._generic_fallback_used += 1

            direction_word = "negative" if net < 0 else "positive"

            _log_diagnostic(
                f"[IMPACT] No specific rule for category="
                f"{story.category}/{story.subcategory}/"
                f"{story.event_type} -- used generic keyword "
                f"fallback: {direction_word} "
                f"(matched: {', '.join(hits[:5])})"
            )

            # Deliberately modest magnitude and confidence --
            # a keyword hit is real signal but weaker evidence
            # than a hand-verified specific rule.
            score = max(-2, min(2, net))

            return ImpactResult(

                story_id=story.story_id,

                rule_name="GENERIC_SENTIMENT_FALLBACK",

                category=story.category,

                subcategory=story.subcategory,

                event_type=story.event_type,

                market_impact=(
                    "NEGATIVE" if net < 0 else "POSITIVE"
                ),

                market_score=score,

                sector_score=score,

                stock_score=score,

                expected_duration="UNKNOWN",

                confidence=35,

                confidence_source="GENERIC_KEYWORD_MATCH",

                market_regime_hint=REGIME_NEUTRAL,

                bullish_sectors=[],

                bearish_sectors=[],

                direct_assets=[],

                indirect_assets=[],

                historical_winners=[],

                historical_losers=[],

                notes=[
                    f"No specific IMPACT_RULES match for "
                    f"category={story.category} -- generic "
                    f"keyword fallback found: {', '.join(hits)}"
                ]
            )

        # --------------------------------------------------
        # Genuinely no signal either way -- this IS the correct
        # outcome sometimes (a routine, non-market-moving
        # notification), so it stays neutral. But it's now
        # counted and loggable, instead of being indistinguishable
        # from every other silent zero.
        # --------------------------------------------------
        self._no_signal_found += 1

        _log_diagnostic(
            f"[IMPACT] No specific rule AND no generic sentiment "
            f"keywords matched for category={story.category}/"
            f"{story.subcategory}/{story.event_type} -- staying "
            f"neutral. If this looks like it should have been "
            f"a real signal, add words to SENTIMENT_KEYWORDS "
            f"(news/news_taxonomy.py) or a specific rule "
            f"(news/impact_rules.py)."
        )

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
                "No matching impact rule and no generic "
                "sentiment keywords matched -- genuinely no "
                "signal found, not a coverage gap."
            ]
        )

    # --------------------------------------------------
    # Generic Sentiment Scan (new 2026-07-22)
    # --------------------------------------------------

    def _generic_sentiment(self, story: MarketStory):
        """
        Scan the story's own text against SENTIMENT_KEYWORDS
        (general market language) and RESULT_KEYWORDS
        (earnings-specific language, previously defined but
        never actually wired into anything). Returns
        (net_score, matched_keywords) -- net_score is simply
        (positive hits - negative hits), matched_keywords is
        the actual words found, so the log line above always
        shows real evidence, never a black-box number.
        """
        text_parts = [
            getattr(story, "name", "") or "",
            getattr(story, "catalyst", "") or "",
            getattr(story, "category", "") or "",
            getattr(story, "subcategory", "") or "",
            getattr(story, "event_type", "") or "",
        ]
        text = " ".join(text_parts).lower()

        if not text.strip():
            return 0, []

        hits = []
        net = 0

        for word in SENTIMENT_KEYWORDS.get("NEGATIVE", []):
            if word in text:
                net -= 1
                hits.append(f"-{word}")

        for word in SENTIMENT_KEYWORDS.get("POSITIVE", []):
            if word in text:
                net += 1
                hits.append(f"+{word}")

        for word in RESULT_KEYWORDS.get("NEGATIVE_RESULTS", []):
            if word in text:
                net -= 1
                hits.append(f"-{word}")

        for word in RESULT_KEYWORDS.get("POSITIVE_RESULTS", []):
            if word in text:
                net += 1
                hits.append(f"+{word}")

        return net, hits

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    def stats(self):

        return {

            "evaluated": self._evaluated,

            "matched": self._matched,

            "unmatched": self._unmatched,

            "generic_fallback_used": self._generic_fallback_used,

            "no_signal_found": self._no_signal_found,
        }