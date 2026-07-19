"""
===============================================================================
BrainContext
===============================================================================

Mission
-------
BrainContext is the single source of truth for Brain V2.

It stores all intelligence collected from various engines for one stock
evaluation.

Every engine publishes information here.

Brain V2 reads information from here.

Responsibilities
----------------
1. Store intelligence
2. Standardize communication between engines
3. Provide a single view of market context

This class NEVER:
- Makes decisions
- Scores opportunities
- Executes trades
- Calls any engine

Author : H&M ORB AUTO TRADER
===============================================================================
"""


class BrainContext:
    """
    Shared intelligence container for Brain V2.
    """

    def __init__(self):

        # ==============================================================
        # Static Intelligence
        # ==============================================================

        self.symbol = ""
        self.company = ""

        self.sector = {}
        self.industry = {}
        self.themes = []

        self.business = ""
        self.market_cap = ""
        self.ownership = ""

        self.commodity_exposure = ""
        self.economic_sensitivity = ""

        # ==============================================================
        # Daily Intelligence
        # ==============================================================

        self.previous_close = 0.0
        self.gap_percent = 0.0

        self.results_calendar = {}
        self.corporate_actions = {}

        # ==============================================================
        # Live Intelligence
        # ==============================================================

        self.ltp = 0.0

        self.sector_strength = 0.0
        self.industry_strength = 0.0
        self.theme_strength = 0.0

        self.relative_strength = 0.0

        self.volume_strength = 0.0

        self.market_breadth = 0.0
        self.market_mood = 0.0
        self.institutional_score = 0.0

        self.continuation_probability = 0.0

        # ==============================================================
        # Event Intelligence
        # ==============================================================

        self.news = []

        self.results = {}

        self.government = {}

        self.global_events = []

        # ==============================================================
        # Market Intelligence
        # ==============================================================

        self.market_regime = ""

        self.market_story = {}

        self.leading_sector = ""

        self.leading_industry = ""

        self.leading_theme = ""

        # ==============================================================
        # Execution Context
        # ==============================================================

        self.execution_strategy = ""

        self.orb_status = ""

        self.entry_allowed = False

        self.override_allowed = False

        self.risk_level = ""