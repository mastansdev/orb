from collections import deque

from repositories.intelligence_repository import (
    IntelligenceRepository,
)
from news_classifier import NewsClassifier
from market_story_builder import (
    MarketStoryBuilder,
)
from collectors.bse_corporate_collector import (
    BSECorporateCollector,
)
from news_models import (
    ProcessedNews,
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
        
        self.stats_data = {
            "collected": 0,
            "processed": 0,
            "stories": 0,
            "saved": 0,
        }

        self.register_collector(
            BSECorporateCollector()
        )

    # --------------------------------------------------
    def register_collector(self, collector):
        self.collectors.append(collector)
        print(f"[RAILWAY] Collector Registered : {collector.name}")

    # --------------------------------------------------
    # Improved collect() loop with tracking logs and Raw News Monitor
    def collect(self):
        total_news = 0

        for collector in self.collectors:
            try:
                print(f"[COLLECTOR] {collector.name}")
                news_items = collector.collect()
                print(f"[COLLECTOR] Received : {len(news_items)}")

                for news in news_items:
                    if self._validate(news):
                        # --- RAW NEWS MONITOR ---
                        print()
                        print("=" * 80)
                        print("RAW NEWS RECEIVED")
                        print("=" * 80)
                        print(f"Source    : {news.source}")
                        print(f"Headline  : {news.headline}")
                        print(f"Published : {news.published_at}")

                        if hasattr(news, "url"):
                            print(f"URL       : {news.url}")

                        print("=" * 80)
                        # -------------------------

                        self.news_queue.append(news)
                        total_news += 1

            except Exception as e:
                print(f"[RAILWAY ERROR] {collector.name}")
                print(e)

        return total_news

    # --------------------------------------------------
    def _validate(self, news):
        if news is None:
            return False

        if not news.headline:
            return False

        return True

    # --------------------------------------------------
    def process(self):
        stories_created = 0

        while self.news_queue:
            raw_news = self.news_queue.popleft()
            try:
                processed = ProcessedNews(
                    raw_news=raw_news
                )
                
                self.stats_data["processed"] += 1

                classified = self.classifier.classify(
                    processed
                )

                stories = self.story_builder.build(
                    [classified]
                )

                for story in stories:
                    self.repository.save_story(
                        story
                    )
                    stories_created += 1
                    
            except Exception as e:
                print(f"[PROCESS ERROR] {e}")

        self.stats_data["stories"] += stories_created
        self.stats_data["saved"] += stories_created

        return stories_created

    # --------------------------------------------------
    def run(self):
        collected = self.collect()
        self.stats_data["collected"] += collected

        stories = self.process()

        print()
        print("=" * 60)
        print("Railway Cycle Complete")
        print("=" * 60)
        print(f"Collected : {collected}")
        print(f"Stories   : {stories}")
        print("=" * 60)
        
        return self.stats()

    # --------------------------------------------------
    def stats(self):
        return self.stats_data

    # --------------------------------------------------
    def health(self):
        return {
            "collectors": len(self.collectors),
            "queue": len(self.news_queue),
            "stories": self.stats_data["stories"],
            "saved": self.stats_data["saved"],
            "status": "HEALTHY",
        }