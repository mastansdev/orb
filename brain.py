"""
==========================================================
Brain
==========================================================

Mission
-------
The Brain is the central decision maker of the trading
system.

It NEVER calculates ORB, Themes, Industries or News.

It receives standardized Evidence objects from every
specialized engine and converts them into one explainable
decision.

Responsibilities
----------------
1. Collect Evidence
2. Validate Evidence
3. Detect Evidence Conflicts
4. Build Explainable Decision
5. Return Decision

Author : H&M ORB AUTO TRADER
==========================================================
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from evidence import Evidence


# ==========================================================
# Decision Actions
# ==========================================================

class DecisionAction(Enum):

    BUY = "BUY"

    WAIT = "WAIT"

    IGNORE = "IGNORE"

    EXIT = "EXIT"

    REDUCE = "REDUCE"

    ADD = "ADD"


# ==========================================================
# Decision Model
# ==========================================================

@dataclass
class Decision:

    symbol: str

    action: DecisionAction

    confidence: float

    score: float

    reasons: List[str] = field(default_factory=list)

    warnings: List[str] = field(default_factory=list)

    evidence_used: int = 0

    timestamp: datetime = field(default_factory=datetime.now)

    def explain(self):

        print()

        print("=" * 70)
        print("BRAIN DECISION")
        print("=" * 70)

        print(f"Symbol         : {self.symbol}")
        print(f"Decision       : {self.action.value}")
        print(f"Confidence     : {self.confidence:.2f}")
        print(f"Score          : {self.score:.2f}")
        print(f"Evidence Used  : {self.evidence_used}")

        print()

        print("Reasons")

        if self.reasons:

            for reason in self.reasons:

                print(f"  ✓ {reason}")

        else:

            print("  None")

        print()

        print("Warnings")

        if self.warnings:

            for warning in self.warnings:

                print(f"  ! {warning}")

        else:

            print("  None")

        print("=" * 70)


# ==========================================================
# Opportunity Lifecycle
# ==========================================================

@dataclass
class OpportunityLifecycle:

    stage: str = "DISCOVERY"

    strength: float = 0.0

    momentum: float = 0.0

    continuation_probability: float = 0.0

    expected_duration: str = "UNKNOWN"

    catalyst: str = ""

    last_updated: datetime = field(
        default_factory=datetime.now
    )


# ==========================================================
# Capital Allocation
# ==========================================================

@dataclass
class CapitalAllocation:

    tier: int = 4

    allocation: str = "NONE"

    reason: str = ""

    conviction: float = 0.0

    timestamp: datetime = field(
        default_factory=datetime.now
    )


# ==========================================================
# Opportunity Intelligence
# ==========================================================

@dataclass
class OpportunityIntelligence:

    symbol: str

    # ==================================================
    # Market Story
    # ==================================================

    story_name: str = ""

    dominant_catalyst: str = ""

    catalyst_type: str = ""

    catalyst_confidence: float = 0.0
    
    story_strength: float = 0.0
    
    story_direction: str = ""
    
    story_evidence_count: int = 0
    
    story_contradictions: int = 0
    
    story_lifecycle: str = ""

    # Market Structure
    dominant_sector: str = ""
    dominant_industry: str = ""
    dominant_theme: str = ""
    sector_strength: float = 0.0
    industry_strength: float = 0.0
    theme_strength: float = 0.0

    # Company Intelligence
    news_strength: float = 0.0
    results_strength: float = 0.0
    government_strength: float = 0.0

    # Price Behaviour
    gap_percent: float = 0.0
    pre_open_strength: float = 0.0
    auction_strength: float = 0.0
    liquidity_strength: float = 0.0
    volume_strength: float = 0.0
    relative_strength: float = 0.0
    continuation_probability: float = 0.0

    # Market Context
    market_regime: str = ""
    market_story: str = ""
    market_acceptance: float = 0.0
    market_strength: float = 0.0
    market_mood: float = 0.0

    # Risk
    opportunity_age: int = 0
    freshness_score: float = 0.0
    negative_strength: float = 0.0
    position_health: float = 100.0

    # Explainability
    reasons: List[str] = field(default_factory=list)

    warnings: List[str] = field(default_factory=list)


# ==========================================================
# Opportunity Model
# ==========================================================

@dataclass
class Opportunity:

    symbol: str

    first_seen: datetime = field(
        default_factory=datetime.now
    )

    intelligence: Optional[OpportunityIntelligence] = None

    quality: float = 0.0

    conviction: float = 0.0

    health: str = "NEW"

    previous_quality: float = 0.0

    confidence: float = 0.0

    capital_allocation: CapitalAllocation = field(
        default_factory=CapitalAllocation
    )

    entry_mode: str = "NORMAL"

    target_mode: str = "NORMAL"

    exit_mode: str = "NORMAL"

    rank: int = 999

    portfolio_percentile: float = 0.0
    conviction_gap_to_best: float = 0.0
    quality_gap_to_best: float = 0.0
    challenge_score: float = 0.0

    replacement_candidate: Optional[str] = None
    replacement_reason: str = ""
    replacement_score: float = 0.0

    reasons: List[str] = field(default_factory=list)

    warnings: List[str] = field(default_factory=list)

    lifecycle: OpportunityLifecycle = field(
        default_factory=OpportunityLifecycle
    )

    last_updated: datetime = field(default_factory=datetime.now)

    decision: DecisionAction = DecisionAction.WAIT


# ==========================================================
# Market Regime
# ==========================================================

@dataclass
class MarketRegime:

    regime: str = "NORMAL"

    confidence: float = 0.0

    description: str = ""

    dominant_factor: str = ""

    timestamp: datetime = field(
        default_factory=datetime.now
    )


# ==========================================================
# Market Story
# ==========================================================

@dataclass
class MarketStory:

    title: str = "UNKNOWN"

    description: str = ""

    dominant_sector: str = ""

    dominant_industry: str = ""

    dominant_theme: str = ""

    dominant_catalyst: str = ""

    confidence: float = 0.0

    affected_symbols: List[str] = field(default_factory=list)

    supporting_reasons: List[str] = field(default_factory=list)

    timestamp: datetime = field(
        default_factory=datetime.now
    )


# ==========================================================
# Brain
# ==========================================================

class Brain:

    """
    Central decision coordinator.

    Every engine supplies Evidence.

    Brain supplies one Decision.
    """

    def __init__(self):

        # Historical decisions
        self.memory = []

        # Live market opportunities
        self.opportunities = {}

        # Current rankings
        self.rankings = []

        # Currently selected opportunities
        self.active_opportunities = []

        self.market_regime = MarketRegime()

        self.market_story = MarketStory()

        self.minimum_confidence = 60

        self.minimum_score = 60

    # --------------------------------------------------

    def _identify_market_story(
            self,
            intelligence: OpportunityIntelligence
    ):
        
            """
            Determine WHY this opportunity exists.

            Responsibility
            --------------
            This function interprets market evidence and identifies
            the dominant reason behind the opportunity.

            It DOES NOT:

                - calculate quality
                - calculate conviction
                - allocate capital
                - make trading decisions

            It ONLY answers:


                "What story is the market telling?"
            """

            story = {
                "primary_cause": "UNKNOWN",
                "primary_driver": None,
                "flow_target": None,
                "flow_direction": "UNKNOWN",
                "flow_breadth": "UNKNOWN",
                "market_leaders": [],
                "supporting": [],
                "contradicting": []
            }

            # --------------------------------------------------
            # Collect available evidence
            # --------------------------------------------------
            evidence = {
                "SECTOR": intelligence.sector_strength,
                "INDUSTRY": intelligence.industry_strength,
                "THEME": intelligence.theme_strength,
                "NEWS": intelligence.news_strength,
                "RESULTS": intelligence.results_strength,
                "GOVERNMENT": intelligence.government_strength,
                "VOLUME": intelligence.volume_strength,
                "RELATIVE_STRENGTH": intelligence.relative_strength,
                "MARKET": intelligence.market_strength
            }

            # --------------------------------------------------
            # Rank evidence by strength
            # --------------------------------------------------
            ranked_evidence = sorted(
                evidence.items(),
                key=lambda item: item[1],
                reverse=True
            )

            # --------------------------------------------------
            # Classify evidence
            # --------------------------------------------------
            cause_evidence = {
                "NEWS": intelligence.news_strength,
                "RESULTS": intelligence.results_strength,
                "GOVERNMENT": intelligence.government_strength
            }
            flow_evidence = {
                "SECTOR": intelligence.sector_strength,
                "INDUSTRY": intelligence.industry_strength,
                "THEME": intelligence.theme_strength
            }
            confirmation_evidence = {
                "RELATIVE_STRENGTH": intelligence.relative_strength,
                "VOLUME": intelligence.volume_strength,
                "MARKET": intelligence.market_strength
            }

            story = self._reason_about_market_story(
                story=story,
                ranked_evidence=ranked_evidence,
                cause_evidence=cause_evidence,
                flow_evidence=flow_evidence,
                confirmation_evidence=confirmation_evidence
            )

            return story

    # --------------------------------------------------

    def _reason_about_market_story(
            self,
            story,
            ranked_evidence,
            cause_evidence,
            flow_evidence,
            confirmation_evidence
    ):
        """
        Determine the dominant market story from the prepared evidence.
        
        """
        
        active_causes = {
            name: strength
            for name, strength in cause_evidence.items()
            if strength > 0
        }

        if not active_causes:
            return story
        
        # --------------------------------------------------
        # Generate possible market hypotheses
        # --------------------------------------------------

        hypotheses = []

        # Company-specific possibility
        if (
            cause_evidence["RESULTS"] > 0
            or cause_evidence["NEWS"] > 0
        ):
            hypotheses.append("COMPANY_SPECIFIC")

        # Government-driven possibility
        if cause_evidence["GOVERNMENT"] > 0:
            hypotheses.append("GOVERNMENT_DRIVEN")

        if not hypotheses:
            return story

        for hypothesis in hypotheses:
            hypothesis_valid = True
            story["primary_cause"] = hypothesis

        # --------------------------------------------------
        # Validate COMPANY_SPECIFIC hypothesis
        # --------------------------------------------------

        if story["primary_cause"] == "COMPANY_SPECIFIC":
             
             if (
                 flow_evidence["SECTOR"] == 0
                 and flow_evidence["INDUSTRY"] == 0
                 and flow_evidence["THEME"] == 0
            ):
                story["supporting"].append(
                     "Peers are not participating"
                )

             else:
            
                story["contradicting"].append (
                    "Sector / Industry participation detected"
                )

                hypothesis_valid = False


        return story
  
    # --------------------------------------------------

    def _observe_market_behaviour(
            self,
            intelligence: OpportunityIntelligence
    ):
        """
        Observe how the market is behaving.
        
        This function DOES NOT decide anything.

        It only reports what it sees.
        """

        observation = {
            "behaviour": "UNKNOWN",
            "leaders": [],
            "followers": [],
            "laggards": [],
            "capital_flow": "UNKNOWN",
            "confidence": 0.0,
            "notes": []
        }

        return observation

    # --------------------------------------------------

    def _calculate_opportunity_quality(
        self,
        intelligence: OpportunityIntelligence
    ):

        """
        Convert market intelligence into one Opportunity Quality.
        Returns a value between 0 and 100.
        """

        positive = [

            intelligence.sector_strength,
            intelligence.industry_strength,
            intelligence.theme_strength,
            intelligence.news_strength,
            intelligence.results_strength,
            intelligence.government_strength,
            intelligence.volume_strength,
            intelligence.relative_strength,
            intelligence.market_strength,
            intelligence.market_mood,
            intelligence.continuation_probability

        ]

        print("\n========== QUALITY INPUTS ==========")
        print(f"Sector               : {intelligence.sector_strength}")
        print(f"Industry             : {intelligence.industry_strength}")
        print(f"Theme                : {intelligence.theme_strength}")
        print(f"News                 : {intelligence.news_strength}")
        print(f"Results              : {intelligence.results_strength}")
        print(f"Government           : {intelligence.government_strength}")
        print(f"Volume               : {intelligence.volume_strength}")
        print(f"Relative Strength    : {intelligence.relative_strength}")
        print(f"Market Strength      : {intelligence.market_strength}")
        print(f"Market Mood          : {intelligence.market_mood}")
        print(f"Continuation         : {intelligence.continuation_probability}")
        print("====================================\n")

        quality = sum(positive) / len(positive)

        # Negative events reduce quality
        quality -= intelligence.negative_strength

        # Clamp between 0 and 100
        quality = max(
            0,
            min(
                100,
                quality
            )
        )

        return quality

    # --------------------------------------------------

    def _rank_opportunities(self):

        """
        Rank every known opportunity from highest quality
        to lowest quality using structural tie-breakers.
        """

        ranked = sorted(

            self.opportunities.values(),

            key=lambda x: (

                x.quality,

                x.confidence,

                x.conviction

            ),

            reverse=True

        )

        for rank, opportunity in enumerate(ranked, start=1):

            opportunity.rank = rank

        self.rankings = ranked

        return ranked

    # --------------------------------------------------

    def _compare_opportunities(
        self,
        opportunity: Opportunity
    ):
        """
        Compare one opportunity against all other known opportunities.
        """
        record = self.opportunities.get(
            opportunity.symbol
        )
        
        if record is None:
            return {
                "rank": None,
                "top_opportunity": False,
                "better_opportunities": [],
                "better_count": 0,
                "total_opportunities": len(self.rankings),
                "portfolio_percentile": 0.0,
                "conviction_gap_to_best": 0.0,
                "quality_gap_to_best": 0.0
            }
            
        better = [
            other.symbol
            for other in self.rankings
            if (
                other.rank < record.rank
                and other.symbol != record.symbol
            )
        ]
        
        # --------------------------------------------------
        # Relative Portfolio Metrics
        # --------------------------------------------------
        if not self.rankings:
            return {
                "rank": record.rank,
                "top_opportunity": False,
                "better_opportunities": [],
                "better_count": 0,
                "total_opportunities": 0,
                "portfolio_percentile": 0.0,
                "conviction_gap_to_best": 0.0,
                "quality_gap_to_best": 0.0
            }

        best = self.rankings[0]

        total = max(
            len(self.rankings),
            1
        )
        
        portfolio_percentile = (
            (total - record.rank + 1) / total
        ) * 100
        
        conviction_gap = (
            best.conviction - record.conviction
        )
        
        quality_gap = (
            best.quality - record.quality
        )
        
        # --------------------------------------------------
        # Store Relative Portfolio Metrics
        # --------------------------------------------------
        record.portfolio_percentile = portfolio_percentile
        record.conviction_gap_to_best = conviction_gap
        record.quality_gap_to_best = quality_gap
        
        return {
            "rank": record.rank,
            "top_opportunity": (
                record.rank <= 5
            ),
            "better_opportunities": better,
            "better_count": len(better),
            "total_opportunities": total,
            "portfolio_percentile": portfolio_percentile,
            "conviction_gap_to_best": conviction_gap,
            "quality_gap_to_best": quality_gap
        }

    # --------------------------------------------------

    def _apply_portfolio_context(
        self,
        opportunity: Opportunity,
        comparison: dict
    ):
        """
        Adjust opportunity conviction
        using portfolio context.
        """
        # --------------------------------------------------
        # Portfolio Rank Pressure
        # --------------------------------------------------
        if not comparison["top_opportunity"]:

            opportunity.conviction -= 2

            opportunity.reasons.append(
                "Outside Top-5 portfolio opportunities."
            )

        # --------------------------------------------------
        # Elite Opportunity Bonus
        # --------------------------------------------------
        elif comparison["portfolio_percentile"] >= 90:

            opportunity.conviction += 1

            opportunity.reasons.append(
                "Elite portfolio opportunity."
            )

        # --------------------------------------------------
        # Clamp Values safely
        # --------------------------------------------------
        opportunity.conviction = max(
            0,
            min(
                100,
                opportunity.conviction
            )
        )

    # --------------------------------------------------

    def _find_replacement_candidate(
        self,
        opportunity: Opportunity
    ):
        """
        Determine whether this opportunity
        should replace an existing one.
        """
        # --------------------------------------------------
        # No opportunities to compare
        # --------------------------------------------------
        if not self.rankings:

            return None

        # --------------------------------------------------
        # Lowest ranked opportunity
        # --------------------------------------------------
        weakest = self.rankings[-1]

        # --------------------------------------------------
        # Never replace itself
        # --------------------------------------------------
        if weakest.symbol == opportunity.symbol:

            return None

        # --------------------------------------------------
        # Replacement Threshold
        # --------------------------------------------------
        conviction_edge = (
            opportunity.conviction - weakest.conviction
        )
        quality_edge = (
            opportunity.quality - weakest.quality
        )

        if (
            conviction_edge >= 5
            and quality_edge >= 5
        ):

            opportunity.replacement_candidate = weakest.symbol

            opportunity.replacement_reason = (
                "Higher conviction and opportunity quality."
            )

            opportunity.replacement_score = (
                conviction_edge + quality_edge
            )

            return weakest

        opportunity.replacement_candidate = None
        opportunity.replacement_reason = ""
        opportunity.replacement_score = 0
        return None

    # --------------------------------------------------

    def _build_market_story(
        self,
        intelligence_list: List[OpportunityIntelligence]
    ):

        """
        Build today's dominant market story by aggregating across 
        all available market intelligence profiles.
        """

        if not intelligence_list:

            return self.market_story

        sector_strength = {}

        theme_strength = {}

        industry_strength = {}

        for intelligence in intelligence_list:

            if intelligence.dominant_sector:

                sector = intelligence.dominant_sector

                sector_strength.setdefault(
                    sector,
                    0
                )

                sector_strength[sector] += intelligence.sector_strength

            if intelligence.dominant_theme:

                theme = intelligence.dominant_theme 

                theme_strength.setdefault(
                    theme,
                    0
                )

                theme_strength[theme] += intelligence.theme_strength

            if intelligence.dominant_industry:

                industry = intelligence.dominant_industry

                industry_strength.setdefault(
                    industry,
                    0
                )

                industry_strength[industry] += intelligence.industry_strength

        if sector_strength:

            self.market_story.dominant_sector = max(
                sector_strength,
                key=sector_strength.get
            )

        if theme_strength:

            self.market_story.dominant_theme = max(
                theme_strength,
                key=theme_strength.get
            )

        if industry_strength:

            self.market_story.dominant_industry = max(
                industry_strength,
                key=industry_strength.get
            )

        return self.market_story

    # --------------------------------------------------

    def _detect_catalysts(
        self,
        intelligence_list: List[OpportunityIntelligence]
    ):
        """
        Detect dominant market catalysts.
        """

        catalysts = {}

        for intelligence in intelligence_list:

            if not intelligence.reasons:
                continue

            for reason in intelligence.reasons:

                catalysts.setdefault(reason, 0)

                catalysts[reason] += 1

        return sorted(

            catalysts.items(),

            key=lambda x: x[1],

            reverse=True

        )

    # --------------------------------------------------

    def _build_opportunity_intelligence(
        self,
        symbol: str,
        evidence_list: List[Evidence]
    ):

        """
        Build one complete intelligence snapshot
        for a trading opportunity.
        """

        intelligence = OpportunityIntelligence(

            symbol=symbol

        )

        for evidence in evidence_list:

            provider = evidence.provider.upper()

            snapshot = evidence.snapshot()

            score = snapshot.get("score", 0)

            reason = snapshot.get("reason", "")

            facts = snapshot.get("facts", {})

            intelligence.reasons.append(reason)

            # ----------------------------
            # Sector
            # ----------------------------

            if provider == "SECTOR":

                intelligence.sector_strength = score
                intelligence.dominant_sector = facts.get("sector_name", "UNKNOWN")

            # ----------------------------
            # Industry
            # ----------------------------

            elif provider == "INDUSTRY":

                intelligence.industry_strength = score
                intelligence.dominant_industry = facts.get("industry_name", "UNKNOWN")

            # ----------------------------
            # Theme
            # ----------------------------

            elif provider == "THEME":

                intelligence.theme_strength = score
                intelligence.dominant_theme = facts.get("theme_name", "UNKNOWN")

            # ----------------------------
            # News
            # ----------------------------

            elif provider == "NEWS":

                intelligence.news_strength = score
                intelligence.dominant_catalyst = facts.get("catalyst", "")
                intelligence.catalyst_type = facts.get("catalyst_type", "")
                intelligence.catalyst_confidence = facts.get("catalyst_confidence", 0.0)

            # ----------------------------
            # Market Story
            # ----------------------------
            elif provider == "MARKET_STORY":

                intelligence.story_strength = facts.get(
                    "story_strength",
                    score
                )

                intelligence.story_direction = facts.get(
                    "story_direction",
                    ""
                )

                intelligence.story_evidence_count = facts.get(
                    "evidence_count",
                    0
                )

                intelligence.story_contradictions = facts.get(
                    "contradiction_count",
                    0
                )

                intelligence.story_lifecycle = facts.get(
                    "lifecycle",
                    ""
                )

                intelligence.story_name = facts.get(
                    "story_name",
                    ""
                )
                
                if "dominant_catalyst" in facts:
                    intelligence.dominant_catalyst = facts.get("dominant_catalyst", "")
                    intelligence.catalyst_type = facts.get("catalyst_type", "")
                    intelligence.catalyst_confidence = facts.get("catalyst_confidence", 0.0)

            # ----------------------------
            # Results
            # ----------------------------

            elif provider == "RESULTS":

                intelligence.results_strength = score

            # ----------------------------
            # Market Environment
            # ----------------------------

            elif provider == "MARKET":

                intelligence.market_strength = score

            # ----------------------------
            # Relative Strength
            # ----------------------------

            elif provider == "RELATIVE_STRENGTH":

                intelligence.relative_strength = score

            # ----------------------------
            # Volume
            # ----------------------------

            elif provider == "VOLUME":

                intelligence.volume_strength = score

            # ----------------------------
            # Government
            # ----------------------------

            elif provider == "GOVERNMENT":

                intelligence.government_strength = score

            # ----------------------------
            # Negative
            # ----------------------------

            elif provider == "NEGATIVE":

                intelligence.negative_strength = score

        return intelligence

    # --------------------------------------------------

    def _calculate_conviction(
        self,
        intelligence: OpportunityIntelligence,
        quality: float
    ):

        """
        Calculate institutional conviction.

        Conviction represents how strongly the Brain
        believes this opportunity deserves capital.
        """

        conviction = quality

        # --------------------------------------------------
        # Positive Reinforcements
        # --------------------------------------------------

        if intelligence.sector_strength >= 80:
            conviction += 3

        if intelligence.industry_strength >= 80:
            conviction += 3

        if intelligence.theme_strength >= 80:
            conviction += 5

        if intelligence.news_strength >= 80:
            conviction += 5

        # --------------------------------------------------
        # Story Reinforcements
        # --------------------------------------------------
        if intelligence.story_strength >= 80:
            conviction += 6

        if intelligence.story_direction == "STRENGTHENING":
            conviction += 4

        if intelligence.story_lifecycle == "DOMINANT":
            conviction += 5
        elif intelligence.story_lifecycle == "STRONG":
            conviction += 3

        if intelligence.story_evidence_count >= 10:
            conviction += 5
        elif intelligence.story_evidence_count >= 5:
            conviction += 3

        if intelligence.government_strength >= 80:
            conviction += 6

        if intelligence.relative_strength >= 80:
            conviction += 4

        if intelligence.volume_strength >= 80:
            conviction += 4

        if intelligence.continuation_probability >= 80:
            conviction += 5

        # --------------------------------------------------
        # Negative Reinforcements
        # --------------------------------------------------

        conviction -= intelligence.negative_strength

        # --------------------------------------------------
        # Story Penalties
        # --------------------------------------------------
        if intelligence.story_contradictions > 0:
            conviction -= (
                intelligence.story_contradictions * 3
            )

        if intelligence.story_direction == "WEAKENING":
            conviction -= 5

        if intelligence.story_direction == "CONTRADICTED":
            conviction -= 10

        # --------------------------------------------------

        conviction = max(
            0,
            min(
                100,
                conviction
            )
        )

        return conviction

    # --------------------------------------------------

    def _update_opportunity_health(
        self,
        opportunity: Opportunity,
        current_quality: float
    ):

        """
        Compare previous and current quality to
        determine opportunity health.
        """

        previous = opportunity.previous_quality

        difference = current_quality - previous

        if previous == 0:

            health = "NEW"

        elif difference >= 8:

            health = "STRONGLY_IMPROVING"

        elif difference >= 3:

            health = "IMPROVING"

        elif difference <= -8:

            health = "DETERIORATING"

        elif difference <= -3:

            health = "WEAKENING"

        else:

            health = "STABLE"

        opportunity.health = health

        opportunity.previous_quality = current_quality

        return health

    # --------------------------------------------------

    def _evaluate_opportunity(
        self,
        symbol: str,
        evidence_list: List[Evidence]
    ):

        """
        Build one complete opportunity lifecycle profile.
        """

        intelligence = self._build_opportunity_intelligence(

            symbol,

            evidence_list

        )

        quality = self._calculate_opportunity_quality(

            intelligence

        )

        conviction = self._calculate_conviction(

            intelligence,

            quality

        )

        opportunity = self.opportunities.get(symbol)

        if opportunity is None:

            opportunity = Opportunity(symbol=symbol)

        opportunity.quality = quality

        opportunity.conviction = conviction

        opportunity.reasons = [
            f"{e.provider.upper()}: {e.snapshot().get('reason', '')}" 
            for e in evidence_list
        ]
        opportunity.warnings = []

        total_confidence = sum(e.snapshot().get("confidence", 0) for e in evidence_list)
        opportunity.confidence = total_confidence / len(evidence_list) if evidence_list else 0

        bullish = sum(1 for e in evidence_list if e.snapshot().get("recommendation") == "BUY")
        bearish = sum(1 for e in evidence_list if e.snapshot().get("recommendation") == "SELL")
        if bullish > 0 and bearish > 0:
            opportunity.warnings.append("Bullish and bearish evidence both present.")
            if abs(bullish - bearish) <= 1:
                opportunity.warnings.append("High evidence conflict.")
                opportunity.confidence *= 0.80

        allocation = self._calculate_capital_allocation(

            opportunity,

            conviction

        )

        opportunity.capital_allocation = allocation

        opportunity.entry_mode = self._determine_entry_mode(

            intelligence,

            conviction,

            allocation

        )

        opportunity.target_mode = self._determine_target_mode(

            conviction,

            opportunity.lifecycle

        )

        self._update_opportunity_health(

            opportunity,

            quality

        )

        return opportunity

    # --------------------------------------------------

    def _build_decision(
        self,
        opportunity: Opportunity,
        evidence_list: List[Evidence]
    ) -> Decision:

        """
        Convert one evaluated opportunity into
        a final explainable decision.
        """

        reasons = list(opportunity.reasons)

        warnings = list(opportunity.warnings)

        reasons.insert(
            0,
            f"Market Rank = {opportunity.rank}"
        )

        reasons.insert(
            1,
            f"Opportunity Quality = {opportunity.quality:.2f}"
        )

        reasons.insert(
            2,
            f"Conviction = {opportunity.conviction:.2f}"
        )

        reasons.insert(
            3,
            f"Health = {opportunity.health}"
        )

        reasons.insert(
            4,
            f"Entry Mode = {opportunity.entry_mode}"
        )

        reasons.insert(
            5,
            f"Target Mode = {opportunity.target_mode}"
        )

        action = DecisionAction.WAIT

        if opportunity.capital_allocation.tier <= 2:

            action = DecisionAction.BUY

        if opportunity.confidence < self.minimum_confidence:
            warnings.append(f"Confidence below minimum ({opportunity.confidence:.2f}).")
            action = DecisionAction.WAIT

        if opportunity.quality < self.minimum_score:
            warnings.append(f"Score below minimum ({opportunity.quality:.2f}).")
            action = DecisionAction.WAIT

        return Decision(

            symbol=opportunity.symbol,

            action=action,

            confidence=opportunity.confidence,

            score=opportunity.quality,

            reasons=reasons,

            warnings=warnings,

            evidence_used=len(evidence_list)

        )

    # --------------------------------------------------

    def _calculate_capital_allocation(
        self,
        opportunity: Opportunity,
        conviction: float
    ):

        """
        Decide how aggressively capital should
        be deployed.

        Quantity is NOT decided here.

        PositionManager converts this into shares.
        """

        allocation = CapitalAllocation()

        allocation.conviction = conviction

        # ----------------------------------------

        if conviction >= 95:

            allocation.tier = 1

            allocation.allocation = "FULL"

            allocation.reason = (
                "Exceptional institutional opportunity."
            )

        elif conviction >= 85:

            allocation.tier = 2

            allocation.allocation = "HIGH"

            allocation.reason = (
                "High conviction opportunity."
            )

        elif conviction >= 70:

            allocation.tier = 3

            allocation.allocation = "MEDIUM"

            allocation.reason = (
                "Good opportunity."
            )

        else:

            allocation.tier = 4

            allocation.allocation = "NONE"

            allocation.reason = (
                "Capital better deployed elsewhere."
            )

        return allocation

    # --------------------------------------------------

    def _determine_entry_mode(
        self,
        intelligence: OpportunityIntelligence,
        conviction: float,
        allocation: CapitalAllocation
    ):

        """
        Decide how this opportunity should
        be entered.
        """

        # ------------------------------------------
        # Exceptional Opportunities
        # ------------------------------------------

        if (

            allocation.tier == 1

            and intelligence.news_strength >= 90

            and intelligence.volume_strength >= 85

            and intelligence.relative_strength >= 85

        ):

            return "EARLY"

        # ------------------------------------------

        if allocation.tier <= 2:

            return "ORB_CONFIRMATION"

        # ------------------------------------------

        return "WAIT"

    # --------------------------------------------------

    def _determine_target_mode(
        self,
        conviction: float,
        lifecycle: OpportunityLifecycle
    ):

        """
        Decide how profits should be managed.
        """

        if (

            conviction >= 90

            and lifecycle.stage in (

                "DISCOVERY",

                "CONFIRMATION",

                "ACCELERATION"

            )

        ):

            return "DYNAMIC"

        if lifecycle.stage == "MATURITY":

            return "TRAIL"

        if lifecycle.stage == "EXHAUSTION":

            return "QUICK_EXIT"

        return "FIXED"

    # --------------------------------------------------

    def _update_opportunity(
        self,
        symbol,
        intelligence,
        quality,
        conviction,
        decision,
        opportunity_reasons=None,
        opportunity_warnings=None
    ):
        """
        Update specialized global tracking fields and timestamps 
        for an existing stored opportunity.
        """
        opportunity = self.opportunities.get(symbol)

        if opportunity is None:
            opportunity = Opportunity(symbol=symbol)
            self.opportunities[symbol] = opportunity

        opportunity.intelligence = intelligence
        opportunity.quality = quality
        opportunity.conviction = conviction
        opportunity.decision = decision.action
        
        if opportunity_reasons is not None:
            opportunity.reasons = list(opportunity_reasons)
        if opportunity_warnings is not None:
            opportunity.warnings = list(opportunity_warnings)
            
        opportunity.last_updated = datetime.now()

    # --------------------------------------------------

    def evaluate(
        self,
        symbol: str,
        evidence_list: List[Evidence],
        conviction_snapshot=None
    ) -> Decision:
        """
        Main Brain evaluation pipeline.
        """

        if not evidence_list:

            return Decision(

                symbol=symbol,

                action=DecisionAction.WAIT,

                confidence=0,

                score=0,

                warnings=["No evidence received."],

                evidence_used=0

            )

        # --------------------------------------------------
        # Conviction Snapshot (Future Integration)
        # --------------------------------------------------
        if conviction_snapshot is not None:

            self.latest_conviction_snapshot = conviction_snapshot

        # --------------------------------------------------
        # Evaluate & Store Opportunity
        # --------------------------------------------------

        opportunity = self._evaluate_opportunity(

            symbol,

            evidence_list

        )

        self.opportunities[symbol] = opportunity

        # --------------------------------------------------
        # Rank All Opportunities Across the Registry
        # --------------------------------------------------

        self._rank_opportunities()

        # --------------------------------------------------
        # Contextual Peer Comparison
        # --------------------------------------------------

        comparison = self._compare_opportunities(
            opportunity
        )

        # --------------------------------------------------
        # Extract Intelligence Snapshot
        # --------------------------------------------------

        intelligence = self._build_opportunity_intelligence(

            symbol,

            evidence_list

        )

        # --------------------------------------------------
        # Build Market-Wide Macro Narrative Story
        # --------------------------------------------------

        all_intelligence = [
            op.intelligence for op in self.opportunities.values() 
            if op.intelligence is not None
        ]
        
        self._build_market_story(all_intelligence)

        # --------------------------------------------------
        # Apply Portfolio Context
        # --------------------------------------------------
        self._apply_portfolio_context(
            opportunity,
            comparison
        )

        # --------------------------------------------------
        # Apply Dynamic Replacement Engine Evaluation
        # --------------------------------------------------
        self._find_replacement_candidate(
            opportunity
        )

        # --------------------------------------------------
        # Build Decision
        # --------------------------------------------------

        decision = self._build_decision(

            opportunity,

            evidence_list

        )

        # --------------------------------------------------
        # Synchronize Brain Memory State Fields
        # --------------------------------------------------

        self._update_opportunity(
            symbol=symbol,
            intelligence=intelligence,
            quality=opportunity.quality,
            conviction=opportunity.conviction,
            decision=decision,
            opportunity_reasons=opportunity.reasons,
            opportunity_warnings=opportunity.warnings
        )

        # --------------------------------------------------
        # Store Decision History
        # --------------------------------------------------

        self.memory.append(

            decision

        )

        MAX_MEMORY = 500

        if len(self.memory) > MAX_MEMORY:

            self.memory.pop(0)

        return decision

    # --------------------------------------------------

    def get_memory(self):

        return self.memory

    # --------------------------------------------------

    def clear_memory(self):

        self.memory.clear()
