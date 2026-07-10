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

from copy import deepcopy

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

    def classify(self, news):

        news = deepcopy(news)

        text = (
            news.get("headline", "")
            + " "
            + news.get("summary", "")
        ).lower()

        news["category"] = self._find_match(
            text,
            CATEGORY_KEYWORDS,
            default="UNKNOWN"
        )

        news["sub_category"] = self._find_match(
            text,
            SUBCATEGORY_KEYWORDS,
            default="UNKNOWN"
        )

        news["event_type"] = self._find_match(
            text,
            EVENT_TYPE_KEYWORDS,
            default="UNKNOWN"
        )

        news["affected_assets"] = self._find_list(
            text,
            ASSET_KEYWORDS
        )

        news["affected_sectors"] = self._find_list(
            text,
            SECTOR_KEYWORDS
        )

        if news["category"] == "UNKNOWN":

            news["classification_method"] = "UNKNOWN"
            news["classification_confidence"] = 0

            self._unknown += 1

        else:

            news["classification_method"] = "RULE"
            news["classification_confidence"] = 100

            self._rule_matches += 1

        self._classified += 1

        return news

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