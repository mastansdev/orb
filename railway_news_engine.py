import re
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

# --------------------------------------------------
# Ingestion-level noise filters
#
# These patterns are boilerplate from SEBI's individual
# enforcement/recovery-proceedings feed (recovery certificates,
# demand notices, account attachments, adjudication orders,
# appeals). They target a single named defaulter over a personal
# case -- never a listed company or a tradeable event -- but they
# mechanically mention "BSE"/"NSE" as the venue where the illiquid
# options were dealt in, which was causing the symbol matcher to
# false-positive match ticker BSE (and, via keyword bleed, ONGC/
# OIL/ANANDRATHI/CHOICEIN) on every single one of them, each
# scored Priority=100/Confidence=100 as if it were real news.
#
# GOVERNMENT source (PIB) is dropped entirely per explicit
# decision: PIB press releases are general Hindi-language
# government/events coverage (ministerial visits, awards,
# inaugurations) -- not market intelligence, not useful to the bot.
# --------------------------------------------------
NOISE_HEADLINE_PATTERNS = [
    r"recovery certificate",
    r"notice of demand",
    r"notice\(?s?\)?\s+of\s+attachment",
    r"adjudication order",
    r"remittance advice",
    r"\bdefaulter\b",
    r"illiquid stock(?:s)? options",
    r"^appeal no\.",
    r"summary settlement order",
    r"caution to regulated entities",
    r"PAN\s*:\s*[A-Z]{5}\d{4}[A-Z]",
]
NOISE_HEADLINE_RE = re.compile(
    "|".join(NOISE_HEADLINE_PATTERNS), re.IGNORECASE
)

NOISE_SOURCE_SUBSTRINGS = ("GOVERNMENT",)


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
        grand_total_news = 0

        for collector in self.collectors:
            try:
                print(f"[COLLECTOR] {collector.name}")
                news_items = collector.collect()
                print(f"[COLLECTOR] Received : {len(news_items)}")

                duplicates = 0
                filtered_noise = 0
                new_this_collector = 0

                for news in news_items:

                    if not self._validate(news):
                        continue

                    if self._is_noise(news):
                        filtered_noise += 1
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
                    new_this_collector += 1
                    grand_total_news += 1

                print()
                print("=" * 60)
                print(f"{collector.name} COLLECTION SUMMARY")
                print("=" * 60)
                print(f"Fetched      : {len(news_items)}")
                print(f"New          : {new_this_collector}")
                print(f"Duplicates   : {duplicates}")
                print(f"Filtered     : {filtered_noise} (noise/irrelevant)")
                print("=" * 60)

            except Exception as e:
                print(f"[RAILWAY ERROR] {collector.name}")
                print(e)

        return grand_total_news

    # --------------------------------------------------
    def _validate(self, news):
        if news is None:
            return False

        if not news.headline:
            return False

        return True

    # --------------------------------------------------
    def _is_noise(self, news):
        """
        True if this item should never reach classification,
        symbol matching, or storage at all -- see the noise
        pattern comment block at the top of this file.
        """
        source_str = str(news.source).upper()
        if any(s in source_str for s in NOISE_SOURCE_SUBSTRINGS):
            return True

        if NOISE_HEADLINE_RE.search(news.headline or ""):
            return True

        return False

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