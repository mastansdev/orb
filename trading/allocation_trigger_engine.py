from datetime import datetime, timedelta

from intelligence.opportunity_pool_engine import (
    opportunity_pool,
)


class AllocationTriggerEngine:
    """
    Institutional Allocation Trigger Engine

    Responsibilities
    ----------------
    Decide WHEN Capital Allocation should run.

    Never
    -----
    • Allocate capital
    • Rank opportunities
    • Execute trades
    • Manage portfolio
    """

    HIGH_CONVICTION = 95

    MIN_POOL_SIZE = 5

    MAX_WAIT_SECONDS = 20

    EMPTY_PORTFOLIO_WAIT = 15

    def __init__(self):

        self.pool = opportunity_pool

        self.last_allocation = datetime.min

    # --------------------------------------------------

    def should_allocate(
        self,
        open_positions: int,
    ):

        ranked = self.pool.ranked()

        if not ranked:
            return False

        # ----------------------------------------
        # Rule 1
        # Exceptional Opportunity
        # ----------------------------------------

        if ranked[0].conviction >= self.HIGH_CONVICTION:

            return True

        # ----------------------------------------
        # Rule 2
        # Healthy Competition
        # ----------------------------------------

        if len(ranked) >= self.MIN_POOL_SIZE:

            return True

        # ----------------------------------------
        # Rule 3
        # Waiting Timeout
        # ----------------------------------------

        oldest = min(
            x.discovered_at
            for x in ranked
        )

        age = (
            datetime.now() -
            oldest
        ).total_seconds()

        if age >= self.MAX_WAIT_SECONDS:

            return True

        # ----------------------------------------
        # Rule 4
        # Empty Portfolio
        # ----------------------------------------

        if (

            open_positions == 0

            and

            age >= self.EMPTY_PORTFOLIO_WAIT

        ):

            return True

        return False

    # --------------------------------------------------

    def allocation_done(self):

        self.last_allocation = datetime.now()