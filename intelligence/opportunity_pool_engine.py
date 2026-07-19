from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


# ==========================================================
# Opportunity
# ==========================================================

@dataclass
class Opportunity:

    symbol: str

    conviction: float

    quality: float

    orb: dict

    intelligence: dict

    evidence: list

    brain_decision: object

    discovered_at: datetime = field(
        default_factory=datetime.now
    )

    state: str = "QUALIFIED"


# ==========================================================
# Opportunity Pool Engine
# ==========================================================

class OpportunityPoolEngine:
    """
    Institutional Opportunity Pool.

    Responsibilities
    ----------------
    • Receive approved opportunities
    • Maintain active opportunity pool
    • Prevent duplicate opportunities
    • Expire stale opportunities
    • Return ranked opportunities

    Never
    -----
    • Execute trades
    • Allocate capital
    • Manage portfolio
    """

    STALE_SECONDS = 30

    def __init__(self):

        self.pool: Dict[
            str,
            Opportunity
        ] = {}

    # --------------------------------------------------

    def add(
        self,
        symbol,
        conviction,
        quality,
        orb,
        intelligence,
        evidence,
        brain_decision,
    ):

        self.pool[symbol] = Opportunity(

            symbol=symbol,

            conviction=conviction,

            quality=quality,

            orb=orb,

            intelligence=intelligence,

            evidence=evidence,

            brain_decision=brain_decision,

        )

    # --------------------------------------------------

    def recommend(self):
        
        ranked = self.ranked()
        
        if not ranked:
            return None
        
        
        opportunity = ranked[0]
        opportunity.state = "RECOMMENDED"
        return opportunity

    # --------------------------------------------------

    def executed(
            self,
            symbol,
    ):
        if symbol not in self.pool:
        
            return
        
        self.pool[symbol].state = "EXECUTED"
        
        del self.pool[symbol]

    # --------------------------------------------------

    def waiting(
            self,
            symbol,
    ):
        
        if symbol not in self.pool:
            
            return
        
        self.pool[symbol].state = "QUALIFIED"


    # --------------------------------------------------

    def expire(self):

        now = datetime.now()

        expired = []

        for symbol, opportunity in self.pool.items():

            age = (
                now -
                opportunity.discovered_at
            ).total_seconds()

            if age >= self.STALE_SECONDS:

                expired.append(symbol)

        for symbol in expired:

            del self.pool[symbol]

    # --------------------------------------------------

    def ranked(self) -> List[Opportunity]:

        self.expire()

        return sorted(

            self.pool.values(),

            key=lambda x: (

                x.conviction,

                x.quality

            ),

            reverse=True

        )

    # --------------------------------------------------

    def best(self) -> Optional[Opportunity]:

        ranked = self.ranked()

        if not ranked:

            return None

        return ranked[0]

    # --------------------------------------------------

    def remove(
        self,
        symbol
    ):

        self.pool.pop(

            symbol,

            None

        )

    # --------------------------------------------------

    def clear(self):

        self.pool.clear()

    # --------------------------------------------------

    def count(self):

        return len(

            self.pool

        )

    # --------------------------------------------------

    def stats(self):

        return {

            "active": len(self.pool),

            "stale_after_seconds": self.STALE_SECONDS,

        }
    
    # ==========================================================
    # Global Opportunity Pool Instance
    # ==========================================================

opportunity_pool = OpportunityPoolEngine()