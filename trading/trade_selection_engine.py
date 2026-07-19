from config import MIN_ORB_RANGE_PERCENT
from intelligence.evidence_builder import EvidenceBuilder
from intelligence.evidence_validator import EvidenceValidator
from intelligence.conviction_engine import ConvictionEngine
from intelligence.brain import Brain, DecisionAction
from tools.decision_trace import DecisionTrace
from intelligence.opportunity_pool_engine import opportunity_pool

class TradeSelectionEngine:

    def __init__(self):
        self.breakouts = 0
        self.selected = 0
        self.skipped = 0

        self.evidence_builder = EvidenceBuilder()
        self.evidence_validator = EvidenceValidator()
        self.conviction_engine = ConvictionEngine()
        self.brain = Brain()
        self.decision_trace = DecisionTrace()
        self.opportunity_pool = opportunity_pool

        # Attached later by the Engine (optional layers)
        self.pattern_engine = None
        self.company_intelligence = None
        self.event_intelligence = None
        self.fno_engine = None
        self.knowledge_graph = None
        self.results_calendar = None

        # Rolling spillovers from recent events
        self._recent_spillovers = []

    # --------------------------------------------------

    def attach_intelligence(
        self,
        pattern_engine=None,
        company_intelligence=None,
        event_intelligence=None,
        fno_engine=None,
        knowledge_graph=None,
        results_calendar=None,
        calendar_harvester=None,
        causal_engine=None
    ):
        """
        Called by the Engine after construction to wire
        memory-driven intelligence layers.
        """
        self.pattern_engine = pattern_engine
        self.company_intelligence = company_intelligence
        self.event_intelligence = event_intelligence
        self.fno_engine = fno_engine
        self.knowledge_graph = knowledge_graph
        self.results_calendar = results_calendar
        self.calendar_harvester = calendar_harvester
        self.causal_engine = causal_engine

    # --------------------------------------------------

    def evaluate(
        self,
        symbol,
        ltp,
        orb,
        intelligence,
        entry_mode="ORB"
    ):
        self.breakouts += 1

        # ---------------------------------
        # Structural ORB Validation (Early Gate)
        # EVENT entries (Rule-001 catalyst override)
        # bypass the ORB structure gate — their gate
        # is the higher conviction bar downstream.
        # ---------------------------------
        if entry_mode != "EVENT":
            orb_result = self._score_orb(orb)
            if not orb_result["passed"]:
                self.skipped += 1
                return self._build_decision(
                    selected=False,
                    score=0,
                    reasons=[orb_result["reason"]],
                    brain_decision=None
                )

        # ---------------------------------
        # Institutional Decision Pipeline
        # ---------------------------------
        evidence = self.evidence_builder.build(intelligence)

        self.brain.update_intelligence()

        news_evidence = self.brain.build_news_evidence()
        print(f"[BRAIN] News Evidence Loaded : {len(news_evidence)}")

        # ---------------------------------
        # Company Memory : record stories
        # ---------------------------------
        if self.company_intelligence is not None:
            for story in self.brain.pending_stories:
                try:
                    self.company_intelligence.record_story(story)
                except Exception:
                    pass

        # ---------------------------------
        # Calendar Harvester : board-meeting
        # intimations → results calendar
        # ---------------------------------
        if self.calendar_harvester is not None:
            for story in self.brain.pending_stories:
                try:
                    self.calendar_harvester.harvest_story(
                        story
                    )
                except Exception:
                    pass

        # ---------------------------------
        # Event Intelligence : stories →
        # structured events → F&O watchlist
        # ---------------------------------
        if self.event_intelligence is not None:
            for story in self.brain.pending_stories:
                try:
                    events = (
                        self.event_intelligence.process_story(
                            story
                        )
                    )

                    for event in events:

                        if self.fno_engine is not None:
                            self.fno_engine.ingest_event(
                                event
                            )

                        # Causal reasoning: activate
                        # institutional cause-effect chains
                        if self.causal_engine is not None:
                            self.causal_engine.analyze(
                                event
                            )

                        # Knowledge-graph spillover:
                        # who else does this event touch?
                        if self.knowledge_graph is not None:
                            spillovers = (
                                self.knowledge_graph
                                    .propagate(event)
                            )
                            if spillovers:
                                self._recent_spillovers = (
                                    self._recent_spillovers
                                    + spillovers
                                )[-100:]
                except Exception as e:
                    print(f"[EVENT] {e}")

        # ---------------------------------
        # Pattern Evidence (memory-driven)
        # ---------------------------------
        pattern_evidence = []
        company_evidence = []

        sector_name = ""
        try:
            sector_snapshot = (
                intelligence.get("symbol", {}).get("sector")
                or {}
            )
            sector_name = sector_snapshot.get("sector_name", "") \
                or sector_snapshot.get("name", "")
        except Exception:
            pass

        if self.pattern_engine is not None:
            try:
                pattern_evidence = self.pattern_engine.build_evidence(
                    symbol,
                    sector_name
                )
            except Exception as e:
                print(f"[PATTERN] {e}")

        if self.company_intelligence is not None:
            try:
                company_evidence = (
                    self.company_intelligence.build_evidence(symbol)
                )
            except Exception as e:
                print(f"[COMPANY] {e}")

        # ---------------------------------
        # Event + F&O catalyst evidence
        # ---------------------------------
        event_evidence = []
        fno_evidence = []

        if self.event_intelligence is not None:
            try:
                event_evidence = (
                    self.event_intelligence.build_evidence(
                        symbol
                    )
                )
            except Exception as e:
                print(f"[EVENT] {e}")

        if self.fno_engine is not None:
            try:
                fno_evidence = (
                    self.fno_engine.build_evidence(symbol)
                )
            except Exception as e:
                print(f"[FNO] {e}")

        # ---------------------------------
        # Binary-event risk : results today?
        # ---------------------------------
        event_risk_evidence = []

        if self.results_calendar is not None:
            try:
                event_risk_evidence = (
                    self.results_calendar.build_evidence(
                        symbol
                    )
                )

                from config import RESULTS_DAY_BLOCK

                if (
                    RESULTS_DAY_BLOCK
                    and event_risk_evidence
                ):
                    self.skipped += 1
                    return self._build_decision(
                        selected=False,
                        score=0,
                        reasons=[
                            f"{symbol}: results/board "
                            f"meeting today — no new risk "
                            f"into binary events"
                        ],
                        brain_decision=None
                    )
            except Exception as e:
                print(f"[CALENDAR] {e}")

        # ---------------------------------
        # Sympathy spillover from graph
        # ---------------------------------
        sympathy_evidence = []

        if self.knowledge_graph is not None:
            try:
                sympathy_evidence = (
                    self.knowledge_graph
                        .build_sympathy_evidence(
                            symbol,
                            self._recent_spillovers
                        )
                )
            except Exception as e:
                print(f"[GRAPH] {e}")

        # ---------------------------------
        # Causal chain evidence
        # ---------------------------------
        causal_evidence = []

        if self.causal_engine is not None:
            try:
                causal_evidence = (
                    self.causal_engine.build_evidence(
                        symbol
                    )
                )
            except Exception as e:
                print(f"[CAUSAL] {e}")

        # ---------------------------------
        # News evidence is now part of the live
        # decision flow (structural + news + memory
        # + events + F&O catalysts + graph spillover
        # + binary-event risk).
        # ---------------------------------
        all_evidence = (
            evidence
            + news_evidence
            + pattern_evidence
            + company_evidence
            + event_evidence
            + fno_evidence
            + event_risk_evidence
            + sympathy_evidence
            + causal_evidence
        )

        validated_evidence = self.evidence_validator.validate(
            all_evidence
        )
        conviction = self.conviction_engine.evaluate(validated_evidence)

        if conviction.get("summary"):
            print(f"[CONVICTION] {conviction['summary']}")

        # ---------------------------------
        # Brain Evaluation (Shadow Mode)
        # ---------------------------------
        brain_decision = self.brain.evaluate(
            symbol=symbol,
            evidence_list=validated_evidence,
            conviction_snapshot=conviction
        )

        selected = (
            brain_decision.action == DecisionAction.BUY
        )
        if selected:
            self.opportunity_pool.add(
                symbol=symbol,
                conviction=brain_decision.score,
                quality=brain_decision.score,
                orb=orb,
                intelligence=intelligence,
                evidence=validated_evidence,
                brain_decision=brain_decision,
            )
            self.selected += 1
        else:
            self.skipped += 1

        # Wrapped tracer call in try-except block to guarantee zero trading disruption
        try:
            self.decision_trace.trace(
                symbol=symbol,
                orb=orb,
                intelligence=intelligence,
                evidence=validated_evidence,
                conviction=conviction,
                brain_decision=brain_decision,
                final_decision="BUY" if selected else "REJECT",
            )
        except Exception as e:
            print(f"[DecisionTrace] {e}")

        return self._build_decision(
            selected=selected,
            score=brain_decision.score,
            reasons=brain_decision.reasons,
            brain_decision=brain_decision
        )

    # --------------------------------------------------

    def _build_decision(
        self,
        selected,
        score,
        reasons,
        brain_decision=None
    ):
        return {
            "selected": selected,
            "queued": selected,
            "score": score,
            "reasons": reasons,
            "brain_decision": brain_decision
        }

    # --------------------------------------------------

    def _score_orb(
        self,
        orb
    ):
        if not orb or orb.get("high") is None or orb.get("low") is None:
            return {
                "passed": False,
                "score": 0,
                "reason": "ORB data unavailable"
            }

        orb_range_percent = ((orb["high"] - orb["low"]) / orb["low"]) * 100

        if orb_range_percent < MIN_ORB_RANGE_PERCENT:
            return {
                "passed": False,
                "score": 0,
                "reason": f"Weak ORB ({orb_range_percent:.2f}%)"
            }

        return {
            "passed": True,
            "score": 100,
            "reason": f"ORB Range {orb_range_percent:.2f}%"
        }

    # --------------------------------------------------

    def stats(self):
        return {
            "breakouts": self.breakouts,
            "selected": self.selected,
            "skipped": self.skipped
        }