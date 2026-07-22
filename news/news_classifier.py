"""
News Classifier

Responsibilities
----------------
Convert normalized news into structured market evidence.

Owns:
    • Category Classification
    • Sub-category Classification
    • Event Type Classification
    • Asset Mapping
    • Sector Mapping

Does NOT:
    • Collect News
    • Score News
    • Predict Market
    • Trigger Trades
    • Calculate Impact

Classification is deterministic using the News Taxonomy.
"""

from news.news_models import (
    ClassifiedNews,
    ProcessedNews,
)
from news.news_taxonomy import (
    CATEGORY_KEYWORDS,
    SUBCATEGORY_KEYWORDS,
    EVENT_TYPE_KEYWORDS,
    ASSET_KEYWORDS,
    SECTOR_KEYWORDS,
)


class NewsClassifier:

    def __init__(self):
        self.reset()

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def reset(self):
        self._classified = 0
        self._unknown = 0
        self._rule_matches = 0
        self._ai_matches = 0

    # --------------------------------------------------
    # Classification
    # --------------------------------------------------

    def classify(self, processed_news: ProcessedNews) -> ClassifiedNews:
        
        # Pull text components out safely
        headline = processed_news.raw_news.headline or ""
        description = processed_news.raw_news.description or ""
        
        text = f"{headline} {description}".lower()

        # Classification Phase
        # --------------------
        # This engine performs deterministic
        # taxonomy-based classification only.
        #
        # No market scoring.
        # No impact estimation.
        # No trading decisions.
        
        category = self._find_match(
            text,
            CATEGORY_KEYWORDS,
            default="UNKNOWN"
        )

        subcategory = self._find_match(
            text,
            SUBCATEGORY_KEYWORDS,
            default="UNKNOWN"
        )

        event_type = self._find_match(
            text,
            EVENT_TYPE_KEYWORDS,
            default="UNKNOWN"
        )

        affected_assets = self._find_list(
            text,
            ASSET_KEYWORDS
        )

        affected_sectors = self._find_list(
            text,
            SECTOR_KEYWORDS
        )

        # --------------------------------------------------
        # Priority / Confidence scoring
        #
        # PREVIOUS BEHAVIOUR (bug): confidence/priority were
        # binary -- 0 if `category` stayed UNKNOWN, else a flat
        # 100 for every single item that matched even one
        # category keyword. A SEBI enforcement notice matching
        # the word "regulatory" scored identically (100/100) to
        # a genuine Tier-1 market-moving event. There was no
        # concept of "how much real signal does this item carry".
        #
        # FIX: score is now the count of independent taxonomy
        # dimensions that actually matched, weighted so a real
        # matched stock symbol -- the single most concrete,
        # actionable signal -- counts far more than a bare
        # category keyword hit. This also folds in the
        # collector's own source-tier priority (RawNews.priority,
        # e.g. SEBI/RBI collector-assigned HIGH vs PIB MEDIUM) as
        # a light floor, since regulators outrank generic press
        # releases even before taxonomy matching.
        # --------------------------------------------------
        affected_symbols_matched = processed_news.symbols or []

        signal_score = 0.0
        if category != "UNKNOWN":
            signal_score += 1.0
        if subcategory != "UNKNOWN":
            signal_score += 1.0
        if event_type != "UNKNOWN":
            signal_score += 1.0
        if affected_assets:
            signal_score += 1.0
        if affected_sectors:
            signal_score += 1.0
        if affected_symbols_matched:
            # A real, specific matched stock is worth more than
            # any of the taxonomy-only signals combined.
            signal_score += 4.0

        # Fix (2026-07-22): this denominator must equal the true
        # maximum achievable signal_score. The six checks above
        # add 1+1+1+1+1+4 = 9 when every one hits, but this was
        # hardcoded to 8 -- so a fully-matched story scored
        # (9/8)*100 = 112.5, exceeding the intended 0-100 bound.
        # Confirmed live 2026-07-22: VEDL and HINDZINC both showed
        # confidence=112 on the News Watchlist, reproducing this
        # exact arithmetic. A partially-matched story (5 of 6)
        # landed at exactly 100 -- also consistent with this bug.
        max_signal_score = 9.0
        computed_confidence = round(
            (signal_score / max_signal_score) * 100
        )

        source_priority_floor = self._source_priority_floor(
            processed_news.raw_news
        )

        classification_confidence = max(
            computed_confidence, 0
        )
        priority_score = max(
            computed_confidence, source_priority_floor
        )

        if category == "UNKNOWN" and not affected_symbols_matched:
            classification_method = "UNKNOWN"
            self._unknown += 1
        else:
            classification_method = "RULE"
            self._rule_matches += 1

        self._classified += 1

        # Construct and return the typed ClassifiedNews object
        return ClassifiedNews(
            news_id=processed_news.raw_news.id,
            headline=processed_news.raw_news.headline,
            summary=processed_news.raw_news.description,
            source=processed_news.raw_news.source,
            published_at=processed_news.raw_news.published_at,
            received_at=processed_news.raw_news.received_at,
            category=category,
            subcategory=subcategory,
            event_type=event_type,
            catalyst="",
            # TODO: Multiple sector support will be introduced in Story Builder V2.
            # MarketStoryBuilder currently expects a single sector.
            sector=affected_sectors[0] if affected_sectors else "",
            industry="",
            theme="",
            affected_symbols=processed_news.symbols,
            affected_assets=affected_assets,
            priority=priority_score,
            confidence=float(classification_confidence),
            classification_method=classification_method
        )

    # --------------------------------------------------

    @staticmethod
    def _source_priority_floor(raw_news):
        """
        Light floor derived from the collector's own source-tier
        priority tag (e.g. RegulatoryCollector marks RBI/SEBI feeds
        HIGH, PIB MEDIUM). This never pushes a no-signal item to a
        high score on its own -- it only nudges the floor, since
        signal_score above already dominates the final number.
        """
        raw_priority = getattr(raw_news, "priority", None)
        name = getattr(raw_priority, "name", None)
        if not name:
            name = str(raw_priority) if raw_priority is not None else ""

        tier = name.upper()

        if "HIGH" in tier:
            return 20
        if "MEDIUM" in tier:
            return 10
        return 0

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def _find_match(
        self,
        text,
        mapping,
        default
    ):
        for label, keywords in mapping.items():
            for keyword in keywords:
                if keyword in text:
                    return label
        return default

    # --------------------------------------------------

    def _find_list(
        self,
        text,
        mapping
    ):
        matches = []
        for label, keywords in mapping.items():
            for keyword in keywords:
                if keyword in text:
                    matches.append(label)
                    break
        return matches

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    def stats(self):
        return {
            "classified": self._classified,
            "unknown": self._unknown,
            "rule_matches": self._rule_matches,
            "ai_matches": self._ai_matches,
        }