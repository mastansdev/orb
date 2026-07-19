from collections import deque

from repositories.intelligence_repository import (
    IntelligenceRepository,
)
from news.news_classifier import NewsClassifier
from news.market_story_builder import (
    MarketStoryBuilder,
)
from collectors.bse_corporate_collector import (
    BSECorporateCollector,
)
from collectors.news_rss_collector import (
    NewsRSSCollector,
)
from collectors.regulatory_collector import (
    RegulatoryCollector,
)
from news.news_models import (
    ProcessedNews,
)
from news.symbol_matcher import symbol_matcher


class RailwayNewsEngine:
    """
    Pure Railway Intelligence Pipeline.

    Responsibilities
    ----------------
    - Receive RawNews
    - Classify News
    - Match affected stock symbols
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

        self.register_collector(
            NewsRSSCollector()
        )

        # Primary regulatory carriers: SEBI / RBI / PIB
        self.register_collector(
            RegulatoryCollector()
        )

    # --------------------------------------------------
    def register_collector(self, collector):
        self.collectors.append(collector)
        print(f"[RAILWAY] Collector Registered : {collector.name}")

    # --------------------------------------------------
    def collect(self):
        total_news = 0

        for collector in self.collectors:
            try:
                print(f"[COLLECTOR] {collector.name}")
                news_items = collector.collect()
                print(f"[COLLECTOR] Received : {len(news_items)}")

                duplicates = 0
                for news in news_items:

                    if not self._validate(news):
                        continue

                    news_hash = self.repository.generate_news_hash(
                        news
                    )

                    if self.repository.news_exists(
                        news_hash
                    ):
                        duplicates += 1
                        continue

                    self.repository.save_raw_news(
                        news,
                        news_hash
                    )

                    # --- RAW NEWS MONITOR ---
                    print()
                    print("=" * 80)
                    print("NEW RAW NEWS")
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

                print()
                print("=" * 60)
                print(f"{collector.name} COLLECTION SUMMARY")
                print("=" * 60)
                print(f"Fetched      : {len(news_items)}")
                print(f"New          : {total_news}")
                print(f"Duplicates   : {duplicates}")
                print("=" * 60)

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

                # --------------------------------------
                # Symbol Matching
                #
                # Matches the headline + description against
                # the stock universe (company names, tickers,
                # curated keywords) to identify which specific
                # stocks this news item affects. Without this,
                # stories only carry a broad sector/category tag
                # with no link to an actual tradeable symbol.
                # --------------------------------------
                matched_symbols = symbol_matcher.match(
                    f"{raw_news.headline} {raw_news.description}"
                )
                processed.symbols = matched_symbols

                if matched_symbols:
                    print(f"[SYMBOL MATCH] {matched_symbols}")
                
                self.stats_data["processed"] += 1

                classified = self.classifier.classify(
                    processed
                )

                # --- CLASSIFICATION MONITOR ---
                print()
                print("=" * 80)
                print("CLASSIFICATION")
                print("=" * 80)
                print(f"Headline       : {raw_news.headline}")
                
                if hasattr(classified, "classification"):
                    print(f"Classification : {classified.classification}")
                if hasattr(classified, "priority"):
                    print(f"Priority       : {classified.priority}")
                if hasattr(classified, "sentiment"):
                    print(f"Sentiment      : {classified.sentiment}")
                if hasattr(classified, "confidence"):
                    print(f"Confidence     : {classified.confidence}")
                if hasattr(classified, "affected_symbols"):
                    print(f"Symbols        : {classified.affected_symbols}")
                
                print("=" * 80)
                # ------------------------------

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