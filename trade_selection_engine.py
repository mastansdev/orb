from config import MIN_ORB_RANGE_PERCENT
from evidence_builder import EvidenceBuilder
from evidence_validator import EvidenceValidator
from conviction_engine import ConvictionEngine

class TradeSelectionEngine:

    def __init__(self):
        self.breakouts = 0
        self.selected = 0
        self.skipped = 0
        
        self.evidence_builder = EvidenceBuilder()
        self.evidence_validator = EvidenceValidator()
        self.conviction_engine = ConvictionEngine()

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
        # Institutional Decision Pipeline
        # ---------------------------------
        evidence = self.evidence_builder.build(intelligence)
        validated_evidence = self.evidence_validator.validate(evidence)
        conviction = self.conviction_engine.evaluate(validated_evidence)

        # Extract narrower scope payload
        symbol_intelligence = intelligence.get("symbol", {})

        # ---------------------------------
        # Evaluation Pipeline
        # ---------------------------------
        score = 0
        reasons = []

        # Define sequential evaluation filters targeted at symbol intelligence
        filters = [
            ("orb", lambda: self._score_orb(orb)),
            ("sector", lambda: self._score_generic_metric(symbol_intelligence, "sector", "Sector")),
            ("industry", lambda: self._score_generic_metric(symbol_intelligence, "industry", "Industry")),
            ("relative_strength", lambda: self._score_generic_metric(symbol_intelligence, "relative_strength", "RS")),
            ("theme", lambda: self._score_theme(symbol_intelligence))
        ]

        for filter_name, filter_func in filters:
            result = filter_func()
            
            if not result["passed"]:
                self.skipped += 1
                reasons.append(result["reason"])
                return self._build_decision(
                    selected=False,
                    score=score, 
                    reasons=reasons
                )
            
            score += result["score"]
            reasons.append(result["reason"])

        self.selected += 1
        return self._build_decision(
            selected=True,
            score=score,
            reasons=reasons
        )

    # --------------------------------------------------

    def _build_decision(
        self,
        selected,
        score,
        reasons
    ):
        return {
            "selected": selected,
            "score": score,
            "reasons": reasons
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

    def _score_generic_metric(
        self, 
        symbol_intelligence, 
        key, 
        display_name
    ):
        """Consolidates scoring architecture for Sector, Industry, and Relative Strength."""
        data = symbol_intelligence.get(key) or {}

        if not data:
            return {
                "passed": False,
                "score": 0,
                "reason": f"{display_name} data unavailable"
            }

        status = data.get("status")
        rank = data.get("rank", "-")

        if status == "STRONG":
            return {
                "passed": True,
                "score": 100,
                "reason": f"Strong {display_name} (Rank {rank})"
            }

        if status == "NEUTRAL":
            return {
                "passed": True,
                "score": 50,
                "reason": f"Neutral {display_name} (Rank {rank})"
            }

        return {
            "passed": False,
            "score": 0,
            "reason": f"Weak {display_name} ({status})"
        }

    # --------------------------------------------------

    def _score_theme(
        self,
        symbol_intelligence
    ):
        themes = symbol_intelligence.get("theme") or []
        strong_themes_count = sum(1 for theme in themes if theme.get("status") == "STRONG")

        if strong_themes_count == 0:
            return {
                "passed": True,
                "score": 0,
                "reason": "No Strong Themes"
            }

        score_mapping = {1: 20, 2: 40}
        score = score_mapping.get(strong_themes_count, 60)

        return {
            "passed": True,
            "score": score,
            "reasons": f"{strong_themes_count} Strong Theme(s)"
        }

    # --------------------------------------------------

    def stats(self):
        return {
            "breakouts": self.breakouts,
            "selected": self.selected,
            "skipped": self.skipped
        }