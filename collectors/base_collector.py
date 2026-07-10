"""
==========================================================
Base Collector
==========================================================

Mission
-------
Defines the standard interface for every News Collector.

Every collector must inherit this class and implement
the collect() method.

Responsibilities
----------------
1. Provide a common interface
2. Standardize collector behavior
3. Return RawNews objects only

This class NEVER:
- Parses catalysts
- Creates Evidence
- Executes trades
- Makes decisions

Author : H&M ORB AUTO TRADER
==========================================================
"""

from abc import ABC, abstractmethod
from typing import List

from news_models import RawNews


class BaseCollector(ABC):
    """
    Abstract base class for all market news collectors.
    """

    def __init__(self, name: str):

        self.name = name

    # --------------------------------------------------

    @abstractmethod
    def collect(self) -> List[RawNews]:
        """
        Fetch latest news from the source.

        Returns
        -------
        List[RawNews]
        """
        pass

    # --------------------------------------------------

    def validate(self, news: RawNews) -> bool:
        """
        Basic validation before accepting news.
        """

        if not news.headline:
            return False

        if not news.source:
            return False

        return True

    # --------------------------------------------------

    def validate_all(
        self,
        news_list: List[RawNews]
    ) -> List[RawNews]:
        """
        Filters invalid news items.
        """

        valid_news = []

        for news in news_list:

            if self.validate(news):

                valid_news.append(news)

        return valid_news

    # --------------------------------------------------

    def __repr__(self):

        return f"{self.__class__.__name__}(name='{self.name}')"