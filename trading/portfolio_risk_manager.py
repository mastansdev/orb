from dataclasses import dataclass
from typing import Optional

# ==========================================================
# Portfolio Decision
# ==========================================================

@dataclass
class PortfolioDecision:

    action: str

    allowed: bool

    reason: str

    replacement_candidate: Optional[object] = None


@dataclass
class PortfolioOpportunity:

    symbol: str

    conviction: float = 0.0

    quality: float = 0.0


# ==========================================================
# Portfolio Risk Manager
# ==========================================================

class PortfolioRiskManager:
    """
    Portfolio-level admission controller.

    Responsibilities:
        • Maximum open trades
        • Duplicate trade protection

    This module decides whether the portfolio may
    accept a new trade.

    It NEVER:
        • scores trades
        • sizes positions
        • manages exits
        • places orders
    """

    def __init__(
        self,
        max_open_trades=100
    ):
        self.max_open_trades = max_open_trades
        self.open_trades = {}
        self.min_replacement_advantage = 15

    # --------------------------------------------------
    # Portfolio State
    # --------------------------------------------------

    def add_trade(
        self,
        opportunity
    ):
        """
        Register one active portfolio opportunity.
        """
        self.open_trades[
            opportunity.symbol
        ] = opportunity

    def remove_trade(
        self,
        symbol
    ):
        """
        Remove one active portfolio opportunity.
        """
        self.open_trades.pop(
            symbol,
            None
        )

    # --------------------------------------------------
    # Weakest Portfolio Opportunity
    # --------------------------------------------------

    def _weakest_opportunity(self):
        """
        Return the weakest currently
        held portfolio opportunity.
        """
        if not self.open_trades:
            return None

        return min(
            self.open_trades.values(),
            key=lambda opportunity: (
                opportunity.conviction,
                opportunity.quality
            )
        )

    # --------------------------------------------------
    # Replacement Evaluation
    # --------------------------------------------------
    
    def _should_replace(
            self,
            new_opportunity,
            weakest_opportunity,
    ):

            if weakest_opportunity is None:
                return False
            
            new_score = (
                new_opportunity.conviction 
                
            )

            weakest_score = (
                weakest_opportunity.conviction 
                
            )

            advantage = (
                new_score -
                weakest_score
            )

            return (
                advantage >=
                self.min_replacement_advantage
            )

    # --------------------------------------------------
    # Admission Check
    # --------------------------------------------------

    def can_take_trade(
        self,
        opportunity
    ):
        # ---------------------------------
        # Maximum Open Trades
        # ---------------------------------
        
        if len(self.open_trades) >= self.max_open_trades:

            weakest = self._weakest_opportunity()

            if self._should_replace(
                new_opportunity=opportunity,
                weakest_opportunity=weakest,
            ):
                
                return PortfolioDecision(
                    action="REPLACE",

                    allowed=True,

                    reason=(
                        f"Replace {weakest.symbol}"
                    ),

                    replacement_candidate=weakest,
                )
            
            return PortfolioDecision(

                action="PORTFOLIO_FULL",

                allowed=False,

                reason=(

                    f"Portfolio Full ({self.max_open_trades})"

                ),
                
                replacement_candidate=weakest,
            )
            
        # ---------------------------------
        # Duplicate Trade Protection
        # ---------------------------------
        if opportunity.symbol in self.open_trades:

            return PortfolioDecision(
                action="DUPLICATE",
                allowed=False,
                reason=(
                    f"{opportunity.symbol} already exists "
                    "in portfolio"
                )
            )

        return PortfolioDecision(

            action="APPROVED",
                
            allowed=True,

            reason="Portfolio admission approved."
        )