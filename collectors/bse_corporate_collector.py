"""
==========================================================
BSE Corporate Collector
==========================================================

Mission
-------
Collect the latest corporate announcements from BSE
and convert them into RawNews objects.

Responsibilities
----------------
1. Connect to BSE
2. Fetch latest announcements
3. Convert announcements into RawNews
4. Return List[RawNews]

This collector NEVER:
- Polls forever
- Sleeps
- Prints
- Logs
- Deduplicates
- Scores news

Author : H&M ORB AUTO TRADER
==========================================================
"""

from typing import List
from datetime import datetime

from bse import BSE

from news.news_models import (
    RawNews,
    NewsSource,
)

# --------------------------------------------------
# High Value Announcement Categories
# --------------------------------------------------

ALLOWED_CATEGORIES = {
    "Board Meeting",
    "Company Update",
    "Result",
    "Financial Results",
}

ALLOWED_SUBCATEGORIES = {
    "Acquisition",
    "Board Meeting",
    "Buyback",
    "Dividend",
    "Bonus",
    "Split",
    "Merger",
    "Amalgamation",
    "Fund Raising",
    "Preferential Issue",
    "QIP",
    "Rights Issue",
    "Credit Rating",
    "Order",
    "Order Win",
    "Contract",
    "Expansion",
    "Capacity Expansion",
}

# --------------------------------------------------
# Ignore Completely
# --------------------------------------------------

IGNORE_SUBCATEGORIES = {
    "Newspaper Publication",
    "AGM",
    "EGM",
    "Annual Report",
    "Business Responsibility and Sustainability Reporting (BRSR)",
    "Certificate under Reg. 74 (5) of SEBI (DP) Regulations, 2018",
    "General",
}


class BSECorporateCollector:

    name = "BSE Corporate"

    def __init__(self):
        # Kept as required to avoid the TypeError
        self.bse = BSE(
            download_folder="./"
        )

    # --------------------------------------------------

    def collect(self) -> List[RawNews]:

        news_list = []

        try:
            response = self.bse.announcements(
                page_no=1
            )

            announcements = response.get(
                "Table",
                []
            )

            for item in announcements:
                # Fixed to map correctly to the real BSE JSON payload
                category = (
                      item.get("CATEGORYNAME") or ""
                ).strip()

                subcategory = (
                    item.get("SUBCATNAME") or ""
                ).strip()

                # 1. Drop ignored categories immediately
                if subcategory in IGNORE_SUBCATEGORIES:
                    continue

                # 2. Keep if it explicitly hits either allowed group
                if category in ALLOWED_CATEGORIES or subcategory in ALLOWED_SUBCATEGORIES:
                    
                    critical = item.get("CRITICALNEWS", 0)
                    if not critical and subcategory not in ALLOWED_SUBCATEGORIES:
                        continue
                    
                    published_at = datetime.fromisoformat(
                        item.get(
                            "News_submission_dt",
                            datetime.now().isoformat()
                        )
                    )
                    
                    news = RawNews(
                        headline=item.get(
                            "HEADLINE",
                            ""
                        ),
                        description=item.get(
                            "MORE",
                            ""
                        ),
                        source=NewsSource.BSE,
                        published_at=published_at,
                        received_at=datetime.now(),
                        url=item.get(
                            "NSURL",
                            ""
                        ),
                    )
                    
                    news_list.append(news)
                    


        except Exception:
            raise

        return news_list