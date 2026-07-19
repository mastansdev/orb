from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class IntelligenceSnapshot:

    last_updated: datetime | None = None

    active_stories: list = field(default_factory=list)

    active_catalysts: list = field(default_factory=list)

    active_evidence: list = field(default_factory=list)

    market_state: dict = field(default_factory=dict)