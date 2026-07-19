from intelligence.evidence import Evidence


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
        """Helper to instantiate and populate an Evidence object."""
        evidence = Evidence(
            provider=provider,
            recommendation=direction,
            score=strength,
            confidence=confidence,
            reason=freshness,
            facts=facts,
            metadata=metadata or {}
        )
        return evidence

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

        symbol_snapshot = intelligence.get("symbol", {})

        print("\n========== INDUSTRY SNAPSHOT ==========")
        print(symbol_snapshot.get("industry"))
        print("=======================================\n")

        market_snapshot = intelligence.get("market", {})

        # --- Sector Analysis ---
        sector_snapshot = symbol_snapshot.get("sector")

        print("\n========== SECTOR SNAPSHOT ==========")
        print(sector_snapshot)
        print("====================================\n")
        
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

        # --- Industry Analysis ---
        industry_snapshot = symbol_snapshot.get("industry")
        if industry_snapshot:
            evidence.append(
                self._create_evidence(
                    provider="industry",
                    direction=industry_snapshot.get("status"),
                    strength=industry_snapshot.get("participation"),
                    confidence=100,
                    freshness="LIVE",
                    facts=industry_snapshot,
                    metadata={
                        "rank": industry_snapshot.get("rank"),
                        "leader": industry_snapshot.get("leader"),
                        "laggard": industry_snapshot.get("laggard")
                    }
                )
            )

        # --- Theme Analysis ---
        theme_list = symbol_snapshot.get("theme", [])
        if theme_list:
            best_theme = max(
                theme_list,
                key=lambda x: x.get("participation", 0)
            )

            evidence.append(
                self._create_evidence(
                    provider="theme",
                    direction=best_theme.get("status"),
                    strength=best_theme.get("participation"),
                    confidence=100,
                    freshness="LIVE",
                    facts=best_theme,
                    metadata={
                        "rank": best_theme.get("rank"),
                        "leader": best_theme.get("leader"),
                        "laggard": best_theme.get("laggard"),
                        "theme": best_theme.get("name")
                    }
                )
            )

        # --- Relative Strength Analysis ---
        relative_strength_snapshot = symbol_snapshot.get("relative_strength")
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