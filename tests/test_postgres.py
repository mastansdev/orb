import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repositories.intelligence_repository import IntelligenceRepository
from news.news_models import MarketStory
from datetime import datetime

repo = IntelligenceRepository()

story = MarketStory(
    story_id="TEST001",
    name="TEST STORY",
    catalyst="RESULTS",
    category="EARNINGS",
    subcategory="QUARTERLY",
    event_type="RESULT",
    sector="IT",
    industry="SOFTWARE",
    theme="AI",
    confidence=90,
    story_strength=90,
    story_direction="STRENGTHENING",
    priority=1,
    lifecycle="NEW",
    expected_duration="SHORT",
    supporting_news=[],
    affected_symbols=[],
    leading_symbols=[],
    evidence_count=1,
    contradiction_count=0,
    created_at=datetime.now(),
    updated_at=datetime.now()
)

repo.save_story(story)

stories = repo.load_intelligence()

print(stories[-1])