from collections import deque

from repositories.intelligence_repository import (
    IntelligenceRepository,
)
from news_classifier import NewsClassifier
from market_story_builder import (
    MarketStoryBuilder,
)


class RailwayNewsEngine:
    """
    Pure Railway Intelligence Pipeline.

    Responsibilities
    ----------------
    - Receive RawNews
    - Classify News
    - Build Market Stories
    - Persist Intelligence

    Never:
    - Trade
    - Connect to Dhan
    - Use Brain
    """

    def __init__(self):
        self.news_queue = deque()
        self.classifier = NewsClassifier()
        self.story_builder = MarketStoryBuilder()
        self.repository = IntelligenceRepository()
        self.collectors = []

    # --------------------------------------------------
    def register_collector(self, collector):
        self.collectors.append(collector)

        print(f"[RAILWAY] Collector Registered : {collector.name}")

    # --------------------------------------------------
    def collect(self):
        total_news = 0

        for collector in self.collectors:
            try:
                news_items = collector.collect()

                for news in news_items:
                    if self._validate(news):
                        self.news_queue.append(news)
                        total_news += 1

            except Exception as e:
                print(f"[RAILWAY ERROR] " f"{collector.name} : {e}")

        return total_news

    # --------------------------------------------------
    def _validate(self, news):
        if news is None:
            return False

        if not news.headline:
            return False

        return True