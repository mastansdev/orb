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

                for entry in feed.entries:

                    news = RawNews(

                        headline=getattr(entry, "title", ""),

                        description=getattr(entry, "summary", ""),

                        source=NewsSource.UNKNOWN,

                        category=NewsCategory.UNKNOWN,

                        priority=NewsPriority.INFO,

                        sentiment=NewsSentiment.UNKNOWN,

                        published_at=datetime.now(),

                        received_at=datetime.now(),

                        url=getattr(entry, "link", "")

                    )

                    news_items.append(news)

            except Exception as e:

                print(f"[RSS ERROR] {url}")

                print(e)

        return self.validate_all(news_items)