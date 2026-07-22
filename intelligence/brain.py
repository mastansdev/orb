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

from intelligence.evidence import Evidence
from repositories.intelligence_repository import IntelligenceRepository
from news.news_evidence_builder import NewsEvidenceBuilder
from news.impact_engine import (
    ImpactEngine,
)

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

    opportunity: "Opportunity" = None

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

        self.intelligence_repository = IntelligenceRepository()

        self.pending_stories = []

        self.news_evidence_builder = NewsEvidenceBuilder()

        self.impact_engine = ImpactEngine()

        self.minimum_confidence = 60

        self.minimum_score = 60

    # --------------------------------------------------
    # Regime-Adaptive Conviction Gate (2026-07-21)
    #
    # Fix: self.market_regime existed but was NEVER updated after
    # __init__ -- it sat at its "NORMAL" default forever, so the
    # conviction gate applied the exact same flat CONVICTION_MIN_SCORE
    # threshold regardless of actual market condition. A trader
    # naturally raises their bar in a choppy/bearish tape (thin,
    # noisy signal -- only take clearly strong setups) and can
    # afford to be closer to normal in a genuine uptrend (real
    # opportunity is already abundant, no need to loosen further).
    # This was a real, named gap -- the bot wasn't doing that.
    #
    # This is a STARTING POINT, not a backtested optimum -- same
    # honesty as the trail/velocity-guard tuning: watch how it
    # behaves live and adjust these numbers.
    # --------------------------------------------------
    REGIME_CONVICTION_ADJUSTMENT = {
        "TRENDING_UP":   -5,   # slightly more permissive
        "TRENDING_DOWN": +10,  # bot is long-only -- be more selective
        "BEARISH":       +15,  # same reasoning, more severe
        "CHOPPY":        +10,  # thin/noisy signal -- raise the bar
        "FLAT":          +8,   # muted signal -- raise the bar somewhat
        "WARMUP":        0,    # not enough data yet to judge regime
        "NORMAL":        0,    # default/fallback
    }

    # Never let the adjustment push the effective bar to an
    # unreasonable extreme in either direction.
    MIN_EFFECTIVE_THRESHOLD = 40
    MAX_EFFECTIVE_THRESHOLD = 85

    def set_market_regime(self, regime, confidence=0.0, description="", dominant_factor=""):
        """
        Feed live regime data in -- call this periodically (e.g.
        from engine.py's existing 30s market-state refresh, the
        same place risk_governor.set_market_state() already gets
        called) so the conviction gate actually reflects current
        conditions instead of a permanent "NORMAL" placeholder.
        """
        self.market_regime = MarketRegime(
            regime=regime,
            confidence=confidence,
            description=description,
            dominant_factor=dominant_factor,
        )

    def _effective_conviction_threshold(self, base_threshold):
        regime = getattr(self.market_regime, "regime", "NORMAL")
        adjustment = self.REGIME_CONVICTION_ADJUSTMENT.get(regime, 0)

        effective = base_threshold + adjustment

        return max(
            self.MIN_EFFECTIVE_THRESHOLD,
            min(self.MAX_EFFECTIVE_THRESHOLD, effective)
        )

    # --------------------------------------------------

    # --------------------------------------------------

    def update_intelligence(self):
         """
         Load newly accumulated institutional intelligence.
         This is the only entry point through which the Brain
         consumes Railway intelligence.
         """

         self.pending_stories = (
             self.intelligence_repository.load_new_intelligence()
        )
         
         return self.pending_stories
    
    # --------------------------------------------------

    # --------------------------------------------------

    def build_news_evidence(self):
        """
        Convert newly received institutional impacts
        into Brain Evidence.
        Railway no longer owns this responsibility.

        Fix (2026-07-21): this used to build ONE evidence
        item per story with no symbol attached, which meant
        it silently applied to every stock's conviction score
        instead of just the stock(s) the story was actually
        about. Now builds one evidence item PER AFFECTED
        SYMBOL (same pattern event_intelligence.py already
        uses for structured events), and skips stories with
        no matched symbol entirely -- a symbol-less macro/
        commodity story isn't noise to discard, it's handled
        separately by TradeSelectionEngine's sensitivity
        fan-out (see ingest_news()), which decides WHICH
        stocks a broad market story actually matters for.
        """

        evidence_list = []

        for story in self.pending_stories:
            symbols = getattr(story, "affected_symbols", None) or []
            if isinstance(symbols, str):
                symbols = [symbols]
            if not symbols:
                continue

            impact = self.impact_engine.evaluate(
                story
            )

            # Fix (2026-07-22): story_direction used to be
            # hardcoded "STRENGTHENING" at creation and on every
            # merge (market_story_builder.py), regardless of
            # what the story was actually about -- WEAKENING and
            # CONTRADICTED were never assigned anywhere in the
            # codebase, confirmed by exhaustive search. Every
            # downstream consumer that branches on this field
            # (FNO_CATALYST evidence, RESULTS_LIVE evidence, the
            # old EVENT_ENTRY bearish guard) could therefore
            # never actually see a bearish signal, no matter how
            # bad the news was. Now derived from the real impact
            # assessment computed just above -- same weighting
            # news_evidence_builder._score() already uses, so
            # the two stay consistent. Mutates the SAME object
            # trade_selection_engine.ingest_news() later passes
            # to news_watchlist.on_story(), so the dashboard
            # picks up the real direction too, not just entry
            # evidence.
            net_impact = (
                impact.market_score * 3
                + impact.sector_score * 2
                + impact.stock_score
            )
            if net_impact > 0:
                story.story_direction = "STRENGTHENING"
            elif net_impact < 0:
                story.story_direction = "WEAKENING"
            else:
                story.story_direction = "NEUTRAL"

            for symbol in symbols:
                if not symbol:
                    continue

                evidence = self.news_evidence_builder.build(
                    story,
                    impact,
                    symbol=str(symbol).upper(),
                )

                evidence_list.append(
                    evidence
                )

        return evidence_list
        
        

    # --------------------------------------------------
     
    # --------------------------------------------------

    
    def _calculate_opportunity_quality(
            self,
            intelligence: OpportunityIntelligence
    ):
        """
        Convert available market intelligence into one
        Opportunity Quality.
        Only evidence that actually exists participates
        in the calculation.
        """

        evidence = []
        
        
        def add(value):
            if value is not None and value > 0:
                evidence.append(value)

        add(intelligence.sector_strength)
        add(intelligence.industry_strength)
        add(intelligence.theme_strength)
        add(intelligence.news_strength)
        add(intelligence.results_strength)
        add(intelligence.government_strength)
        add(intelligence.volume_strength)
        add(intelligence.relative_strength)
        add(intelligence.market_strength)
        add(intelligence.market_mood)
        add(intelligence.continuation_probability)

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

        if not evidence:
            return 0.0

        quality = sum(evidence) / len(evidence)

        quality -= intelligence.negative_strength

        quality = max(0.0, min(100.0, quality))

        return quality

    

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

            # Fix (2026-07-21): two compounding bugs kept this
            # branch from EVER firing. (1) evidence_builder.py
            # emits provider="sector" (lowercase) but this
            # checked "SECTOR" (uppercase) — never matched.
            # (2) even matched, sector_engine.py's snapshot key
            # is "name", not "sector_name" — always fell back
            # to "UNKNOWN". Net effect: dominant_sector was
            # ALWAYS empty/"UNKNOWN", so risk_governor.py's
            # `if sector:` sector-cap check silently no-opped
            # for every candidate (looked like it was blocking
            # on "unknown sector" when it was actually just
            # skipping the check).
            if provider.upper() == "SECTOR":

                intelligence.sector_strength = score
                intelligence.dominant_sector = (
                    facts.get("sector_name")
                    or facts.get("name")
                    or "UNKNOWN"
                )

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

            # ----------------------------
            # Pattern Memory / Company Memory
            # ----------------------------
            # AVOID patterns act as negative evidence.
            # Positive history acts as continuation
            # support.
            # ----------------------------

            elif provider in ("PATTERN", "COMPANY"):

                recommendation = str(
                    snapshot.get("recommendation", "")
                ).upper()

                if recommendation in ("AVOID", "SELL"):
                    intelligence.negative_strength += score
                else:
                    intelligence.continuation_probability = max(
                        intelligence.continuation_probability,
                        score
                    )

            # ----------------------------
            # Event Intelligence / F&O Catalysts
            # ----------------------------
            # Structured events act like high-grade
            # news; live F&O catalysts support
            # continuation. Negative directions act
            # as negative evidence.
            # ----------------------------

            elif provider in (
                "EVENT", "FNO_CATALYST",
                "CAUSAL", "SYMPATHY", "EVENT_RISK",
                "RESULTS_LIVE",
            ):

                recommendation = str(
                    snapshot.get("recommendation", "")
                ).upper()

                if recommendation in ("AVOID", "SELL"):
                    intelligence.negative_strength += score
                else:
                    intelligence.news_strength = max(
                        intelligence.news_strength,
                        score
                    )
                    if not intelligence.dominant_catalyst:
                        intelligence.dominant_catalyst = (
                            facts.get("catalyst", "")
                        )

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

       # --------------------------------------------------
       # Capital Allocation
       # --------------------------------------------------
       # PortfolioRiskManager determines capital allocation.

        opportunity.capital_allocation = None

        # ExecutionStrategySelector determines entry mode.
        opportunity.entry_mode = None

        # PositionManager / ExecutionStrategySelector
        # determine target management.
        opportunity.target_mode = None

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

        # --------------------------------------------------
        # Brain Decision
        # --------------------------------------------------

        # --------------------------------------------------
        # Institutional Decision Gate V1
        # --------------------------------------------------

        action = DecisionAction.WAIT

        # Critical warning detection

        critical_warning = any(
            warning.lower().startswith((

                "confidence below",
                "score below",
                "high evidence conflict",
                "bullish and bearish"
            ))
            for warning in warnings
        )

        # Elite Opportunity
        if (
            opportunity.quality >= 85
            and opportunity.confidence >= 80
            and not critical_warning
        ):
            action = DecisionAction.BUY

        # Strong Opportunity
        elif (
            opportunity.quality >= 75
            and opportunity.confidence >= 70
            and not critical_warning
        ):
            action = DecisionAction.BUY

        # Good Opportunity (observe only)
        elif (
            opportunity.quality >= self.minimum_score
            and opportunity.confidence >= self.minimum_confidence
        ):
            warnings.append(
                "Opportunity meets minimum threshold but not institutional quality."
            )
            action = DecisionAction.WAIT

        # Weak Opportunity
        else:

            if opportunity.confidence < self.minimum_confidence:
                warnings.append(
                    f"Confidence below minimum ({opportunity.confidence:.2f})."
                )

            if opportunity.quality < self.minimum_score:
                warnings.append(
                    f"Score below minimum ({opportunity.quality:.2f})."
                )

            action = DecisionAction.WAIT

        # --------------------------------------------------
        # Conviction Gate (CONVICTION_SPECIFICATION.md)
        #
        #   Evidence contributes; CONVICTION DECIDES;
        #   Risk authorizes; Execution acts.
        #
        # A BUY is only allowed when the Conviction Engine
        # (Strength × Agreement × Confidence) also agrees.
        # --------------------------------------------------

        snapshot = getattr(
            self,
            "latest_conviction_snapshot",
            None
        )

        if action == DecisionAction.BUY and snapshot:

            conviction_score = snapshot.get("score")
            alignment = snapshot.get("alignment")

            if conviction_score is not None:

                from config import CONVICTION_MIN_SCORE

                effective_threshold = self._effective_conviction_threshold(
                    CONVICTION_MIN_SCORE
                )

                if conviction_score < effective_threshold:
                    action = DecisionAction.WAIT
                    regime = getattr(
                        self.market_regime, "regime", "NORMAL"
                    )
                    warnings.append(
                        f"Conviction gate: "
                        f"{conviction_score:.1f} < "
                        f"{effective_threshold} "
                        f"(base {CONVICTION_MIN_SCORE}, "
                        f"regime={regime}) "
                        f"({snapshot.get('grade')})"
                    )

                elif alignment == "BEARISH":
                    action = DecisionAction.WAIT
                    warnings.append(
                        "Conviction gate: evidence alignment "
                        "is BEARISH."
                    )

                else:
                    reasons.append(
                        f"Conviction {conviction_score:.1f} "
                        f"({snapshot.get('grade')}) — "
                        f"{snapshot.get('summary', '')}"
                    )

        print("\n========== BRAIN DECISION GATE ==========")
        print(f"Symbol        : {opportunity.symbol}")
        print(f"Quality       : {opportunity.quality:.2f}")
        print(f"Confidence    : {opportunity.confidence:.2f}")
        print(f"Action        : {action.value}")
        print(f"Reason Count  : {len(reasons)}")
        print(f"Top Reasons   : {reasons[:5]}")
        print(f"Warnings      : {warnings}")
        print("=========================================\n")

        
        return Decision(

            symbol=opportunity.symbol,

            action=action,

            confidence=opportunity.confidence,

            score=opportunity.quality,

            reasons=reasons,

            warnings=warnings,

            evidence_used=len(evidence_list),

            opportunity=opportunity

        )

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
        # Portfolio Intelligence
        # --------------------------------------------------
        # Portfolio-wide ranking and peer comparison are
        # handled by PortfolioRiskManager.
        comparison = None

        # --------------------------------------------------
        # Extract Intelligence Snapshot
        # --------------------------------------------------

        intelligence = self._build_opportunity_intelligence(

            symbol,

            evidence_list

        )

        # --------------------------------------------------
        # Market Story
        # --------------------------------------------------
        # MarketStoryEngine owns market story construction.
        # Brain consumes market story produced by that engine.

        # --------------------------------------------------
        # Portfolio Context
        # --------------------------------------------------
        # PortfolioRiskManager owns portfolio decisions.
        # Brain evaluates only this opportunity.

        # --------------------------------------------------
        # Replacement Candidate
        # --------------------------------------------------
        # Portfolio replacement decisions are handled by
        # PortfolioRiskManager.

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