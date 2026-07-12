from evidence import Evidence

class NewsEvidenceBuilder:
    """
    Converts Market Story intelligence
    into standardized Brain Evidence.
    """

    def __init__(self):
        pass

    # --------------------------------------------------

    def build(
        self,
        story,
        impact
    ):
        """
        Build Brain Evidence from
        Market Story + Impact.
        """
        # --------------------------------------------------
        # Recommendation
        # --------------------------------------------------
        recommendation = self._recommendation(
            story,
            impact
        )

        # --------------------------------------------------
        # Score
        # --------------------------------------------------
        score = self._score(
            story,
            impact
        )

        # --------------------------------------------------
        # Reason
        # --------------------------------------------------
        reason = self._reason(
            story,
            impact
        )

        # --------------------------------------------------
        # Evidence
        # --------------------------------------------------
        return Evidence(
            provider="NEWS",
            recommendation=recommendation,
            score=score,
            confidence=max(
                0,
                min(
                    100,
                    story.confidence
                )
            ),
            priority=max(
                0,
                min(
                    100,
                    story.priority
                )
            ),
            reason=reason
        )

    # --------------------------------------------------
    def _recommendation(
        self,
        story,
        impact
    ):
        """
        Convert Market Story into
        BUY / WAIT / IGNORE.
        """
        # --------------------------------------------------
        # News alone never triggers a trade.
        # It prepares the Brain to watch the opportunity.
        # --------------------------------------------------
        return "WAIT"

    # --------------------------------------------------
    def _score(
        self,
        story,
        impact
    ):
        """
        Calculate News Evidence score.
        """
        # --------------------------------------------------
        # Base Story Confidence
        # --------------------------------------------------
        score = story.confidence

        # --------------------------------------------------
        # Market Impact
        # --------------------------------------------------
        score += impact.market_score * 3

        # --------------------------------------------------
        # Sector Impact
        # --------------------------------------------------
        score += impact.sector_score * 2

        # --------------------------------------------------
        # Stock Impact
        # --------------------------------------------------
        score += impact.stock_score

        # --------------------------------------------------
        # Normalize
        # --------------------------------------------------
        return max(
            0,
            min(
                100,
                score
            )
        )

    # --------------------------------------------------
    def _reason(
        self,
        story,
        impact
    ):
        """
        Build explainable reason.
        """
        parts = []
        
        # --------------------------------------------------
        # Theme
        # --------------------------------------------------
        if story.theme:
            parts.append(
                f"Theme={story.theme}"
            )

        # --------------------------------------------------
        # Sector
        # --------------------------------------------------
        if story.sector:
            parts.append(
                f"Sector={story.sector}"
            )

        # --------------------------------------------------
        # Impact
        # --------------------------------------------------
        if getattr(impact, "market_impact", None):
            parts.append(
                f"Impact={impact.market_impact}"
            )

        # --------------------------------------------------
        # Priority
        # --------------------------------------------------
        if getattr(story, "priority", None) is not None:
            parts.append(
                f"Priority={story.priority:.0f}"
            )

        # --------------------------------------------------
        # Confidence
        # --------------------------------------------------
        if getattr(story, "confidence", None) is not None:
            parts.append(
                f"Confidence={story.confidence:.0f}"
            )

        # --------------------------------------------------
        # Duration
        # --------------------------------------------------
        if getattr(impact, "expected_duration", None):
            parts.append(
                f"Duration={impact.expected_duration}"
            )

        return " | ".join(parts)