from intelligence.evidence import Evidence

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
        impact,
        symbol="",
    ):
        """
        Build Brain Evidence from
        Market Story + Impact.

        Fix (2026-07-21): `symbol` was never passed here --
        every MARKET_STORY evidence item carried symbol=""
        (Evidence's own default), and nothing downstream
        filtered on it, so ANY news about ANY stock was being
        applied to EVERY stock's conviction score for the
        30-minute cache window. Now the caller (Brain.
        build_news_evidence) passes the actual symbol this
        evidence is for, one call per affected symbol.
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
            provider="MARKET_STORY",
            symbol=symbol,
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
            reason=reason,
            facts={
                "story_name": story.name,
                "story_strength": story.story_strength,
                "story_direction": story.story_direction,
                "evidence_count": story.evidence_count,
                "contradiction_count": story.contradiction_count,
                "lifecycle": story.lifecycle
            }
        )

    # --------------------------------------------------
    def _recommendation(
        self,
        story,
        impact
    ):
        """
        Convert Market Story into
        BUY / SELL / WAIT.

        Fix (2026-07-22): this used to unconditionally return
        "WAIT" -- the story and impact parameters were accepted
        but never actually read. Confirmed live: this meant NO
        piece of news evidence, ever, regardless of content,
        could vote in the conviction engine's bullish/bearish
        alignment check (WAIT isn't in either vocabulary list).
        A single news item still shouldn't be the ONLY thing
        that can force a trade -- that philosophy was right --
        but it must be able to at least vote against a bad one,
        which it structurally never could. Same net-impact
        weighting as _score() below and Brain.build_news_
        evidence's story_direction fix, so all three stay
        consistent with each other.
        """
        net_impact = (
            impact.market_score * 3
            + impact.sector_score * 2
            + impact.stock_score
        )

        if net_impact > 0:
            return "BUY"
        if net_impact < 0:
            return "SELL"
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