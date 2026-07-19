from dataclasses import dataclass
from typing import Dict, List, Optional


# ==========================================================
# Ranked Opportunity
# ==========================================================

@dataclass
class RankedOpportunity:

    symbol: str

    conviction: float

    quality: float

    opportunity: object


# ==========================================================
# Opportunity Ranker
# ==========================================================

class OpportunityRanker:
    """
    Maintains all approved opportunities and
    continuously ranks them.

    Responsibilities
    ----------------
    • Store approved opportunities
    • Rank by overall opportunity quality
    • Return strongest opportunity
    • Remove executed opportunities

    Never
    -----
    • Execute trades
    • Check portfolio limits
    • Manage exits
    • Allocate capital
    """

    def __init__(self):

        self.opportunities: Dict[
            str,
            RankedOpportunity
        ] = {}

    # --------------------------------------------------

    def add(
        self,
        opportunity
    ):

        ranked = RankedOpportunity(

            symbol=opportunity.symbol,

            conviction=opportunity.conviction,

            quality=opportunity.quality,

            opportunity=opportunity

        )

        self.opportunities[
            ranked.symbol
        ] = ranked

    # --------------------------------------------------

    def remove(
        self,
        symbol
    ):

        self.opportunities.pop(
            symbol,
            None
        )

    # --------------------------------------------------

    def best(self) -> Optional[RankedOpportunity]:

        if not self.opportunities:
            return None

        return max(

            self.opportunities.values(),

            key=lambda item: (

                item.conviction,

                item.quality

            )

        )

    # --------------------------------------------------

    def ranked(self) -> List[RankedOpportunity]:

        return sorted(

            self.opportunities.values(),

            key=lambda item: (

                item.conviction,

                item.quality

            ),

            reverse=True

        )

    # --------------------------------------------------

    def count(self):

        return len(

            self.opportunities

        )

    # --------------------------------------------------

    def clear(self):

        self.opportunities.clear()