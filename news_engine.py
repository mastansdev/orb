"""
==========================================================
News Engine
==========================================================

Mission
-------
Central orchestrator of the News Intelligence System.

Responsibilities
----------------
1. Register collectors
2. Poll collectors
3. Validate incoming RawNews
4. Deduplicate news
5. Queue incoming news
6. Persist raw news
7. Orchestrate the complete News Intelligence pipeline
8. Return standardized Evidence objects

This engine NEVER:
- Executes trades
- Creates catalysts
- Makes trading decisions

Author : H&M ORB AUTO TRADER
==========================================================
"""

from collections import deque
from datetime import datetime
from intelligence_repository import (
    IntelligenceRepository,
)
import hashlib
import sqlite3
from typing import List

from news_models import (
    RawNews,
    ProcessedNews,
)
from news_classifier import NewsClassifier
from market_story_builder import (
    MarketStoryBuilder,
)

class NewsEngine:

    def __init__(self, context=None):

        self.context = context

        self.collectors = []

        self.news_queue = deque()

        self.classifier = NewsClassifier()
        self.story_builder = MarketStoryBuilder()
        
        # Market Intelligence State
        if context is not None:
            self.market_catalyst = context.market_catalyst
            self.market_memory = context.market_memory
            self.market_environment = context.market_environment
        else:
            self.market_catalyst = None
            self.market_memory = None
            self.market_environment = None
        
        self.repository = IntelligenceRepository()

        self.db = sqlite3.connect(
            "news_engine.db",
            check_same_thread=False
        )

        self.cursor = self.db.cursor()

        self._create_tables()

    # --------------------------------------------------

    def _create_tables(self):

        self.cursor.execute("""

        CREATE TABLE IF NOT EXISTS news_raw(

            id TEXT PRIMARY KEY,

            headline TEXT,

            source TEXT,

            published_at TEXT,

            received_at TEXT,

            hash TEXT UNIQUE

        )

        """)

        self.db.commit()

    # --------------------------------------------------

    def register_collector(self, collector):

        self.collectors.append(collector)

        print(
            f"[NEWS] Collector Registered : {collector.name}"
        )

    # --------------------------------------------------

    def collect(self):

        total_news = 0

        for collector in self.collectors:

            try:

                news_items = collector.collect()

                for news in news_items:

                    if self._validate(news):

                        if not self._is_duplicate(news):

                            print(
                                f"[NEWS ACCEPTED] "
                                f"{news.source.value} | "
                                f"{news.headline}"
                            )

                            self.news_queue.append(news)

                            self._store(news)

                            total_news += 1

            except Exception as e:

                print(

                    f"[NEWS ERROR] "

                    f"{collector.name} : {e}"

                )

        return total_news

    # --------------------------------------------------

    def process(self):
        """
        Process queued RawNews through the complete
        News Intelligence pipeline.

        Returns:
            List[Evidence]
        """

        evidence_list = []

        while self.news_queue:

            # ----------------------------------------------
            # Raw News
            # ----------------------------------------------
            raw_news = self.news_queue.popleft()

            # ----------------------------------------------
            # Processed News
            # ----------------------------------------------
            processed_news = ProcessedNews(
                raw_news=raw_news
            )

            # ----------------------------------------------
            # Classified News
            # ----------------------------------------------
            classified_news = self.classifier.classify(
                processed_news
            )

            # ----------------------------------------------
            # Market Stories
            # ----------------------------------------------
            stories = self.story_builder.build(
                [classified_news]
            )

            # ----------------------------------------------
            # Impact
            # ----------------------------------------------
            for story in stories:

                # ------------------------------------------
                # Persist Intelligence
                # ------------------------------------------

                self.repository.save_story(
                     story,
                    
                )

        return evidence_list
    
    # --------------------------------------------------

    def _validate(self, news: RawNews):

        if news is None:

            return False

        if not news.headline:

            return False

        return True

    # --------------------------------------------------

    def _hash(self, news: RawNews):

        text = (

            news.headline.lower()

            + str(news.published_at)

            + news.source.value

        )

        return hashlib.sha256(

            text.encode()
        ).hexdigest()

    # --------------------------------------------------

    def _is_duplicate(self, news: RawNews):

        news_hash = self._hash(news)

        self.cursor.execute(

            "SELECT hash FROM news_raw WHERE hash=?",

            (news_hash,)

        )

        row = self.cursor.fetchone()

        return row is not None

    # --------------------------------------------------

    def _store(self, news: RawNews):

        news_hash = self._hash(news)

        self.cursor.execute(

            """

            INSERT OR IGNORE INTO news_raw

            VALUES(?,?,?,?,?,?)

            """,

            (

                news.id,

                news.headline,

                news.source.value,

                str(news.published_at),

                str(news.received_at),

                news_hash

            )

        )

        self.db.commit()

    # --------------------------------------------------

    def queue_size(self):

        return len(self.news_queue)

    # --------------------------------------------------

    def health(self):

        return {

            "collectors": len(self.collectors),

            "queue": len(self.news_queue),

            "database": "CONNECTED"

        }