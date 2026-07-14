from copy import deepcopy


class ConvictionEngine:
    """
    Institutional Conviction Engine

    Responsibility:
        • Receive normalized evidence
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
    """

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
    )

    INFLUENCE_ONLY_PROVIDERS = (
        "market_mood",
    )

    # --------------------------------------------------

    def __init__(self):
        pass

    # --------------------------------------------------

    def _index_evidence(
        self,
        evidence_list
    ):
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
            "contributors": {},
            "provider_count": 0,
            "required_present": [],
            "missing_required": [],
            "optional_present": [],
            "ready_for_scoring": False,
            "summary": None
        }

    # --------------------------------------------------

    def evaluate(
        self,
        evidence_list
    ):
        """
        Phase 2

        Organize validated evidence.

        No conviction calculation yet.
        """
        snapshot = self._default_snapshot()

        providers = self._index_evidence(
            evidence_list
        )

        snapshot["contributors"] = providers

        snapshot["provider_count"] = len(
            providers
        )

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

        return deepcopy(snapshot)