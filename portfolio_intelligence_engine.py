from dataclasses import dataclass
from typing import List, Optional


# ---------------------------------------------------------
# Portfolio Intelligence Decision
# ---------------------------------------------------------

@dataclass(slots=True)
class PortfolioRecommendation:
    action: str
    reason: str

    weakest_symbol: Optional[str] = None
    weakest_conviction: float = 0.0

    candidate_symbol: Optional[str] = None
    candidate_conviction: float = 0.0


# ---------------------------------------------------------
# Portfolio Intelligence Engine
# ---------------------------------------------------------

class PortfolioIntelligenceEngine:
    """
    Institutional Portfolio Intelligence

    Responsibility
    --------------
    Decide whether existing capital should remain
    invested or be reallocated.

    Never
    -----
    - Buy
    - Sell
    - Place orders
    - Modify positions

    It only produces recommendations.
    """

    def __init__(
        self,
        replacement_threshold: float = 15.0,
        minimum_hold_seconds: int = 600,
    ):

        self.replacement_threshold = replacement_threshold
        self.minimum_hold_seconds = minimum_hold_seconds

    # -----------------------------------------------------

    def evaluate(
        self,
        portfolio,
        ranked_opportunities: List,
        current_time=None,
    ) -> PortfolioRecommendation:

        if not ranked_opportunities:

            return PortfolioRecommendation(
                action="NO_ACTION",
                reason="No ranked opportunities available",
            )

        if not portfolio:

            return PortfolioRecommendation(
                action="NO_ACTION",
                reason="Portfolio empty",
            )

        weakest = portfolio.weakest_position()

        if weakest is None:

            return PortfolioRecommendation(
                action="NO_ACTION",
                reason="No weakest position",
            )

        best = ranked_opportunities[0]

        if best.symbol == weakest.symbol:

            return PortfolioRecommendation(
                action="KEEP",
                reason="Current portfolio already owns best opportunity",
            )

        conviction_gap = (
            best.conviction -
            weakest.conviction
        )

        if conviction_gap < self.replacement_threshold:

            return PortfolioRecommendation(
                action="KEEP",
                reason=f"Conviction gap only {conviction_gap:.1f}",
                weakest_symbol=weakest.symbol,
                weakest_conviction=weakest.conviction,
                candidate_symbol=best.symbol,
                candidate_conviction=best.conviction,
            )

        if hasattr(weakest, "holding_seconds"):

            if weakest.holding_seconds < self.minimum_hold_seconds:

                return PortfolioRecommendation(
                    action="KEEP",
                    reason="Minimum holding time not completed",
                    weakest_symbol=weakest.symbol,
                    weakest_conviction=weakest.conviction,
                    candidate_symbol=best.symbol,
                    candidate_conviction=best.conviction,
                )

        return PortfolioRecommendation(
            action="REPLACE",
            reason="Superior opportunity available",
            weakest_symbol=weakest.symbol,
            weakest_conviction=weakest.conviction,
            candidate_symbol=best.symbol,
            candidate_conviction=best.conviction,
        )