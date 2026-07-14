# =============================================================================
# CORE ARCHITECTURE FILE
#
# This file is considered STABLE.
# Do not modify unless a project-wide architectural change is approved.
# =============================================================================

"""
==========================================================
Evidence
==========================================================

Mission
-------
Provide a standardized evidence object used by every
intelligence engine in the trading system.

Every engine must communicate with the Brain using
Evidence objects.

Responsibilities
----------------
1. Represent objective evidence
2. Preserve explainable reasoning
3. Standardize communication between engines

This class NEVER:
- Makes decisions
- Scores trades
- Executes orders
- Manages portfolio

Author : H&M ORB AUTO TRADER
==========================================================
"""

from copy import deepcopy
from datetime import datetime


class Evidence:
    """
    Standardized evidence exchanged between all engines
    and the Brain.
    """

    def __init__(
        self,
        provider: str,
        symbol: str = "",
        question: str = "",
        recommendation: str = "WAIT",
        score: float = 0.0,
        confidence: float = 0.0,
        priority: int = 0,
        reason: str = "",
        facts: dict = None,
        metadata: dict = None,
    ):

        self._data = {

            "provider": provider,

            "symbol": symbol,

            "question": question,

            "recommendation": recommendation,

            "score": score,

            "confidence": confidence,

            "priority": priority,

            "reason": reason,

            "timestamp": datetime.now(),

            "facts": facts or {},

            "metadata": metadata or {}

        }

    # --------------------------------------------------

    @property
    def provider(self):
        return self._data["provider"]

    @property
    def symbol(self):
        return self._data["symbol"]

    @property
    def recommendation(self):
        return self._data["recommendation"]

    @property
    def score(self):
        return self._data["score"]

    @property
    def confidence(self):
        return self._data["confidence"]

    @property
    def priority(self):
        return self._data["priority"]

    @property
    def reason(self):
        return self._data["reason"]

    @property
    def timestamp(self):
        return self._data["timestamp"]

    @property
    def facts(self):
        return self._data["facts"]

    @property
    def metadata(self):
        return self._data["metadata"]

    # --------------------------------------------------

    def snapshot(self):
        """
        Returns a deep copy of the complete evidence.
        """
        return deepcopy(self._data)

    # --------------------------------------------------

    def __repr__(self):

        return (

            f"Evidence("

            f"provider='{self.provider}', "

            f"symbol='{self.symbol}', "

            f"recommendation='{self.recommendation}', "

            f"score={self.score}, "

            f"confidence={self.confidence}, "

            f"priority={self.priority})"

        )