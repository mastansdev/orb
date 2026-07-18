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
import requests

from collectors.base_collector import BaseCollector
from news_models import (
    RawNews,
    NewsSource,
    NewsCategory,
    NewsPriority,
    NewsSentiment,
)


class NewsRSSCollector(BaseCollector):

    # Many news sites block or reject requests that don't identify
    # as a real browser, and instead return a blocked/error page.
    # feedparser would then try to parse that error page as RSS and
    # fail (reported as feed.bozo), even though the feed itself is
    # fine. Fetching with a proper header first avoids this.
    REQUEST_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0 Safari/537.36"
        ),
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }

    REQUEST_TIMEOUT_SECONDS = 10

    def __init__(self):
        super().__init__("NEWS RSS")
        self.feeds = [
            # Economic Times Markets
            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",

            # LiveMint Markets
            "https://www.livemint.com/rss/markets",

            # NOTE: Moneycontrol and Business Standard removed --
            # both are blocked by anti-bot protection that a
            # standard header fix could not get past (Moneycontrol:
            # persistent invalid-feed error; Business Standard:
            # explicit 403 Forbidden). Revisit later with more
            # specialized tooling if these sources become important.
        ]

    # --------------------------------------------------

    def collect(self) -> List[RawNews]:
        news_items = []

        for url in self.feeds:
            try:
                response = requests.get(
                    url,
                    headers=self.REQUEST_HEADERS,
                    timeout=self.REQUEST_TIMEOUT_SECONDS,
                )
                response.raise_for_status()

                feed = feedparser.parse(response.content)

                # Upgrade 3: Check for malformed RSS feeds using feed.bozo
                if feed.bozo:
                    print(f"[RSS WARNING] Invalid RSS Feed: {url}")
                    continue

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