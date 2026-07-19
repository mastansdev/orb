"""
==========================================================
Conviction Engine
==========================================================

Implements CONVICTION_SPECIFICATION.md Section 6:

    Conviction is NOT  30 + 20 + 15 = 65

    Conviction IS      Strength × Agreement × Confidence

Responsibility:
    • Receive validated evidence
    • Evaluate conviction
    • Produce a unified conviction snapshot

This engine NEVER:
    • collects market data
    • ranks sectors
    • reads news
    • manages portfolio risk
    • sizes positions
    • executes trades
    • audits decisions

Author : H&M ORB AUTO TRADER
==========================================================
"""

from copy import deepcopy

from config import (
    CONVICTION_GRADE_A_PLUS,
    CONVICTION_GRADE_A,
    CONVICTION_GRADE_B,
)


class ConvictionEngine:

    REQUIRED_PROVIDERS = (
        "sector",
        "industry",
        "relative_strength",
        "theme",
    )

    OPTIONAL_PROVIDERS = (
        "results",
        "market_mood",
        "breadth",
        "news",
        "institutional_flow",
        "MARKET_STORY",
        "PATTERN",
        "COMPANY",
        "EVENT",
        "FNO_CATALYST",
        "CAUSAL",
        "SYMPATHY",
        "EVENT_RISK",
        "RESULTS_LIVE",
    )

    # Environment providers influence conviction but can
    # never form it on their own (Spec Section 4).
    INFLUENCE_ONLY_PROVIDERS = (
        "market_mood",
        "breadth",
    )

    # Recommendations counted as bullish / bearish for the
    # Agreement calculation.
    BULLISH = ("BUY", "STRONG", "LEADER", "POSITIVE", "BULLISH")
    BEARISH = ("SELL", "WEAK", "LAGGARD", "NEGATIVE", "BEARISH", "AVOID")

    # --------------------------------------------------

    def __init__(self):
        pass

    # --------------------------------------------------

    def _index_evidence(self, evidence_list):
        providers = {}

        for evidence in evidence_list:
            provider = evidence.provider
            if provider:
                providers[provider] = evidence

        return providers

    # --------------------------------------------------

    def _default_snapshot(self):
        return {
            "score": None,
            "grade": None,
            "alignment": None,
            "confidence": None,
            "strength": None,
            "agreement": None,
            "contributors": {},
            "provider_count": 0,
            "required_present": [],
            "missing_required": [],
            "optional_present": [],
            "conflicts": [],
            "ready_for_scoring": False,
            "summary": None,
        }

    # --------------------------------------------------
    # Component 1 : Strength
    # --------------------------------------------------

    def _strength(self, providers):
        """
        Average provider score (0-100), using only
        providers that actually supplied a score.

        Influence-only providers are excluded here —
        they act later through Confidence.
        """
        scores = []

        for name, evidence in providers.items():
            if name in self.INFLUENCE_ONLY_PROVIDERS:
                continue

            score = evidence.score

            if score is not None and score > 0:
                scores.append(min(100.0, float(score)))

        if not scores:
            return 0.0

        return sum(scores) / len(scores)

    # --------------------------------------------------
    # Component 2 : Agreement
    # --------------------------------------------------

    def _direction(self, evidence):
        recommendation = str(
            evidence.recommendation or ""
        ).upper()

        if recommendation in self.BULLISH:
            return 1

        if recommendation in self.BEARISH:
            return -1

        return 0

    # --------------------------------------------------

    def _agreement(self, providers):
        """
        Fraction of directional providers that agree with
        the dominant direction (0.0 – 1.0).

        Neutral (WAIT) providers do not vote.
        """
        votes = []

        for name, evidence in providers.items():
            if name in self.INFLUENCE_ONLY_PROVIDERS:
                continue

            direction = self._direction(evidence)

            if direction != 0:
                votes.append((name, direction))

        if not votes:
            # No directional evidence at all:
            # structural presence only. Neutral agreement.
            return 0.5, "NEUTRAL", []

        bullish = [name for name, d in votes if d > 0]
        bearish = [name for name, d in votes if d < 0]

        conflicts = []
        if bullish and bearish:
            conflicts.append(
                f"Bullish={bullish} vs Bearish={bearish}"
            )

        dominant = max(len(bullish), len(bearish))
        agreement = dominant / len(votes)

        if len(bullish) >= len(bearish):
            alignment = "BULLISH"
        else:
            alignment = "BEARISH"

        return agreement, alignment, conflicts

    # --------------------------------------------------
    # Component 3 : Confidence
    # --------------------------------------------------

    def _confidence(self, providers, missing_required, conflicts):
        """
        Average provider confidence, discounted by:
          • incompleteness (missing required providers)
          • conflicts (Spec Section 7: conflict never
            rejects — it reduces conviction)
        """
        confidences = [
            float(evidence.confidence or 0)
            for evidence in providers.values()
        ]

        if not confidences:
            return 0.0

        confidence = sum(confidences) / len(confidences)

        # Completeness discount: each missing required
        # provider removes 15% of confidence.
        completeness = 1.0 - (0.15 * len(missing_required))
        confidence *= max(0.4, completeness)

        # Conflict discount (Section 7)
        if conflicts:
            confidence *= 0.80

        return min(100.0, confidence)

    # --------------------------------------------------
    # Grade
    # --------------------------------------------------

    def _grade(self, score):
        if score >= CONVICTION_GRADE_A_PLUS:
            return "A+"
        if score >= CONVICTION_GRADE_A:
            return "A"
        if score >= CONVICTION_GRADE_B:
            return "B"
        return "C"

    # --------------------------------------------------
    # PUBLIC : Evaluate
    # --------------------------------------------------

    def evaluate(self, evidence_list):
        """
        Convert validated evidence into one conviction
        snapshot:

            conviction = Strength × Agreement × Confidence

        normalized back to a 0-100 score.
        """
        snapshot = self._default_snapshot()

        providers = self._index_evidence(evidence_list)

        snapshot["contributors"] = providers
        snapshot["provider_count"] = len(providers)

        snapshot["required_present"] = [
            provider
            for provider in self.REQUIRED_PROVIDERS
            if provider in providers
        ]

        snapshot["missing_required"] = [
            provider
            for provider in self.REQUIRED_PROVIDERS
            if provider not in providers
        ]

        snapshot["optional_present"] = [
            provider
            for provider in self.OPTIONAL_PROVIDERS
            if provider in providers
        ]

        snapshot["ready_for_scoring"] = (
            len(snapshot["missing_required"]) == 0
        )

        # ---------------------------------
        # Conviction Calculation
        # ---------------------------------

        strength = self._strength(providers)

        agreement, alignment, conflicts = self._agreement(
            providers
        )

        confidence = self._confidence(
            providers,
            snapshot["missing_required"],
            conflicts,
        )

        # Strength(0-100) × Agreement(0-1) × Confidence(0-1)
        score = strength * agreement * (confidence / 100.0)
        score = max(0.0, min(100.0, score))

        snapshot["strength"] = round(strength, 2)
        snapshot["agreement"] = round(agreement, 2)
        snapshot["confidence"] = round(confidence, 2)
        snapshot["alignment"] = alignment
        snapshot["conflicts"] = conflicts
        snapshot["score"] = round(score, 2)
        snapshot["grade"] = self._grade(score)

        snapshot["summary"] = (
            f"Conviction {snapshot['score']:.1f} "
            f"({snapshot['grade']}) = "
            f"Strength {strength:.1f} × "
            f"Agreement {agreement:.2f} × "
            f"Confidence {confidence:.1f}%"
            + (" | CONFLICT" if conflicts else "")
            + (
                ""
                if snapshot["ready_for_scoring"]
                else f" | Missing: {snapshot['missing_required']}"
            )
        )

        return deepcopy(snapshot)
