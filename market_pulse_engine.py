"""
==========================================================
Market Pulse Engine
==========================================================

Mission
-------
Continuously observe the LIVE market and measure
whether money is actually flowing.

This engine NEVER:
- Buys
- Sells
- Scores trades
- Executes positions

Responsibilities
----------------
1. Observe overall market health
2. Observe sector participation
3. Observe industry participation
4. Observe theme participation
5. Observe breadth
6. Observe market regime
7. Supply live evidence to Brain

Author : H&M ORB AUTO TRADER
==========================================================
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List


# ==========================================================
# Market Regime
# ==========================================================

class MarketRegime(Enum):

    UNKNOWN = "UNKNOWN"

    TRENDING_UP = "TRENDING_UP"

    TRENDING_DOWN = "TRENDING_DOWN"

    RANGE = "RANGE"

    VOLATILE = "VOLATILE"


# ==========================================================
# Observation
# ==========================================================

@dataclass
class PulseObservation:

    timestamp: datetime

    source: str

    message: str


# ==========================================================
# Market Snapshot
# ==========================================================

@dataclass
class MarketSnapshot:

    timestamp: datetime = field(default_factory=datetime.now)

    market_regime: MarketRegime = MarketRegime.UNKNOWN

    market_breadth: float = 0.0

    advancing: int = 0

    declining: int = 0

    unchanged: int = 0

    active_themes: List[str] = field(default_factory=list)

    active_industries: List[str] = field(default_factory=list)

    strongest_sector: str = ""

    weakest_sector: str = ""

    strongest_industry: str = ""

    weakest_industry: str = ""

    strongest_theme: str = ""

    weakest_theme: str = ""

    observations: List[PulseObservation] = field(default_factory=list)

    def add_observation(
        self,
        source: str,
        message: str
    ):

        self.observations.append(

            PulseObservation(

                timestamp=datetime.now(),

                source=source,

                message=message

            )

        )


# ==========================================================
# Market Pulse Engine
# ==========================================================

class MarketPulseEngine:

    """
    Observes the LIVE market continuously.

    This engine only measures.

    It NEVER decides.
    """

    def __init__(self):

        self.current_snapshot = MarketSnapshot()

        self.market_memory: List[MarketSnapshot] = []

    # ------------------------------------------------------

    def update_market_regime(

        self,

        regime: MarketRegime

    ):

        self.current_snapshot.market_regime = regime

        self.current_snapshot.add_observation(

            "ENGINE",

            f"Market regime changed to {regime.value}"

        )

    # ------------------------------------------------------

    def update_market_breadth(

        self,

        advancing: int,

        declining: int,

        unchanged: int

    ):

        total = advancing + declining + unchanged

        breadth = 0.0

        if total:

            breadth = advancing / total

        self.current_snapshot.advancing = advancing

        self.current_snapshot.declining = declining

        self.current_snapshot.unchanged = unchanged

        self.current_snapshot.market_breadth = breadth

    # ------------------------------------------------------

    def update_sector_strength(

        self,

        strongest: str,

        weakest: str

    ):

        self.current_snapshot.strongest_sector = strongest

        self.current_snapshot.weakest_sector = weakest

    # ------------------------------------------------------

    def update_industry_strength(

        self,

        strongest: str,

        weakest: str

    ):

        self.current_snapshot.strongest_industry = strongest

        self.current_snapshot.weakest_industry = weakest

    # ------------------------------------------------------

    def update_theme_strength(

        self,

        strongest: str,

        weakest: str

    ):

        self.current_snapshot.strongest_theme = strongest

        self.current_snapshot.weakest_theme = weakest

    # ------------------------------------------------------

    def set_active_themes(

        self,

        themes: List[str]

    ):

        self.current_snapshot.active_themes = themes

    # ------------------------------------------------------

    def set_active_industries(

        self,

        industries: List[str]

    ):

        self.current_snapshot.active_industries = industries

    # ------------------------------------------------------

    def save_snapshot(self):

        self.market_memory.append(

            self.current_snapshot

        )

        self.current_snapshot = MarketSnapshot()

    # ------------------------------------------------------

    def get_current_snapshot(self):

        return self.current_snapshot

    # ------------------------------------------------------

    def get_market_memory(self):

        return self.market_memory