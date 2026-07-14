from news_engine import NewsEngine

from collectors.news_rss_collector import NewsRSSCollector
from collectors.bse_corporate_collector import BSECorporateCollector

from market_catalyst import MarketCatalyst
from market_memory import MarketMemory
from market_environment import MarketEnvironment
from intelligence_context import IntelligenceContext

class IntelligenceBootstrap:

    def __init__(self):

        # ---------------------------------
        # Market Intelligence State
        # ---------------------------------

        self.market_catalyst = MarketCatalyst()
        self.market_memory = MarketMemory()
        self.market_environment = MarketEnvironment()

        # ---------------------------------
        # Intelligence Context
        # ---------------------------------

        self.context = IntelligenceContext()

        self.context.market_catalyst = self.market_catalyst
        self.context.market_memory = self.market_memory
        self.context.market_environment = self.market_environment
                        
        # ---------------------------------
        # News Engine
        # ---------------------------------

        self.news_engine = NewsEngine(self.context)

        self.news_engine.register_collector(
            NewsRSSCollector()
        )

        self.news_engine.register_collector(
            BSECorporateCollector()
        )

              