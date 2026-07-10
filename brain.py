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
from typing import List

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
# Brain
# ==========================================================

class Brain:

    """
    Central decision coordinator.

    Every engine supplies Evidence.

    Brain supplies one Decision.
    """

    def __init__(self):

        self.memory = []

    # --------------------------------------------------

    def evaluate(

        self,

        symbol: str,

        evidence_list: List[Evidence]

    ) -> Decision:

        if not evidence_list:

            return Decision(

                symbol=symbol,

                action=DecisionAction.WAIT,

                confidence=0,

                score=0,

                warnings=["No evidence received."],

                evidence_used=0

            )

        total_score = 0

        total_confidence = 0

        recommendations = {}

        reasons = []

        warnings = []

        # ----------------------------------------------

        for evidence in evidence_list:

            snapshot = evidence.snapshot()

            recommendation = snapshot["recommendation"]

            score = snapshot["score"]

            confidence = snapshot["confidence"]

            priority = snapshot["priority"]

            reason = snapshot["reason"]

            total_score += score

            total_confidence += confidence

            reasons.append(

                f"{snapshot['provider']} : {reason}"

            )

            recommendations.setdefault(

                recommendation,

                0

            )

            recommendations[recommendation] += priority

        # ----------------------------------------------

        final_action = max(

            recommendations,

            key=recommendations.get

        )

        # ----------------------------------------------

        average_score = (

            total_score /

            len(evidence_list)

        )

        average_confidence = (

            total_confidence /

            len(evidence_list)

        )

        # ----------------------------------------------

        if len(recommendations) > 1:

            warnings.append(

                "Conflicting evidence detected."

            )

        decision = Decision(

            symbol=symbol,

            action=DecisionAction[final_action],

            confidence=average_confidence,

            score=average_score,

            reasons=reasons,

            warnings=warnings,

            evidence_used=len(evidence_list)

        )

        self.memory.append(decision)

        return decision

    # --------------------------------------------------

    def get_memory(self):

        return self.memory

    # --------------------------------------------------

    def clear_memory(self):

        self.memory.clear()