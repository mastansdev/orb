from evidence import Evidence


class EvidenceBuilder:
    """
    Institutional Evidence Builder

    Responsibility:
        • Convert intelligence snapshots into Evidence objects.

    It NEVER:
        • validates evidence
        • calculates conviction
        • executes trades
        • fetches market data
    """

    def __init__(self):
        pass

    # --------------------------------------------------

    def _create_evidence(
        self,
        provider,
        direction,
        strength,
        confidence,
        freshness,
        facts,
        metadata=None
    ):
        """Helper to instantiate, populate, and snapshot an Evidence object."""
        evidence = Evidence(
            provider=provider,
            recommendation=direction,
            score=strength,
            confidence=confidence,
            reason=freshness,
            facts=facts,
            metadata=metadata or {}
        )
        return evidence.snapshot()

    # --------------------------------------------------

    def build(
        self,
        intelligence
    ):
        """
        Build Evidence collection from the
        Intelligence Snapshot.
        """
        evidence = []
        if not intelligence:
            return evidence

        # --- Sector Analysis ---
        sector_snapshot = intelligence.get("sector")
        if sector_snapshot:
            evidence.append(
                self._create_evidence(
                    provider="sector",
                    direction=sector_snapshot.get("status"),
                    strength=sector_snapshot.get("participation"),
                    confidence=100,
                    freshness="LIVE",
                    facts=sector_snapshot,
                    metadata={
                        "rank": sector_snapshot.get("rank"),
                        "leader": sector_snapshot.get("leader"),
                        "laggard": sector_snapshot.get("laggard")
                    }
                )
            )

        # --- Relative Strength Analysis ---
        relative_strength_snapshot = intelligence.get("relative_strength")
        if relative_strength_snapshot:
            evidence.append(
                self._create_evidence(
                    provider="relative_strength",
                    direction=relative_strength_snapshot.get("status"),
                    strength=relative_strength_snapshot.get("percentile"),
                    confidence=100,
                    freshness="LIVE",
                    facts=relative_strength_snapshot,
                    metadata={
                        "rank": relative_strength_snapshot.get("rank"),
                        "leader": relative_strength_snapshot.get("is_leader"),
                        "score": relative_strength_snapshot.get("score")
                    }
                )
            )

        return evidence