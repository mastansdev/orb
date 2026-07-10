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
# Market Impact
# ==================================================
IMPACT_LOW = "LOW"
IMPACT_MEDIUM = "MEDIUM"
IMPACT_HIGH = "HIGH"
IMPACT_EXTREME = "EXTREME"

# ==================================================
# Market Regime
# ==================================================
REGIME_RISK_ON = "RISK_ON"
REGIME_RISK_OFF = "RISK_OFF"
REGIME_NEUTRAL = "NEUTRAL"
REGIME_VOLATILE = "VOLATILE"

# ==================================================
# Duration
# ==================================================
DURATION_INTRADAY = "INTRADAY"
DURATION_SHORT = "SHORT"
DURATION_MEDIUM = "MEDIUM"
DURATION_LONG = "LONG"

# ==================================================
# Confidence Source
# ==================================================
SOURCE_HISTORICAL = "HISTORICAL"
SOURCE_POLICY = "POLICY"
SOURCE_ECONOMIC = "ECONOMIC"
SOURCE_REGULATORY = "REGULATORY"
SOURCE_MARKET_STRUCTURE = "MARKET_STRUCTURE"

# ==================================================
# Rule Template
# ==================================================
RULE_TEMPLATE = {
    "category": "",
    "sub_category": "",
    "event_type": "",
    "market_impact": IMPACT_LOW,
    "market_score": 0,
    "sector_score": 0,
    "stock_score": 0,
    "confidence": 0,
    "confidence_source": SOURCE_HISTORICAL,
    "market_regime_hint": REGIME_NEUTRAL,
    "expected_duration": DURATION_INTRADAY,
    "direct_assets": [],
    "indirect_assets": [],
    "bullish_sectors": [],
    "bearish_sectors": [],
    "historical_winners": [],
    "historical_losers": [],
}

# ==================================================
# Impact Rules
# ==================================================
IMPACT_RULES = {
    # ==================================================
    # MARKET REGIME CATALYSTS
    # ==================================================
    "WAR_ESCALATION": {
        "category": "GEOPOLITICAL",
        "sub_category": "CONFLICT",
        "event_type": "MILITARY_ACTION",
        "market_impact": IMPACT_EXTREME,
        "market_score": -4,
        "sector_score": -2,
        "stock_score": 0,
        "confidence": 85,
        "confidence_source": SOURCE_HISTORICAL,
        "market_regime_hint": REGIME_VOLATILE,
        "expected_duration": DURATION_LONG,
        "direct_assets": ["CRUDE_OIL", "GOLD", "USD"],
        "indirect_assets": ["GLOBAL_EQUITIES", "EM_CURRENCIES"],
        "bullish_sectors": ["DEFENSE", "OIL_GAS", "COMMODITIES"],
        "bearish_sectors": ["AVIATION", "PAINTS", "AUTOMOBILE"],
        "historical_winners": ["BRENT_CRUDE", "XAU_USD"],
        "historical_losers": ["SPX", "NIFTY", "DAX"],
    },
    "CEASEFIRE": {
        "category": "GEOPOLITICAL",
        "sub_category": "CONFLICT",
        "event_type": "DIPLOMACY",
        "market_impact": IMPACT_HIGH,
        "market_score": 4,
        "sector_score": 2,
        "stock_score": 0,
        "confidence": 75,
        "confidence_source": SOURCE_HISTORICAL,
        "market_regime_hint": REGIME_RISK_ON,
        "expected_duration": DURATION_MEDIUM,
        "direct_assets": ["GLOBAL_EQUITIES"],
        "indirect_assets": ["CRUDE_OIL", "GOLD"],
        "bullish_sectors": ["AUTOMOBILE", "PAINTS", "AVIATION"],
        "bearish_sectors": ["DEFENSE", "OIL_GAS"],
        "historical_winners": ["SPX", "NIFTY"],
        "historical_losers": ["BRENT_CRUDE", "XAU_USD"],
    },
    "RBI_RATE_HIKE": {
        "category": "MACRO",
        "sub_category": "DOMESTIC_MONETARY_POLICY",
        "event_type": "INTEREST_RATE_DECISION",
        "market_impact": IMPACT_HIGH,
        "market_score": -2,
        "sector_score": -3,
        "stock_score": 0,
        "confidence": 80,
        "confidence_source": SOURCE_POLICY,
        "market_regime_hint": REGIME_RISK_OFF,
        "expected_duration": DURATION_MEDIUM,
        "direct_assets": ["INR", "DOMESTIC_BONDS"],
        "indirect_assets": ["DOMESTIC_EQUITIES"],
        "bullish_sectors": ["BANKING_CASA_HEAVY"],
        "bearish_sectors": ["REAL_ESTATE", "AUTOMOBILE", "HIGH_DEBT"],
        "historical_winners": ["INR_USD_STABILITY", "SHORT_TERM_YIELDS"],
        "historical_losers": ["NIFTY_REALTY", "NIFTY_AUTO"],
    },
    "RBI_RATE_CUT": {
        "category": "MACRO",
        "sub_category": "DOMESTIC_MONETARY_POLICY",
        "event_type": "INTEREST_RATE_DECISION",
        "market_impact": IMPACT_HIGH,
        "market_score": 3,
        "sector_score": 3,
        "stock_score": 0,
        "confidence": 80,
        "confidence_source": SOURCE_POLICY,
        "market_regime_hint": REGIME_RISK_ON,
        "expected_duration": DURATION_MEDIUM,
        "direct_assets": ["DOMESTIC_EQUITIES"],
        "indirect_assets": ["INR", "DOMESTIC_BONDS"],
        "bullish_sectors": ["REAL_ESTATE", "AUTOMOBILE", "NBFCs", "INFRASTRUCTURE"],
        "bearish_sectors": ["BANKING_LOW_CASA"],
        "historical_winners": ["NIFTY_REALTY", "NIFTY_AUTO", "BOND_PRICES"],
        "historical_losers": ["FIXED_INCOME_YIELDS"],
    },
    "FED_RATE_HIKE": {
        "category": "MACRO",
        "sub_category": "GLOBAL_MONETARY_POLICY",
        "event_type": "INTEREST_RATE_DECISION",
        "market_impact": IMPACT_EXTREME,
        "market_score": -3,
        "sector_score": -2,
        "stock_score": 0,
        "confidence": 90,
        "confidence_source": SOURCE_POLICY,
        "market_regime_hint": REGIME_RISK_OFF,
        "expected_duration": DURATION_LONG,
        "direct_assets": ["USD", "US_TREASURIES"],
        "indirect_assets": ["EM_EQUITIES", "EM_CURRENCIES", "GOLD"],
        "bullish_sectors": ["FINANCIALS_GLOBAL"],
        "bearish_sectors": ["IT_OUTSOURCING", "TECH", "EMERGING_MARKETS"],
        "historical_winners": ["DXY", "US_10Y_YIELD"],
        "historical_losers": ["NIFTY", "EEM", "XAU_USD"],
    },
    "FED_RATE_CUT": {
        "category": "MACRO",
        "sub_category": "GLOBAL_MONETARY_POLICY",
        "event_type": "INTEREST_RATE_DECISION",
        "market_impact": IMPACT_EXTREME,
        "market_score": 4,
        "sector_score": 3,
        "stock_score": 0,
        "confidence": 90,
        "confidence_source": SOURCE_POLICY,
        "market_regime_hint": REGIME_RISK_ON,
        "expected_duration": DURATION_LONG,
        "direct_assets": ["EM_EQUITIES", "GOLD"],
        "indirect_assets": ["USD", "US_TREASURIES"],
        "bullish_sectors": ["TECH", "GROWTH_STOCKS", "EMERGING_MARKETS"],
        "bearish_sectors": ["CASH_EQUIVALENTS"],
        "historical_winners": ["NIFTY", "XAU_USD", "EEM"],
        "historical_losers": ["DXY"],
    },
    # ==================================================
    # SECTOR ROTATION
    # ==================================================
    "PLI_SCHEME": {
        "category": "POLICY",
        "sub_category": "GOVERNMENT_INCENTIVE",
        "event_type": "REGULATORY_APPROVAL",
        "market_impact": IMPACT_MEDIUM,
        "market_score": 1,
        "sector_score": 4,
        "stock_score": 5,
        "confidence": 85,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_LONG,
        "direct_assets": ["DOMESTIC_EQUITIES"],
        "indirect_assets": [],
        "bullish_sectors": ["MANUFACTURING", "ELECTRONICS", "EV_COMPONENTS", "DEFENSE_MFG"],
        "bearish_sectors": [],
        "historical_winners": ["BENEFICIARY_BENCHMARKS"],
        "historical_losers": ["IMPORT_DEPENDENT_COMPETITORS"],
    },
    "IMPORT_DUTY": {
        "category": "POLICY",
        "sub_category": "TRADE_POLICY",
        "event_type": "TARIFF_CHANGE",
        "market_impact": IMPACT_LOW,
        "market_score": 0,
        "sector_score": 3,
        "stock_score": 4,
        "confidence": 75,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_MEDIUM,
        "direct_assets": ["TARGET_SECTOR_EQUITIES"],
        "indirect_assets": [],
        "bullish_sectors": ["DOMESTIC_PRODUCERS", "SUBSTITUTE_MANUFACTURERS"],
        "bearish_sectors": ["IMPORTERS", "CONSUMER_RETAIL_DEPENDENT"],
        "historical_winners": ["DOMESTIC_STEEL_MANUFACTURERS", "DOMESTIC_CHEMICALS"],
        "historical_losers": ["TRADERS", "END_CONSUMER_MANUFACTURERS"],
    },
    "EXPORT_DUTY": {
        "category": "POLICY",
        "sub_category": "TRADE_POLICY",
        "event_type": "TARIFF_CHANGE",
        "market_impact": IMPACT_MEDIUM,
        "market_score": -1,
        "sector_score": -4,
        "stock_score": -4,
        "confidence": 80,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_SHORT,
        "direct_assets": ["EXPORT_SECTOR_EQUITIES"],
        "indirect_assets": ["DOMESTIC_COMMODITY_PRICES"],
        "bullish_sectors": ["DOMESTIC_DOWNSTREAM_CONSUMERS"],
        "bearish_sectors": ["UPSTREAM_EXPORTERS", "COMMODITIES"],
        "historical_winners": ["DOMESTIC_INFRA_CONSUMERS_OF_STEEL"],
        "historical_losers": ["METALS_EXPORTERS", "PADDY_EXPORTERS"],
    },
    # ==================================================
    # COMPANY EVENTS
    # ==================================================
    "STRONG_RESULTS": {
        "category": "CORPORATE",
        "sub_category": "EARNINGS",
        "event_type": "FINANCIAL_REPORT",
        "market_impact": IMPACT_LOW,
        "market_score": 0,
        "sector_score": 1,
        "stock_score": 4,
        "confidence": 95,
        "confidence_source": SOURCE_ECONOMIC,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_SHORT,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": ["PEER_STOCKS"],
        "bullish_sectors": ["PARENT_SECTOR"],
        "bearish_sectors": [],
        "historical_winners": ["BEATING_EARNINGS_STOCKS"],
        "historical_losers": ["SHORT_SELLERS"],
    },
    "WEAK_RESULTS": {
        "category": "CORPORATE",
        "sub_category": "EARNINGS",
        "event_type": "FINANCIAL_REPORT",
        "market_impact": IMPACT_LOW,
        "market_score": 0,
        "sector_score": -1,
        "stock_score": -4,
        "confidence": 95,
        "confidence_source": SOURCE_ECONOMIC,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_SHORT,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": ["PEER_STOCKS"],
        "bullish_sectors": [],
        "bearish_sectors": ["PARENT_SECTOR"],
        "historical_winners": ["COMPETITOR_STOCKS"],
        "historical_losers": ["MISSING_EARNINGS_STOCKS"],
    },
    "LARGE_ORDER_WIN": {
        "category": "CORPORATE",
        "sub_category": "BUSINESS_DEVELOPMENT",
        "event_type": "CONTRACT_SIGNING",
        "market_impact": IMPACT_LOW,
        "market_score": 0,
        "sector_score": 0,
        "stock_score": 3,
        "confidence": 90,
        "confidence_source": SOURCE_REGULATORY,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_INTRADAY,
        "direct_assets": ["SPECIFIC_STOCK"],
        "indirect_assets": ["SUPPLY_CHAIN_PARTNERS"],
        "bullish_sectors": ["CAPITAL_GOODS", "INFRASTRUCTURE"],
        "bearish_sectors": [],
        "historical_winners": ["ORDER_WINNER_EQUITIES"],
        "historical_losers": [],
    },
    "MERGER": {
        "category": "CORPORATE",
        "sub_category": "M_AND_A",
        "event_type": "STRATEGIC_RESTRUCTURING",
        "market_impact": IMPACT_MEDIUM,
        "market_score": 1,
        "sector_score": 2,
        "stock_score": 4,
        "confidence": 70,
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
    # ==================================================
    # LIQUIDITY
    # ==================================================
    "FII_BUYING": {
        "category": "LIQUIDITY",
        "sub_category": "INSTITUTIONAL_FLOWS",
        "event_type": "MARKET_PARTICIPATION",
        "market_impact": IMPACT_HIGH,
        "market_score": 3,
        "sector_score": 2,
        "stock_score": 1,
        "confidence": 85,
        "confidence_source": SOURCE_MARKET_STRUCTURE,
        "market_regime_hint": REGIME_RISK_ON,
        "expected_duration": DURATION_SHORT,
        "direct_assets": ["LARGE_CAP_EQUITIES", "INDEX_FUTURES"],
        "indirect_assets": ["INR"],
        "bullish_sectors": ["FINANCIALS", "IT", "HEAVYWEIGHTS"],
        "bearish_sectors": [],
        "historical_winners": ["NIFTY_50", "SENSEX", "BSE_LARGE_CAP"],
        "historical_losers": ["INVERSE_INDEX_ETFS"],
    },
    "FII_SELLING": {
        "category": "LIQUIDITY",
        "sub_category": "INSTITUTIONAL_FLOWS",
        "event_type": "MARKET_PARTICIPATION",
        "market_impact": IMPACT_HIGH,
        "market_score": -3,
        "sector_score": -2,
        "stock_score": -1,
        "confidence": 85,
        "confidence_source": SOURCE_MARKET_STRUCTURE,
        "market_regime_hint": REGIME_RISK_OFF,
        "expected_duration": DURATION_SHORT,
        "direct_assets": ["LARGE_CAP_EQUITIES", "INDEX_FUTURES"],
        "indirect_assets": ["INR"],
        "bullish_sectors": ["DEFENSIVE_SECTORS", "PHARMA", "FMCG"],
        "bearish_sectors": ["FINANCIALS", "HIGH_VALUATION_GROWTH"],
        "historical_winners": ["USD_INR", "VIX_INDEX"],
        "historical_losers": ["NIFTY_50", "SENSEX"],
    },
    "MSCI_REBALANCE": {
        "category": "LIQUIDITY",
        "sub_category": "INDEX_FLOWS",
        "event_type": "INDEX_REBALANCING",
        "market_impact": IMPACT_MEDIUM,
        "market_score": 0,
        "sector_score": 0,
        "stock_score": 5,
        "confidence": 95,
        "confidence_source": SOURCE_MARKET_STRUCTURE,
        "market_regime_hint": REGIME_NEUTRAL,
        "expected_duration": DURATION_INTRADAY,
        "direct_assets": ["INCLUDED_STOCKS", "EXCLUDED_STOCKS"],
        "indirect_assets": [],
        "bullish_sectors": [],
        "bearish_sectors": [],
        "historical_winners": ["INFLOW_TARGET_STOCKS"],
        "historical_losers": ["OUTFLOW_TARGET_STOCKS"],
    },
}