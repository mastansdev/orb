"""
==========================================================
News Models
==========================================================

Mission
-------
Provide standardized models used throughout the News
Intelligence subsystem.

Responsibilities
----------------
1. Standardize incoming news
2. Preserve original news
3. Track processing lifecycle
4. Provide structured data to downstream engines

Author : H&M ORB AUTO TRADER
==========================================================
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
import uuid


# ==========================================================
# News Source
# ==========================================================

class NewsSource(Enum):

    NSE = "NSE"

    BSE = "BSE"

    MONEYCONTROL = "Moneycontrol"

    ET = "Economic Times"

    MINT = "Mint"

    REUTERS = "Reuters"

    BLOOMBERG = "Bloomberg"

    INVESTING = "Investing"

    RBI = "RBI"

    SEBI = "SEBI"

    GOVERNMENT = "Government"

    COMMODITY = "Commodity Feed"

    GLOBAL = "Global"

    MANUAL = "Manual"

    UNKNOWN = "Unknown"


# ==========================================================
# News Category
# ==========================================================

class NewsCategory(Enum):

    CORPORATE = "Corporate"

    RESULT = "Result"

    ORDER = "Order"

    GOVERNMENT = "Government"

    POLICY = "Policy"

    REGULATORY = "Regulatory"

    COMMODITY = "Commodity"

    GLOBAL = "Global"

    MACRO = "Macro"

    MERGER = "Merger"

    ACQUISITION = "Acquisition"

    BULK_DEAL = "Bulk Deal"

    BLOCK_DEAL = "Block Deal"

    INSIDER = "Insider"

    PROMOTER = "Promoter"

    MARKET = "Market"

    SECTOR = "Sector"

    INDUSTRY = "Industry"

    THEME = "Theme"

    TECHNICAL = "Technical"

    UNKNOWN = "Unknown"


# ==========================================================
# News Priority
# ==========================================================

class NewsPriority(Enum):

    CRITICAL = 100

    VERY_HIGH = 90

    HIGH = 75

    MEDIUM = 50

    LOW = 25

    INFO = 10


# ==========================================================
# News Sentiment
# ==========================================================

class NewsSentiment(Enum):

    POSITIVE = "Positive"

    NEGATIVE = "Negative"

    NEUTRAL = "Neutral"

    UNKNOWN = "Unknown"


# ==========================================================
# News Status
# ==========================================================

class NewsStatus(Enum):

    NEW = "New"

    PROCESSED = "Processed"

    DUPLICATE = "Duplicate"

    CATALYST_CREATED = "Catalyst Created"

    EXPIRED = "Expired"


# ==========================================================
# Raw News
# ==========================================================

@dataclass
class RawNews:
    """
    Original news exactly as received.
    Never modified.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    headline: str = ""

    description: str = ""

    source: NewsSource = NewsSource.UNKNOWN

    category: NewsCategory = NewsCategory.UNKNOWN

    priority: NewsPriority = NewsPriority.INFO

    sentiment: NewsSentiment = NewsSentiment.UNKNOWN

    published_at: datetime = field(default_factory=datetime.now)

    received_at: datetime = field(default_factory=datetime.now)

    url: str = ""

    status: NewsStatus = NewsStatus.NEW


# ==========================================================
# Processed News
# ==========================================================

@dataclass
class ProcessedNews:
    """
    News enriched by the News Engine.
    Passed to NewsClassifier.
    """

    raw_news: RawNews

    processed_at: datetime = field(default_factory=datetime.now)

    themes: List[str] = field(default_factory=list)

    text_categories: List[str] = field(default_factory=list)

    industries: List[str] = field(default_factory=list)

    symbols: List[str] = field(default_factory=list)

    keywords: List[str] = field(default_factory=list)

    duplicate_of: Optional[str] = None

    source_count: int = 1

    confidence: float = 0.0

    notes: List[str] = field(default_factory=list)

    def add_note(self, note: str):

        self.notes.append(note)


# ==========================================================
# Classified News
# ==========================================================

@dataclass
class ClassifiedNews:
    """
    News enriched with market intelligence.
    Produced by NewsClassifier.
    Consumed by MarketStoryBuilder.
    """

    # --------------------------------------------------
    # Identity
    # --------------------------------------------------

    news_id: str

    # --------------------------------------------------
    # Original News
    # --------------------------------------------------

    headline: str

    summary: str

    source: NewsSource

    published_at: datetime

    received_at: datetime

    # --------------------------------------------------
    # Classification
    # --------------------------------------------------

    category: str

    subcategory: str

    event_type: str

    catalyst: str

    # --------------------------------------------------
    # Market Mapping
    # --------------------------------------------------

    sector: str

    industry: str

    theme: str

    affected_symbols: List[str]

    affected_assets: List[str]

    # --------------------------------------------------
    # Intelligence
    # --------------------------------------------------

    priority: int

    confidence: float

    classification_method: str


# ==========================================================
# Market Story
# ==========================================================

@dataclass
class MarketStory:
    """
    Living market narrative built from one or
    more classified news events.
    """

    # --------------------------------------------------
    # Identity
    # --------------------------------------------------

    story_id: str

    # --------------------------------------------------
    # Story
    # --------------------------------------------------

    name: str

    catalyst: str

    category: str

    subcategory: str

    event_type: str

    sector: str

    industry: str

    theme: str

    # --------------------------------------------------
    # Intelligence
    # --------------------------------------------------

    confidence: float

    priority: int

    lifecycle: str

    expected_duration: str

    # --------------------------------------------------
    # Relationships
    # --------------------------------------------------

    supporting_news: List[str]

    affected_symbols: List[str]

    # --------------------------------------------------
    # Timeline
    # --------------------------------------------------

    created_at: datetime

    updated_at: datetime

    # --------------------------------------------------
    # Analysis Notes
    # --------------------------------------------------

    notes: List[str] = field(default_factory=list)


# ==========================================================
# Impact Result
# ==========================================================

@dataclass
class ImpactResult:
    """
    Market impact assessment generated
    from a Market Story.
    Produced by ImpactEngine.
    Consumed by NewsEvidenceBuilder.
    """

    # --------------------------------------------------
    # Story
    # --------------------------------------------------

    story_id: str

    rule_name: str

    category: str

    subcategory: str

    event_type: str

    # --------------------------------------------------
    # Impact
    # --------------------------------------------------

    market_impact: str

    market_score: int

    sector_score: int

    stock_score: int

    expected_duration: str

    # --------------------------------------------------
    # Rule Confidence
    # --------------------------------------------------

    confidence: float

    confidence_source: str

    market_regime_hint: str

    # --------------------------------------------------
    # Market Mapping
    # --------------------------------------------------

    bullish_sectors: List[str]

    bearish_sectors: List[str]

    direct_assets: List[str]

    indirect_assets: List[str]

    # --------------------------------------------------
    # Historical Behaviour
    # --------------------------------------------------

    historical_winners: List[str]

    historical_losers: List[str]

    # --------------------------------------------------
    # Analysis
    # --------------------------------------------------

    notes: List[str] = field(default_factory=list)