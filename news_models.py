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
    Passed to Catalyst Processor.
    """

    raw_news: RawNews

    processed_at: datetime = field(default_factory=datetime.now)

    themes: List[str] = field(default_factory=list)

    industries: List[str] = field(default_factory=list)

    symbols: List[str] = field(default_factory=list)

    keywords: List[str] = field(default_factory=list)

    duplicate_of: Optional[str] = None

    source_count: int = 1

    confidence: float = 0.0

    notes: List[str] = field(default_factory=list)

    def add_note(self, note: str):

        self.notes.append(note)