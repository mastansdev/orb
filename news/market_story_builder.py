"""
==========================================================
Market Story Builder
==========================================================

Mission
-------
Transform classified news into one or more evolving
Market Stories.

Markets do not trade headlines.

Markets trade stories.

Responsibilities
----------------
1. Merge related news
2. Detect dominant catalyst
3. Detect dominant sector
4. Detect dominant industry
5. Detect dominant theme
6. Estimate story confidence
7. Estimate story lifecycle
8. Return structured MarketStory objects

Author : H&M ORB AUTO TRADER
==========================================================
"""

from datetime import datetime, timedelta
from typing import List
import uuid

from news.news_models import ClassifiedNews, MarketStory


class MarketStoryBuilder:

    """
    Converts classified news into
    institutional market stories.
    """

    def __init__(self):

        self.active_stories = {}

    # --------------------------------------------------
    def _create_story(
        self,
        classified_news
    ):
        """
        Create a new Market Story from
        classified news.
        """
        story = MarketStory(
            story_id=str(uuid.uuid4()),
            name=classified_news.theme
            or classified_news.industry
            or classified_news.sector
            or classified_news.category
            or "UNKNOWN",
            catalyst=classified_news.catalyst,
            category=classified_news.category,
            subcategory=classified_news.subcategory,
            event_type=classified_news.event_type,
            sector=classified_news.sector,
            industry=classified_news.industry,
            theme=classified_news.theme,
            confidence=classified_news.confidence,
            story_strength=classified_news.confidence,
            story_direction="STRENGTHENING",
            priority=classified_news.priority,
            lifecycle="NEW",
            expected_duration="UNKNOWN",
            supporting_news=[
                classified_news.news_id
            ],
            affected_symbols=list(
                classified_news.affected_symbols
            ),
            leading_symbols=list(
                classified_news.affected_symbols
            ),

            evidence_count=1,

            contradiction_count=0,

            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.active_stories[story.story_id] = story
        return story

    # --------------------------------------------------
    def _merge_story(
        self,
        story,
        classified_news
    ):
        """
        Merge related news into an
        existing Market Story.
        """
        # --------------------------------------------------
        # Add supporting news
        # --------------------------------------------------
        if classified_news.news_id not in story.supporting_news:
            story.supporting_news.append(
                classified_news.news_id
            )
        story.evidence_count = len(
            story.supporting_news
        )    

        # --------------------------------------------------
        # Merge affected symbols
        # --------------------------------------------------
        for symbol in classified_news.affected_symbols:
            if symbol not in story.affected_symbols:
                story.affected_symbols.append(symbol)
        
        story.leading_symbols = list(
            story.affected_symbols
        )

        # --------------------------------------------------
        # Confidence Growth
        # --------------------------------------------------
        news_confidence = classified_news.confidence or 0
        story.confidence = min(
            100,
            max(story.confidence, news_confidence) + 2
        )

        story.story_strength = story.confidence

        # --------------------------------------------------
        # Lifecycle
        # --------------------------------------------------
        news_count = len(
            story.supporting_news
        )
        if news_count == 1:
            story.lifecycle = "NEW"
        elif news_count <= 3:
            story.lifecycle = "DEVELOPING"
        elif news_count <= 6:
            story.lifecycle = "STRONG"
        else:
            story.lifecycle = "DOMINANT"

        # --------------------------------------------------
        # Update Timestamp
        # --------------------------------------------------
        story.story_direction = "STRENGTHENING"
        story.updated_at = datetime.now()
        return story

    # --------------------------------------------------
    # How long a story stays eligible to absorb new news via
    # theme/industry matching. Catalyst matches have no time
    # limit -- a shared, specific catalyst is strong enough
    # evidence on its own regardless of how much time has passed.
    STORY_MERGE_WINDOW = timedelta(hours=2)

    def _find_matching_story(
        self,
        classified_news
    ):
        """
        Find an existing Market Story that matches this classified
        news.

        Fix (2026-07-20): this used to merge on ANY SINGLE ONE of
        catalyst/theme/industry/SECTOR matching, with no recency
        limit. Confirmed live in production: this let a handful of
        giant, incoherent "mega stories" form per sector -- e.g. a
        real PHARMA story ballooned to 30 symbols including BSE,
        RELIANCE, DMART, and BOSCHLTD (none of them pharma
        companies), and a BANKING story reached ~100 symbols
        spanning banks, hotels, cement, and IT. Root cause: sector
        is a very broad tag (dozens of unrelated companies share
        one), and with no recency check an old story kept silently
        absorbing every new headline that loosely matched its
        sector, all day long.

        New merge criteria, ranked strongest to weakest:

        1. Same non-empty CATALYST -- the most specific,
           narrative-level signal (e.g. a named M&A deal, a
           specific results announcement). No recency limit: a
           real shared catalyst is strong evidence on its own.
        2. Same non-empty THEME or INDUSTRY -- narrower than
           sector, but still broad enough to need a recency guard
           (STORY_MERGE_WINDOW) so an hours-old story doesn't keep
           absorbing unrelated new headlines indefinitely.
        3. SECTOR ALONE is deliberately no longer a merge trigger.
           It was the primary driver of the mega-story problem --
           a genuine sector-wide rotation story should only form
           from repeated theme/industry signals, not a single bare
           sector-tag coincidence between two unrelated headlines.

        Returns None if no suitable story exists.
        """
        now = datetime.now()

        # ----------------------------------------------
        # 1. Same catalyst -- strongest signal, no recency limit
        # ----------------------------------------------
        if classified_news.catalyst:
            for story in self.active_stories.values():
                if (
                    story.catalyst
                    and story.catalyst == classified_news.catalyst
                ):
                    return story

        # ----------------------------------------------
        # 2. Same theme or industry -- requires recency
        # ----------------------------------------------
        for story in self.active_stories.values():

            if now - story.updated_at > self.STORY_MERGE_WINDOW:
                continue

            if (
                classified_news.theme
                and story.theme
                and story.theme == classified_news.theme
            ):
                return story

            if (
                classified_news.industry
                and story.industry
                and story.industry == classified_news.industry
            ):
                return story

        return None

    # --------------------------------------------------
    def _expire_story(
        self,
    ):
        """
        Remove stories that are no longer
        relevant to today's market.
        """
        expired = []
        for story_id, story in self.active_stories.items():
            age = datetime.now() - story.updated_at
            if age > timedelta(hours=24):
                expired.append(story_id)
        # ----------------------------------------------
        for story_id in expired:
            del self.active_stories[story_id]

    # --------------------------------------------------
    def build(
        self,
        news_items: List[ClassifiedNews]
    ):
        """
        Build Market Stories.
        """
        # --------------------------------------------------
        # Remove expired stories
        # --------------------------------------------------
        self._expire_story()
        
        # --------------------------------------------------
        new_or_updated_stories = []
        for news in news_items:
            story = self._find_matching_story(news)
            if story:
                story = self._merge_story(
                    story,
                    news
                )
            else:
                story = self._create_story(
                    news
                )
            new_or_updated_stories.append(
                story
            )
        return new_or_updated_stories