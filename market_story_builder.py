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

from news_models import ClassifiedNews, MarketStory


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
            priority=classified_news.priority,
            lifecycle="NEW",
            expected_duration="UNKNOWN",
            supporting_news=[
                classified_news.news_id
            ],
            affected_symbols=list(
                classified_news.affected_symbols
            ),
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

        # --------------------------------------------------
        # Confidence Growth
        # --------------------------------------------------
        story.confidence = min(
            100,
            story.confidence + 5
        )

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
        story.updated_at = datetime.now()
        return story

    # --------------------------------------------------
    def _find_matching_story(
        self,
        classified_news
    ):
        """
        Find an existing Market Story that
        matches this classified news.

        Returns None if no suitable story
        exists.
        """
        # --------------------------------------------------
        for story in self.active_stories.values():

            # ----------------------------------------------
            # Same Catalyst
            # ----------------------------------------------
            if (
                story.catalyst 
                and story.catalyst == classified_news.catalyst
            ):
                return story

            # ----------------------------------------------
            # Same Theme
            # ----------------------------------------------
            if (
                story.theme 
                and story.theme == classified_news.theme
            ):
                return story

            # ----------------------------------------------
            # Same Industry
            # ----------------------------------------------
            if (
                story.industry 
                and story.industry == classified_news.industry
            ):
                return story

            # ----------------------------------------------
            # Same Sector
            # ----------------------------------------------
            if (
                story.sector 
                and story.sector == classified_news.sector
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