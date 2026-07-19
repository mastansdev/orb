"""
News Collector

Responsibilities
----------------
Collect, normalize and queue raw news from multiple sources.

Owns:
    • News Queue
    • Duplicate Detection
    • Processing Status
    • Collection Statistics

Does NOT:
    • Classify News
    • Score News
    • Calculate Market Impact
    • Trigger Trades
    • Know Market Regime
    • Know Brain

This module is the entry point of the News Intelligence Pipeline.
"""

from collections import deque
from datetime import datetime
import uuid


class NewsCollector:
    """
    Collects raw news from different sources and provides
    a normalized queue for downstream intelligence modules.
    """

    def __init__(self):
        self.name = "NewsCollector"
        self.reset()

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def reset(self):
        self._queue = deque()

        self._processed_ids = set()

        self._received = 0
        self._duplicates = 0
        self._processed = 0

    # --------------------------------------------------
    # News Collection
    # --------------------------------------------------

    def add_news(
        self,
        source,
        headline,
        summary="",
        symbols=None,
        url="",
        timestamp=None,
    ):
        """
        Add raw news into the collector.

        Returns
        -------
        bool
            True  -> Accepted
            False -> Duplicate
        """

        if symbols is None:
            symbols = []

        if timestamp is None:
            timestamp = datetime.now()

        news_id = self._generate_news_id(
            source,
            headline
        )

        if news_id in self._processed_ids:
            self._duplicates += 1
            return False

        self._processed_ids.add(news_id)

        news = {
            "id": news_id,
            "timestamp": timestamp,
            "source": source,

            "headline": headline.strip(),
            "summary": summary.strip(),

            "symbols": list(symbols),

            # Filled later by NewsClassifier
            "category": None,

            # Filled later by ImpactEngine
            "impact": None,

            # Filled later by ImpactEngine
            "confidence": None,

            "url": url,

            "processed": False,
        }

        self._queue.append(news)

        self._received += 1

        return True

    # --------------------------------------------------
    # Retrieval
    # --------------------------------------------------

    def get_unprocessed_news(self):
        """
        Returns the oldest unprocessed news item.

        Returns None when queue is empty.
        """

        for news in self._queue:
            if not news["processed"]:
                return news

        return None

    # --------------------------------------------------

    def mark_processed(self, news_id):
        """
        Marks a news item as processed.
        """

        for news in self._queue:

            if news["id"] != news_id:
                continue

            if news["processed"]:
                return False

            news["processed"] = True

            self._processed += 1

            return True

        return False

    # --------------------------------------------------

    def pending_count(self):
        return sum(
            not news["processed"]
            for news in self._queue
        )

    # --------------------------------------------------

    def clear(self):
        self.reset()

    # --------------------------------------------------

    def stats(self):
        return {
            "received": self._received,
            "duplicates": self._duplicates,
            "processed": self._processed,
            "pending": self.pending_count(),
        }

    # --------------------------------------------------

    def queue(self):
        """
        Read-only queue snapshot.
        """
        return list(self._queue)

    # --------------------------------------------------
    # Internal
    # --------------------------------------------------

    @staticmethod
    def _generate_news_id(source, headline):
        """
        Generate a deterministic ID for duplicate detection.
        """

        key = f"{source}|{headline.strip().lower()}"

        return str(
            uuid.uuid5(
                uuid.NAMESPACE_DNS,
                key
            )
        )