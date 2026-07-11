"""
==========================================================
News RSS Collector
==========================================================

Mission
-------
Collect market news from trusted RSS feeds and convert
them into RawNews objects.

Responsibilities
----------------
1. Fetch RSS feeds
2. Parse feed entries
3. Create RawNews objects
4. Return List[RawNews]

Author : H&M ORB AUTO TRADER
==========================================================
"""

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List

import feedparser

from collectors.base_collector import BaseCollector
from news_models import (
    RawNews,
    NewsSource,
    NewsCategory,
    NewsPriority,
    NewsSentiment,
)


class NewsRSSCollector(BaseCollector):

    def __init__(self):
        super().__init__("NEWS RSS")
        self.feeds = [
            # Moneycontrol
            "https://www.moneycontrol.com/rss/business.xml",

            # Economic Times Markets
            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",

            # LiveMint Markets
            "https://www.livemint.com/rss/markets",

            # Business Standard Markets
            "https://www.business-standard.com/rss/markets-106.rss"
        ]

    # --------------------------------------------------

    def collect(self) -> List[RawNews]:
        news_items = []

        for url in self.feeds:
            try:
                feed = feedparser.parse(url)

                # Upgrade 3: Check for malformed RSS feeds using feed.bozo
                if feed.bozo:
                    print(f"[RSS WARNING] Invalid RSS Feed: {url}")

                for entry in feed.entries:
                    # Upgrade 4: Validate and strip headline, skipping empty entries
                    headline = getattr(entry, "title", "").strip()
                    if not headline:
                        continue

                    news = RawNews(
                        headline=headline,
                        description=getattr(entry, "summary", "") or "",
                        source=self._get_source(url),          # Upgrade 1: Dynamic source matching
                        category=NewsCategory.UNKNOWN,
                        priority=NewsPriority.INFO,
                        sentiment=NewsSentiment.UNKNOWN,
                        published_at=self._published_time(entry), # Upgrade 2: Parse publisher timestamp
                        received_at=datetime.now(),
                        url=getattr(entry, "link", "")
                    )
                    news_items.append(news)

            except Exception as e:
                print(f"[RSS ERROR] {url}")
                print(e)

        return self.validate_all(news_items)

    # --------------------------------------------------

    def _get_source(self, url: str) -> NewsSource:
        url = url.lower()

        if "moneycontrol" in url:
            return NewsSource.MONEYCONTROL

        if "economictimes" in url:
            return NewsSource.ET

        if "livemint" in url:
            return NewsSource.MINT

        if "reuters" in url:
            return NewsSource.REUTERS

        if "bloomberg" in url:
            return NewsSource.BLOOMBERG

        return NewsSource.UNKNOWN

    # --------------------------------------------------

    def _published_time(
            self,
            entry
    ) -> datetime:
        published = getattr(entry, "published", None)

        if published:
            try:
                return parsedate_to_datetime(published)
            except Exception:
                pass

        return datetime.now()