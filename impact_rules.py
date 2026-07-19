"""
Impact Rules

Responsibilities
----------------
Institutional market knowledge base.

Defines historical relationships between market catalysts and their
typical effects on:

    • Market Regime
    • Assets
    • Sectors
    • Capital Flow

Contains NO business logic.

ImpactEngine is responsible for reading these rules.

This file should only contain knowledge.
"""

# ==================================================
# Global Constants
# ==================================================

# Market Impact Levels
IMPACT_LOW = "LOW"
IMPACT_MEDIUM = "MEDIUM"
IMPACT_HIGH = "HIGH"
IMPACT_EXTREME = "EXTREME"

# Expected Durations
DURATION_SHORT = "SHORT"
DURATION_MEDIUM = "MEDIUM"
DURATION_LONG = "LONG"

# Confidence Sources
SOURCE_REGULATORY = "REGULATORY"

# Market Regime Hints
REGIME_NEUTRAL = "NEUTRAL"

REGIME_RISK_ON = "RISK_ON"

REGIME_RISK_OFF = "RISK_OFF"

REGIME_VOLATILE = "VOLATILE"


# ==================================================
# Corporate Event Dictionary
# ==================================================
CORPORATE_EVENT_RULES = {
    # --------------------------------------------------
    # Mergers, Acquisitions & Restructuring
    # --------------------------------------------------
    "MERGER": {
        "category": "CORPORATE",
        "sub_category": "M_AND_A",
        "event_type": "STRATEGIC_RESTRUCTURING",
        "market_impact": IMPACT_MEDIUM,
        "market_score": 1,
        "sector_score": 2,
        "stock_score": 4,
        "confidence": 90,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_MEDIUM,
        "direct_assets": ["TARGET_STOCK", "ACQUIRER_STOCK"],
        "indirect_assets": ["SECTOR_PEERS"],
        "bullish_sectors": ["CONSOLIDATING_SECTORS"],
        "bearish_sectors": [],
        "historical_winners": ["TARGET_COMPANY_STOCKS"],
        "historical_losers": ["INEFFICIENT_PEERS"],
    },
    "ACQUISITION": {
        "category": "CORPORATE",
        "sub_category": "M_AND_A",
        "event_type": "ACQUISITION",
        "market_impact": IMPACT_MEDIUM,
        "market_score": 0,
        "sector_score": 2,
        "stock_score": 5,
        "confidence": 90,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_MEDIUM,
        "direct_assets": ["ACQUIRER_STOCK", "TARGET_STOCK"],
        "indirect_assets": ["SECTOR_PEERS"],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": ["ACQUIRER", "TARGET"],
        "historical_losers": [],
    },
    "DEMERGER": {
        "category": "CORPORATE",
        "sub_category": "RESTRUCTURING",
        "event_type": "DEMERGER",
        "market_impact": IMPACT_MEDIUM,
        "market_score": 0,
        "sector_score": 1,
        "stock_score": 5,
        "confidence": 90,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_LONG,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": ["SECTOR_PEERS"],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": [],
    },
    "DIVESTMENT": {
        "category": "CORPORATE",
        "sub_category": "RESTRUCTURING",
        "event_type": "DIVESTMENT",
        "market_impact": IMPACT_MEDIUM,
        "market_score": 0,
        "sector_score": 1,
        "stock_score": 4,
        "confidence": 90,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_MEDIUM,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": [],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": [],
    },
    "DELISTING": {
        "category": "CORPORATE",
        "sub_category": "RESTRUCTURING",
        "event_type": "DELISTING",
        "market_impact": IMPACT_HIGH,
        "market_score": 0,
        "sector_score": 0,
        "stock_score": 7,
        "confidence": 98,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_LONG,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": [],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": [],
    },

    # --------------------------------------------------
    # Business Development
    # --------------------------------------------------
    "LARGE_ORDER_WIN": {
        "category": "CORPORATE",
        "sub_category": "BUSINESS_DEVELOPMENT",
        "event_type": "ORDER_WIN",
        "market_impact": IMPACT_HIGH,
        "market_score": 0,
        "sector_score": 2,
        "stock_score": 6,
        "confidence": 95,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_SHORT,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": ["SUPPLY_CHAIN"],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": ["ORDER_WINNERS"],
        "historical_losers": [],
    },
    "CAPACITY_EXPANSION": {
        "category": "CORPORATE",
        "sub_category": "BUSINESS_DEVELOPMENT",
        "event_type": "CAPACITY_EXPANSION",
        "market_impact": IMPACT_MEDIUM,
        "market_score": 0,
        "sector_score": 2,
        "stock_score": 5,
        "confidence": 90,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_LONG,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": ["SECTOR_PEERS"],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": [],
    },
    "REGULATORY_APPROVAL": {
        "category": "CORPORATE",
        "sub_category": "BUSINESS_DEVELOPMENT",
        "event_type": "REGULATORY_APPROVAL",
        "market_impact": IMPACT_HIGH,
        "market_score": 0,
        "sector_score": 1,
        "stock_score": 6,
        "confidence": 95,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_MEDIUM,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": [],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": [],
    },
    "PATENT": {
        "category": "CORPORATE",
        "sub_category": "BUSINESS_DEVELOPMENT",
        "event_type": "PATENT",
        "market_impact": IMPACT_MEDIUM,
        "market_score": 0,
        "sector_score": 1,
        "stock_score": 5,
        "confidence": 90,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_LONG,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": [],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": [],
    },
    "JOINT_VENTURE": {
        "category": "CORPORATE",
        "sub_category": "BUSINESS_DEVELOPMENT",
        "event_type": "JOINT_VENTURE",
        "market_impact": IMPACT_MEDIUM,
        "market_score": 0,
        "sector_score": 1,
        "stock_score": 5,
        "confidence": 90,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_MEDIUM,
        "direct_assets": ["PARTNER_COMPANIES"],
        "indirect_assets": ["SECTOR_PEERS"],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": [],
    },

    # --------------------------------------------------
    # Capital Actions
    # --------------------------------------------------
    "BUYBACK": {
        "category": "CORPORATE",
        "sub_category": "CAPITAL_ACTION",
        "event_type": "BUYBACK",
        "market_impact": IMPACT_MEDIUM,
        "market_score": 0,
        "sector_score": 1,
        "stock_score": 5,
        "confidence": 95,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_MEDIUM,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": [],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": ["BUYBACK_STOCKS"],
        "historical_losers": [],
    },
    "DIVIDEND": {
        "category": "CORPORATE",
        "sub_category": "CAPITAL_ACTION",
        "event_type": "DIVIDEND",
        "market_impact": IMPACT_LOW,
        "market_score": 0,
        "sector_score": 0,
        "stock_score": 2,
        "confidence": 90,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_SHORT,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": [],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": ["HIGH_DIVIDEND_STOCKS"],
        "historical_losers": [],
    },
    "BONUS": {
        "category": "CORPORATE",
        "sub_category": "CAPITAL_ACTION",
        "event_type": "BONUS",
        "market_impact": IMPACT_LOW,
        "market_score": 0,
        "sector_score": 0,
        "stock_score": 2,
        "confidence": 90,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_SHORT,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": [],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": [],
    },
    "SPLIT": {
        "category": "CORPORATE",
        "sub_category": "CAPITAL_ACTION",
        "event_type": "STOCK_SPLIT",
        "market_impact": IMPACT_LOW,
        "market_score": 0,
        "sector_score": 0,
        "stock_score": 2,
        "confidence": 90,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_SHORT,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": [],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": [],
    },

    # --------------------------------------------------
    # Capital Raising
    # --------------------------------------------------
    "QIP": {
        "category": "CORPORATE",
        "sub_category": "CAPITAL_RAISING",
        "event_type": "QIP",
        "market_impact": IMPACT_MEDIUM,
        "market_score": 0,
        "sector_score": 0,
        "stock_score": -2,
        "confidence": 90,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_SHORT,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": [],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": ["QIP_STOCKS"],
    },
    "RIGHTS_ISSUE": {
        "category": "CORPORATE",
        "sub_category": "CAPITAL_RAISING",
        "event_type": "RIGHTS_ISSUE",
        "market_impact": IMPACT_MEDIUM,
        "market_score": 0,
        "sector_score": 0,
        "stock_score": -2,
        "confidence": 90,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_SHORT,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": [],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": ["RIGHTS_ISSUE_STOCKS"],
    },
    "PREFERENTIAL_ALLOTMENT": {
        "category": "CORPORATE",
        "sub_category": "CAPITAL_RAISING",
        "event_type": "PREFERENTIAL_ALLOTMENT",
        "market_impact": IMPACT_MEDIUM,
        "market_score": 0,
        "sector_score": 0,
        "stock_score": -1,
        "confidence": 85,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_SHORT,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": [],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": [],
    },

    # --------------------------------------------------
    # Credit Rating
    # --------------------------------------------------
    "CREDIT_RATING_UPGRADE": {
        "category": "CORPORATE",
        "sub_category": "CREDIT_RATING",
        "event_type": "UPGRADE",
        "market_impact": IMPACT_MEDIUM,
        "market_score": 0,
        "sector_score": 1,
        "stock_score": 4,
        "confidence": 95,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_MEDIUM,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": ["CORPORATE_BONDS"],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": ["UPGRADED_COMPANIES"],
        "historical_losers": [],
    },
    "CREDIT_RATING_DOWNGRADE": {
        "category": "CORPORATE",
        "sub_category": "CREDIT_RATING",
        "event_type": "DOWNGRADE",
        "market_impact": IMPACT_HIGH,
        "market_score": 0,
        "sector_score": -2,
        "stock_score": -5,
        "confidence": 98,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_MEDIUM,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": ["CORPORATE_BONDS"],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": ["DOWNGRADED_COMPANIES"],
    },

    # --------------------------------------------------
    # Financial Results & Board Actions
    # --------------------------------------------------
    "BOARD_MEETING_RESULTS": {
        "category": "CORPORATE",
        "sub_category": "BOARD_MEETING",
        "event_type": "FINANCIAL_RESULTS",
        "market_impact": IMPACT_LOW,
        "market_score": 0,
        "sector_score": 0,
        "stock_score": 2,
        "confidence": 95,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_SHORT,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": ["OPTIONS"],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": [],
    },
    "STRONG_RESULTS": {
        "category": "CORPORATE",
        "sub_category": "FINANCIAL_RESULTS",
        "event_type": "RESULTS",
        "market_impact": IMPACT_HIGH,
        "market_score": 1,
        "sector_score": 3,
        "stock_score": 8,
        "confidence": 98,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_MEDIUM,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": ["SECTOR_PEERS"],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": ["EARNINGS_BEATS"],
        "historical_losers": [],
    },
    "WEAK_RESULTS": {
        "category": "CORPORATE",
        "sub_category": "FINANCIAL_RESULTS",
        "event_type": "RESULTS",
        "market_impact": IMPACT_HIGH,
        "market_score": -1,
        "sector_score": -3,
        "stock_score": -8,
        "confidence": 98,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_MEDIUM,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": ["SECTOR_PEERS"],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": ["EARNINGS_MISSES"],
    },

    # --------------------------------------------------
    # Promoter Actions
    # --------------------------------------------------
    "PROMOTER_STAKE_INCREASE": {
        "category": "CORPORATE",
        "sub_category": "PROMOTER_ACTION",
        "event_type": "STAKE_INCREASE",
        "market_impact": IMPACT_MEDIUM,
        "market_score": 0,
        "sector_score": 0,
        "stock_score": 4,
        "confidence": 95,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_MEDIUM,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": [],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": [],
    },
    "PROMOTER_STAKE_DECREASE": {
        "category": "CORPORATE",
        "sub_category": "PROMOTER_ACTION",
        "event_type": "STAKE_DECREASE",
        "market_impact": IMPACT_MEDIUM,
        "market_score": 0,
        "sector_score": 0,
        "stock_score": -4,
        "confidence": 95,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_MEDIUM,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": [],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": [],
    },

    # --------------------------------------------------
    # Legal & Regulatory Actions
    # --------------------------------------------------
    "INSOLVENCY": {
        "category": "CORPORATE",
        "sub_category": "LEGAL",
        "event_type": "INSOLVENCY",
        "market_impact": IMPACT_HIGH,
        "market_score": 0,
        "sector_score": -2,
        "stock_score": -7,
        "confidence": 98,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_LONG,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": ["LENDERS"],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": ["DISTRESSED_COMPANIES"],
    },
    "REGULATORY_INVESTIGATION": {
        "category": "CORPORATE",
        "sub_category": "LEGAL",
        "event_type": "REGULATORY_INVESTIGATION",
        "market_impact": IMPACT_HIGH,
        "market_score": 0,
        "sector_score": -1,
        "stock_score": -6,
        "confidence": 98,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_LONG,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": [],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": [],
        "historical_losers": ["INVESTIGATED_COMPANIES"],
    },
}

# ==================================================
# Master Rule Registry
# ==================================================

IMPACT_RULES = {
    **CORPORATE_EVENT_RULES,
}