"""
==========================================================
Market Catalyst Engine
==========================================================

Mission
-------
Observe external market catalysts, classify them into
structured market intelligence and preserve market memory.

This engine NEVER:
- Buys
- Sells
- Scores trades
- Executes positions

Responsibilities
----------------
1. Receive catalyst events
2. Classify catalysts
3. Map market impact
4. Maintain active catalysts
5. Preserve catalyst memory
6. Supply catalyst intelligence to Brain

Author : H&M ORB AUTO TRADER
==========================================================
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
import uuid


# ==========================================================
# Catalyst Types
# ==========================================================

class CatalystType(Enum):

    CORPORATE = "Corporate"

    COMMODITY = "Commodity"

    MACRO = "Macro"

    GLOBAL = "Global"

    GOVERNMENT = "Government"

    RESULT = "Result"

    UNKNOWN = "Unknown"


# ==========================================================
# Catalyst Impact
# ==========================================================

class Impact(Enum):

    LOW = 1

    MEDIUM = 2

    HIGH = 3

    EXTREME = 4


# ==========================================================
# Catalyst Status
# ==========================================================

class CatalystStatus(Enum):

    NEW = "NEW"

    ACTIVE = "ACTIVE"

    CONFIRMED = "CONFIRMED"

    EXPIRED = "EXPIRED"


# ==========================================================
# Observation
# ==========================================================

@dataclass
class Observation:
    """
    Individual observation recorded against a catalyst.
    """

    timestamp: datetime

    source: str

    message: str


# ==========================================================
# Catalyst
# ==========================================================

@dataclass
class Catalyst:
    """
    One market-moving catalyst.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    title: str = ""

    catalyst_type: CatalystType = CatalystType.UNKNOWN

    timestamp: datetime = field(default_factory=datetime.now)

    source: str = ""

    impact: Impact = Impact.LOW

    priority: int = 0

    reason: str = ""

    expires_at: Optional[datetime] = None

    status: CatalystStatus = CatalystStatus.NEW

    # Market Mapping

    affected_themes: List[str] = field(default_factory=list)

    affected_industries: List[str] = field(default_factory=list)

    expected_positive: List[str] = field(default_factory=list)

    expected_negative: List[str] = field(default_factory=list)

    # Market Memory

    observations: List[Observation] = field(default_factory=list)

    # ------------------------------------------------------

    def __post_init__(self):

        self.add_observation(
            source="ENGINE",
            message=f"Catalyst created from {self.source}"
        )

    # ------------------------------------------------------

    def add_observation(
        self,
        source: str,
        message: str
    ):

        self.observations.append(

            Observation(

                timestamp=datetime.now(),

                source=source,

                message=message

            )

        )

    # ------------------------------------------------------

    def update_status(
        self,
        status: CatalystStatus
    ):

        self.status = status

        self.add_observation(

            source="ENGINE",

            message=f"Status changed to {status.value}"

        )


# ==========================================================
# Market Catalyst Engine
# ==========================================================

class MarketCatalystEngine:
    """
    Central repository for all active market catalysts.

    This engine observes external events and preserves
    market memory for the Brain.
    """

    def __init__(self):

        self.active_catalysts: List[Catalyst] = []

        self.market_memory: List[Catalyst] = []

    # ------------------------------------------------------

    def add_catalyst(
        self,
        catalyst: Catalyst
    ):

        catalyst.update_status(CatalystStatus.ACTIVE)

        self.active_catalysts.append(catalyst)

        self.market_memory.append(catalyst)

        print(
            f"[CATALYST] "
            f"{catalyst.title} | "
            f"{catalyst.catalyst_type.value} | "
            f"Priority={catalyst.priority}"
        )

    # ------------------------------------------------------

    def get_active(self) -> List[Catalyst]:

        self.check_expiry()

        return sorted(

            self.active_catalysts,

            key=lambda x: x.priority,

            reverse=True

        )

    # ------------------------------------------------------

    def check_expiry(self):

        now = datetime.now()

        for catalyst in self.active_catalysts:

            if (

                catalyst.expires_at is not None

                and

                catalyst.status != CatalystStatus.EXPIRED

                and

                now >= catalyst.expires_at

            ):

                catalyst.update_status(

                    CatalystStatus.EXPIRED

                )

    # ------------------------------------------------------

    def clear_expired(self):

        before = len(self.active_catalysts)

        self.active_catalysts = [

            catalyst

            for catalyst in self.active_catalysts

            if catalyst.status != CatalystStatus.EXPIRED

        ]

        removed = before - len(self.active_catalysts)

        if removed:

            print(

                f"[CATALYST ENGINE] "

                f"Removed {removed} expired catalyst(s)."

            )

    # ------------------------------------------------------

    def get_market_memory(self) -> List[Catalyst]:

        return self.market_memory

    # ------------------------------------------------------

    def get_active_count(self) -> int:

        return len(self.active_catalysts)

    # ------------------------------------------------------

    def get_memory_count(self) -> int:

        return len(self.market_memory)