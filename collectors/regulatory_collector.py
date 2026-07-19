"""
==========================================================
Regulatory RSS Collector  (SEBI / RBI / PIB)
==========================================================

Mission
-------
Collect news from India's primary regulatory carriers —
the sources that CREATE market-moving events rather
than report them:

    • SEBI  — orders, circulars, enforcement
    • RBI   — policy, circulars, press releases
    • PIB   — government press releases, cabinet
              decisions, ministry announcements

Responsibilities
----------------
1. Fetch regulatory RSS feeds
2. Convert entries into RawNews with correct source,
   category, and priority
3. Return List[RawNews]

This class NEVER:
- Parses catalysts
- Creates Evidence
- Makes decisions

Author : H&M ORB AUTO TRADER
==========================================================
"""

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List

import feedparser
import requests

from collectors.base_collector import BaseCollector
from news.news_models import (
    RawNews,
    NewsSource,
    NewsCategory,
    NewsPriority,
    NewsSentiment,
)


class RegulatoryCollector(BaseCollector):

    REQUEST_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0 Safari/537.36"
        ),
        "Accept": (
            "application/rss+xml, application/xml, "
            "text/xml, */*"
        ),
    }

    REQUEST_TIMEOUT_SECONDS = 15

    # Each feed carries its own source/category/priority
    # mapping — regulators outrank media by default.
    FEEDS = [
        {
            "url": "https://www.rbi.org.in/pressreleases_rss.xml",
            "source": NewsSource.RBI,
            "category": NewsCategory.POLICY,
            "priority": NewsPriority.HIGH,
        },
        {
            "url": "https://www.rbi.org.in/notifications_rss.xml",
            "source": NewsSource.RBI,
            "category": NewsCategory.REGULATORY,
            "priority": NewsPriority.HIGH,
        },
        {
            "url": "https://www.sebi.gov.in/sebirss.xml",
            "source": NewsSource.SEBI,
            "category": NewsCategory.REGULATORY,
            "priority": NewsPriority.HIGH,
        },
        {
            # PIB All-Ministries press releases (English)
            "url": (
                "https://pib.gov.in/RssMain.aspx"
                "?ModId=6&Lang=1&Regid=3"
            ),
            "source": NewsSource.GOVERNMENT,
            "category": NewsCategory.GOVERNMENT,
            "priority": NewsPriority.MEDIUM,
        },
    ]

    def __init__(self):
        super().__init__("REGULATORY (SEBI/RBI/PIB)")

    # --------------------------------------------------

    def collect(self) -> List[RawNews]:

        news_items = []

        for feed_config in self.FEEDS:

            url = feed_config["url"]

            try:
                response = requests.get(
                    url,
                    headers=self.REQUEST_HEADERS,
                    timeout=self.REQUEST_TIMEOUT_SECONDS,
                )
                response.raise_for_status()

                feed = feedparser.parse(response.content)

                if feed.bozo and not feed.entries:
                    print(
                        f"[REGULATORY] Invalid feed: {url}"
                    )
                    continue

                for entry in feed.entries:

                    headline = getattr(
                        entry, "title", ""
                    ).strip()

                    if not headline:
                        continue

                    news_items.append(
                        RawNews(
                            headline=headline,
                            description=(
                                getattr(entry, "summary", "")
                                or ""
                            ),
                            source=feed_config["source"],
                            category=feed_config["category"],
                            priority=feed_config["priority"],
                            sentiment=NewsSentiment.UNKNOWN,
                            published_at=self._published_at(
                                entry
                            ),
                            url=getattr(entry, "link", "")
                            or "",
                        )
                    )

            except Exception as e:
                print(
                    f"[REGULATORY] {url} failed: "
                    f"{str(e)[:120]}"
                )

        return self.validate_all(news_items)

    # --------------------------------------------------

    @staticmethod
    def _published_at(entry):
        raw = getattr(entry, "published", "") or getattr(
            entry, "updated", ""
        )

        if raw:
            try:
                return parsedate_to_datetime(raw)
            except Exception:
                pass

        return datetime.now()
