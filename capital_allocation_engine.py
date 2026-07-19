from typing import Optional

from opportunity_pool_engine import (
    Opportunity,
    opportunity_pool,
)


class CapitalAllocationEngine:
    """
    Institutional Capital Allocation Engine

    Responsibilities
    ----------------
    • Read Opportunity Pool
    • Select highest-quality opportunity
    • Allocate one opportunity per cycle
    • Remove allocated opportunity from pool

    Never
    -----
    • Execute trades
    • Manage portfolio
    • Calculate ORB
    • Manage risk
    """

    def __init__(self):

        self.pool = opportunity_pool

        self.allocations = 0

    # --------------------------------------------------

    def allocate(self) -> Optional[Opportunity]:

        candidate = self.pool.recommend()

        if candidate is None:

            return None

        self.allocations += 1

        return candidate
    
    # --------------------------------------------------

    
    def confirm_execution(
            self,
            symbol,
    ):
        
        self.pool.executed(
            symbol
        )

    # --------------------------------------------------

    def reject(
            self,
            symbol,
    ):
        self.pool.waiting(
            symbol
        )

    # --------------------------------------------------


    def pending(self):

        return self.pool.count()

    # --------------------------------------------------

    def stats(self):

        return {

            "allocations": self.allocations,

            "pending": self.pending(),

        }