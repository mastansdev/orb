"""
==========================================================
Catalyst Mapper
==========================================================

Mission
-------
Convert external market catalysts into structured market
relationships for the Brain.

Responsibilities
----------------
1. Catalyst -> Themes
2. Theme -> Industries
3. Industry -> Stocks

This file contains MARKET KNOWLEDGE only.

No trading logic.
No scoring.
No execution.

Author : H&M ORB AUTO TRADER
==========================================================
"""

# ==========================================================
# CATALYST -> THEMES
# ==========================================================

CATALYST_TO_THEMES = {

    "CRUDE_OIL": [
        "Oil & Gas",
        "Paint",
        "Tyres",
        "Airlines",
        "Chemicals"
    ],

    "NATURAL_GAS": [
        "Gas Distribution",
        "Fertilizers",
        "Power"
    ],

    "GOLD": [
        "Jewellery",
        "Gold Finance"
    ],

    "SILVER": [
        "Mining",
        "Precious Metals"
    ],

    "COPPER": [
        "Mining",
        "Electrical Equipment"
    ],

    "ALUMINIUM": [
        "Mining",
        "Metals"
    ],

    "ZINC": [
        "Mining",
        "Metals"
    ],

    "RBI_RATE_CUT": [
        "Banking",
        "NBFC",
        "Real Estate",
        "Auto"
    ],

    "RBI_RATE_HIKE": [
        "Banking",
        "NBFC"
    ],

    "DEFENCE_ORDER": [
        "Defence"
    ],

    "RAILWAY_ORDER": [
        "Railways"
    ],

    "POWER_REFORMS": [
        "Power"
    ],

    "SOLAR_POLICY": [
        "Renewable Energy"
    ]
}


# ==========================================================
# THEME -> INDUSTRIES
# ==========================================================

THEME_TO_INDUSTRIES = {

    "Oil & Gas": [
        "Exploration",
        "Refining",
        "Oil Marketing"
    ],

    "Mining": [
        "Mining"
    ],

    "Power": [
        "Power Generation",
        "Power Equipment"
    ],

    "Defence": [
        "Defence Equipment"
    ],

    "Railways": [
        "Railway Equipment"
    ],

    "Banking": [
        "Private Bank",
        "PSU Bank"
    ],

    "NBFC": [
        "NBFC"
    ],

    "Paint": [
        "Paint"
    ],

    "Tyres": [
        "Tyres"
    ],

    "Airlines": [
        "Airlines"
    ],

    "Jewellery": [
        "Jewellery"
    ],

    "Renewable Energy": [
        "Solar",
        "Wind"
    ]
}


# ==========================================================
# INDUSTRY -> STOCKS
# ==========================================================

INDUSTRY_TO_STOCKS = {

    "Exploration": [
        "ONGC",
        "OIL"
    ],

    "Oil Marketing": [
        "IOC",
        "BPCL",
        "HPCL"
    ],

    "Mining": [
        "HINDZINC",
        "NATIONALUM",
        "HINDCOPPER",
        "NMDC",
        "MOIL"
    ],

    "Paint": [
        "ASIANPAINT",
        "BERGER",
        "KANSAINER",
        "INDIGOPNTS"
    ],

    "Tyres": [
        "MRF",
        "APOLLOTYRE",
        "BALKRISIND",
        "CEATLTD",
        "JKTYRE"
    ],

    "Airlines": [
        "INDIGO"
    ],

    "Private Bank": [
        "HDFCBANK",
        "ICICIBANK",
        "AXISBANK",
        "KOTAKBANK"
    ],

    "PSU Bank": [
        "SBI",
        "BANKBARODA",
        "PNB",
        "CANBK"
    ]
}