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

from news_models import (
    ClassifiedNews,
    ProcessedNews,
)
from news_taxonomy import (
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

        if category == "UNKNOWN":
            classification_method = "UNKNOWN"
            classification_confidence = 0
            self._unknown += 1
        else:
            classification_method = "RULE"
            classification_confidence = 100
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
            priority=classification_confidence,
            confidence=float(classification_confidence),
            classification_method=classification_method
        )

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