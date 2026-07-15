from config import MIN_ORB_RANGE_PERCENT
from evidence_builder import EvidenceBuilder
from evidence_validator import EvidenceValidator
from conviction_engine import ConvictionEngine
from brain import Brain, DecisionAction
from tools.decision_trace import DecisionTrace # 1. Import added

class TradeSelectionEngine:

    def __init__(self):
        self.breakouts = 0
        self.selected = 0
        self.skipped = 0
        
        self.evidence_builder = EvidenceBuilder()
        self.evidence_validator = EvidenceValidator()
        self.conviction_engine = ConvictionEngine()
        self.brain = Brain()
        self.decision_trace = DecisionTrace()  # 2. Initialized here

    # --------------------------------------------------

    def evaluate(
        self,
        symbol,
        ltp,
        orb,
        intelligence
    ):
        self.breakouts += 1

        # ---------------------------------
        # Structural ORB Validation (Early Gate)
        # ---------------------------------
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
        
        all_evidence = evidence + news_evidence

        # Kept unchanged for live session safety (ignoring news_evidence for now)
        validated_evidence = self.evidence_validator.validate(evidence)
        conviction = self.conviction_engine.evaluate(validated_evidence)

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
            self.selected += 1
        else:
            self.skipped += 1

        # 3. Wrapped tracer call in try-except block to guarantee zero trading disruption
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