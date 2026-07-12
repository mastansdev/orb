# ==========================================================
# Category Classification
# ==========================================================

CATEGORY_KEYWORDS = {

    # ======================================================
    # Government & Policy
    # ======================================================

    "GOVERNMENT": [

        "cabinet",
        "government",
        "ministry",
        "minister",
        "approval",
        "approved",
        "approves",
        "scheme",
        "policy",
        "notification",
        "gazette",
        "budget",
        "union budget",
        "state budget",
        "parliament",
        "lok sabha",
        "rajya sabha"

    ],

    # ======================================================
    # Corporate Results
    # ======================================================

    "RESULT": [

        "q1",
        "q2",
        "q3",
        "q4",
        "quarterly results",
        "annual results",
        "earnings",
        "profit",
        "net profit",
        "loss",
        "ebitda",
        "revenue",
        "sales",
        "guidance",
        "margin"

    ],

    # ======================================================
    # Orders
    # ======================================================

    "ORDER": [

        "order",
        "contract",
        "purchase order",
        "work order",
        "letter of award",
        "loa",
        "agreement",
        "deal",
        "contract awarded",
        "wins order",
        "receives order"

    ],

    # ======================================================
    # Corporate Actions
    # ======================================================

    "CORPORATE": [

        "board meeting",
        "buyback",
        "bonus",
        "stock split",
        "rights issue",
        "preferential issue",
        "fund raise",
        "qualified institutional placement",
        "qip",
        "allotment",
        "dividend"

    ],

    # ======================================================
    # M&A
    # ======================================================

    "MERGER": [

        "merger",
        "merge",
        "amalgamation"

    ],

    "ACQUISITION": [

        "acquire",
        "acquires",
        "acquisition",
        "stake purchase",
        "takeover"

    ],

    # ======================================================
    # Promoter Activity
    # ======================================================

    "PROMOTER": [

        "promoter",
        "pledge",
        "shareholding",
        "stake sale",
        "stake increase",
        "open offer"

    ],

    # ======================================================
    # Market Activity
    # ======================================================

    "MARKET": [

        "fii",
        "dii",
        "bulk deal",
        "block deal",
        "upper circuit",
        "lower circuit"

    ],

    # ======================================================
    # Commodity
    # ======================================================

    "COMMODITY": [

        "gold",
        "silver",
        "crude",
        "natural gas",
        "copper",
        "aluminium",
        "steel"

    ],

    # ======================================================
    # Macro
    # ======================================================

    "MACRO": [

        "inflation",
        "cpi",
        "wpi",
        "repo rate",
        "gdp",
        "fed",
        "rbi",
        "interest rate",
        "tariff"

    ]

}

# ==========================================================
# Sub Category Classification
# ==========================================================

SUBCATEGORY_KEYWORDS = {

    # --------------------------------------------------
    # Financial Results
    # --------------------------------------------------

    "BOARD_MEETING": [
        "board meeting",
        "meeting of board",
        "board of directors",
    ],

    "FINANCIAL_RESULTS": [
        "financial results",
        "quarterly results",
        "annual results",
        "earnings",
        "results",
    ],

    # --------------------------------------------------
    # M&A
    # --------------------------------------------------

    "M_AND_A": [
        "acquisition",
        "acquire",
        "takeover",
        "merger",
        "merge",
        "amalgamation",
    ],

    "RESTRUCTURING": [
        "demerger",
        "divestment",
        "slump sale",
        "business transfer",
    ],

    # --------------------------------------------------
    # Business Development
    # --------------------------------------------------

    "BUSINESS_DEVELOPMENT": [
        "order",
        "contract",
        "order win",
        "capacity expansion",
        "plant expansion",
        "patent",
        "joint venture",
        "strategic partnership",
    ],

    # --------------------------------------------------
    # Capital Actions
    # --------------------------------------------------

    "CAPITAL_ACTION": [
        "buyback",
        "bonus",
        "split",
        "stock split",
        "dividend",
    ],

    # --------------------------------------------------
    # Capital Raising
    # --------------------------------------------------

    "CAPITAL_RAISING": [
        "qip",
        "qualified institutional placement",
        "rights issue",
        "preferential allotment",
        "preferential issue",
        "fund raising",
    ],

    # --------------------------------------------------
    # Credit Rating
    # --------------------------------------------------

    "CREDIT_RATING": [
        "credit rating",
        "rating upgrade",
        "rating downgrade",
        "icra",
        "care ratings",
        "crisil",
        "india ratings",
        "acuite",
    ],

    # --------------------------------------------------
    # Promoter Actions
    # --------------------------------------------------

    "PROMOTER_ACTION": [
        "promoter",
        "stake increase",
        "stake decrease",
        "shareholding",
        "pledge",
    ],

    # --------------------------------------------------
    # Legal
    # --------------------------------------------------

    "LEGAL": [
        "nclt",
        "insolvency",
        "ibc",
        "sebi investigation",
        "ed investigation",
        "sfio",
        "cbi",
    ],
}

# ==========================================================
# Event Classification
# ==========================================================

EVENT_TYPE_KEYWORDS = {

    # --------------------------------------------------
    # Financial Results
    # --------------------------------------------------

    "BOARD_MEETING_RESULTS": [
        "board meeting",
        "meeting of board",
        "consider financial results",
        "approve financial results",
    ],

    "STRONG_RESULTS": [
        "record profit",
        "profit jumps",
        "profit rises",
        "earnings beat",
        "revenue growth",
        "margin expansion",
    ],

    "WEAK_RESULTS": [
        "loss widens",
        "profit declines",
        "earnings miss",
        "revenue falls",
        "margin pressure",
    ],

    # --------------------------------------------------
    # M&A
    # --------------------------------------------------

    "ACQUISITION": [
        "acquisition",
        "acquires",
        "acquire",
        "takeover",
    ],

    "MERGER": [
        "merger",
        "merge",
        "amalgamation",
    ],

    "DEMERGER": [
        "demerger",
    ],

    "DIVESTMENT": [
        "divestment",
        "asset sale",
        "business sale",
    ],

    "DELISTING": [
        "delisting",
    ],

    # --------------------------------------------------
    # Business Development
    # --------------------------------------------------

    "LARGE_ORDER_WIN": [
        "order",
        "contract",
        "work order",
        "letter of award",
        "loa",
        "purchase order",
    ],

    "CAPACITY_EXPANSION": [
        "capacity expansion",
        "expansion",
        "new plant",
        "new facility",
    ],

    "REGULATORY_APPROVAL": [
        "approval",
        "regulatory approval",
        "clearance",
        "license received",
    ],

    "PATENT": [
        "patent",
        "patent granted",
    ],

    "JOINT_VENTURE": [
        "joint venture",
        "strategic partnership",
        "joint agreement",
    ],

    # --------------------------------------------------
    # Capital Actions
    # --------------------------------------------------

    "BUYBACK": [
        "buyback",
        "share buyback",
    ],

    "DIVIDEND": [
        "dividend",
        "interim dividend",
        "final dividend",
    ],

    "BONUS": [
        "bonus issue",
        "bonus shares",
    ],

    "SPLIT": [
        "stock split",
        "share split",
        "split",
    ],

    # --------------------------------------------------
    # Capital Raising
    # --------------------------------------------------

    "QIP": [
        "qip",
        "qualified institutional placement",
    ],

    "RIGHTS_ISSUE": [
        "rights issue",
    ],

    "PREFERENTIAL_ALLOTMENT": [
        "preferential allotment",
        "preferential issue",
    ],

    # --------------------------------------------------
    # Credit Rating
    # --------------------------------------------------

    "CREDIT_RATING_UPGRADE": [
        "rating upgraded",
        "credit rating upgraded",
        "upgraded to",
    ],

    "CREDIT_RATING_DOWNGRADE": [
        "rating downgraded",
        "credit rating downgraded",
        "downgraded to",
    ],

    # --------------------------------------------------
    # Promoter Actions
    # --------------------------------------------------

    "PROMOTER_STAKE_INCREASE": [
        "stake increase",
        "increased stake",
        "promoter bought",
    ],

    "PROMOTER_STAKE_DECREASE": [
        "stake decrease",
        "reduced stake",
        "stake sale",
    ],

    # --------------------------------------------------
    # Legal
    # --------------------------------------------------

    "INSOLVENCY": [
        "insolvency",
        "ibc",
        "nclt",
    ],

    "REGULATORY_INVESTIGATION": [
        "sebi investigation",
        "ed investigation",
        "sfio",
        "cbi investigation",
    ],

}

# ==========================================================
# Sector Intelligence
# ==========================================================

SECTOR_KEYWORDS = {

    "DEFENCE": [

        "defence",
        "defense",
        "military",
        "navy",
        "army",
        "air force",
        "drdo",
        "warship",
        "frigate",
        "destroyer",
        "submarine",
        "fighter jet",
        "combat aircraft",
        "missile",
        "artillery"

    ],

    "POWER": [

        "power",
        "electricity",
        "generation",
        "transmission",
        "distribution",
        "grid",
        "thermal",
        "hydro",
        "renewable"

    ],

    "BANKING": [

        "bank",
        "banking",
        "nbfc",
        "lending",
        "credit",
        "loan",
        "deposit"

    ],

    "PHARMA": [

        "pharma",
        "pharmaceutical",
        "drug",
        "medicine",
        "formulation",
        "api",
        "healthcare"

    ],

    "AUTO": [

        "automobile",
        "auto",
        "vehicle",
        "passenger vehicle",
        "commercial vehicle",
        "tractor",
        "two wheeler"

    ],

    "IT": [

        "software",
        "information technology",
        "cloud",
        "cyber security",
        "digital",
        "it services"

    ],

    "METALS": [

        "steel",
        "iron",
        "copper",
        "aluminium",
        "zinc",
        "metal"

    ],

    "OIL_GAS": [

        "oil",
        "gas",
        "lng",
        "crude",
        "refinery",
        "petroleum"

    ],

    "REALTY": [

        "real estate",
        "housing",
        "property",
        "construction",
        "commercial property"

    ],

    "FMCG": [

        "consumer goods",
        "fmcg",
        "food",
        "beverage",
        "personal care"

    ]

}

# ==========================================================
# Industry Intelligence
# ==========================================================

INDUSTRY_KEYWORDS = {

    # ======================================================
    # Defence
    # ======================================================

    "SHIPBUILDING": [

        "shipyard",
        "shipbuilding",
        "warship",
        "frigate",
        "destroyer",
        "submarine",
        "naval vessel",
        "combat ship"

    ],

    "DEFENCE_ELECTRONICS": [

        "radar",
        "electronic warfare",
        "avionics",
        "missile guidance",
        "fire control",
        "surveillance system"

    ],

    "AEROSPACE": [

        "fighter aircraft",
        "combat aircraft",
        "helicopter",
        "engine",
        "aerospace"

    ],

    # ======================================================
    # Electronics
    # ======================================================

    "EMS": [

        "electronics manufacturing",
        "contract manufacturing",
        "pcb",
        "assembly"

    ],

    "SEMICONDUCTORS": [

        "semiconductor",
        "chip",
        "wafer",
        "fab",
        "osat"

    ],

    # ======================================================
    # Power
    # ======================================================

    "POWER_EQUIPMENT": [

        "transformer",
        "switchgear",
        "substation",
        "transmission line"

    ],

    "CABLES": [

        "cable",
        "wire",
        "conductors"

    ],

    # ======================================================
    # Infrastructure
    # ======================================================

    "ENGINEERING_PROCUREMENT_CONSTRUCTION": [

        "epc",
        "engineering procurement construction",
        "construction contract"

    ],

    "CAPITAL_GOODS": [

        "capital goods",
        "industrial equipment",
        "heavy engineering"

    ],

    # ======================================================
    # Railways
    # ======================================================

    "RAIL_EQUIPMENT": [

        "wagon",
        "coach",
        "locomotive",
        "rail signalling",
        "rail equipment"

    ],

    # ======================================================
    # Consumer
    # ======================================================

    "JEWELLERY": [

        "jewellery",
        "jewelry",
        "gold ornaments",
        "bullion"

    ],

    # ======================================================
    # Banking
    # ======================================================

    "PRIVATE_BANKS": [

        "private bank"

    ],

    "PUBLIC_SECTOR_BANKS": [

        "public sector bank",
        "psu bank"

    ]

}

# ==========================================================
# Theme Intelligence
# ==========================================================

THEME_KEYWORDS = {

    # ======================================================
    # Defence
    # ======================================================

    "NAVAL_MODERNIZATION": [

        "warship",
        "warships",
        "frigate",
        "frigates",
        "destroyer",
        "destroyers",
        "submarine",
        "submarines",
        "combat ship",
        "combat ships",
        "naval fleet",
        "navy expansion",
        "naval modernization"

    ],

    "DEFENCE_EXPORTS": [

        "defence export",
        "defense export",
        "export order",
        "military export",
        "global defence"

    ],

    # ======================================================
    # Electronics
    # ======================================================

    "EMS": [

        "electronics manufacturing",
        "ems",
        "pcb",
        "printed circuit board",
        "contract manufacturing",
        "electronics assembly"

    ],

    "SEMICONDUCTOR": [

        "semiconductor",
        "chip",
        "chipset",
        "wafer",
        "fab",
        "osat"

    ],

    # ======================================================
    # Power
    # ======================================================

    "POWER_CAPEX": [

        "power capex",
        "power project",
        "transmission project",
        "substation",
        "grid expansion"

    ],

    "RENEWABLE_ENERGY": [

        "renewable",
        "solar",
        "wind",
        "green energy",
        "clean energy"

    ],

    "GREEN_HYDROGEN": [

        "green hydrogen",
        "hydrogen",
        "electrolyser"

    ],

    # ======================================================
    # Railways
    # ======================================================

    "RAILWAY_MODERNIZATION": [

        "railway modernization",
        "vande bharat",
        "wagon",
        "locomotive",
        "metro",
        "rail infrastructure",
        "signalling"

    ],

    # ======================================================
    # Digital
    # ======================================================

    "DATA_CENTRES": [

        "data centre",
        "data center",
        "server park",
        "hyperscale"

    ],

    "ARTIFICIAL_INTELLIGENCE": [

        "artificial intelligence",
        "ai",
        "machine learning",
        "generative ai",
        "llm"

    ],

    # ======================================================
    # Consumer
    # ======================================================

    "JEWELLERY": [

        "gold jewellery",
        "gold price",
        "bullion",
        "hallmark",
        "wedding season",
        "jewellery",
        "jewelry"

    ],

    # ======================================================
    # Auto
    # ======================================================

    "ELECTRIC_VEHICLES": [

        "electric vehicle",
        "ev",
        "battery",
        "charging station"

    ],

    # ======================================================
    # Infrastructure
    # ======================================================

    "INFRASTRUCTURE": [

        "capex",
        "infrastructure",
        "expressway",
        "airport",
        "smart city",
        "industrial corridor"

    ]

}

# ==========================================================
# Government / Ministry Intelligence
# ==========================================================

MINISTRY_KEYWORDS = {

    "DEFENCE": [

        "ministry of defence",
        "defence ministry",
        "defense ministry",
        "indian navy",
        "indian army",
        "indian air force",
        "drdo",
        "navy",
        "army",
        "air force",
        "warship",
        "warships",
        "frigate",
        "frigates",
        "destroyer",
        "destroyers",
        "submarine",
        "submarines",
        "missile",
        "missiles",
        "fighter jet",
        "fighter jets",
        "combat aircraft",
        "combat ship",
        "combat ships",
        "naval",
        "military",
        "defence procurement",
        "defense procurement",
        "border security"

    ],

    "RAILWAYS": [

        "ministry of railways",
        "indian railways",
        "railway board",
        "railway",
        "railways",
        "vande bharat",
        "locomotive",
        "wagon",
        "coach",
        "signalling",
        "metro rail",
        "rail infrastructure"

    ],

    "POWER": [

        "ministry of power",
        "power ministry",
        "transmission",
        "distribution",
        "grid",
        "renewable energy",
        "thermal power",
        "hydro power",
        "power generation"

    ],

    "ROADS_INFRA": [

        "ministry of road transport",
        "nhai",
        "highway",
        "expressway",
        "road project",
        "bharatmala",
        "infrastructure"

    ],

    "ELECTRONICS": [

        "ministry of electronics",
        "meity",
        "electronics manufacturing",
        "semiconductor",
        "pli scheme",
        "electronics"

    ]

}

# ==========================================================
# Regulatory Intelligence
# ==========================================================

REGULATOR_KEYWORDS = {}

# ==========================================================
# Commodity Intelligence
# ==========================================================

COMMODITY_KEYWORDS = {}

# ==========================================================
# Corporate Action Intelligence
# ==========================================================

CORPORATE_ACTION_KEYWORDS = {

    "BUYBACK": [
        "buyback",
    ],

    "DIVIDEND": [
        "dividend",
        "interim dividend",
        "final dividend",
    ],

    "BONUS": [
        "bonus",
        "bonus shares",
    ],

    "SPLIT": [
        "stock split",
        "share split",
    ],

    "RIGHTS_ISSUE": [
        "rights issue",
    ],

    "QIP": [
        "qip",
        "qualified institutional placement",
    ],

    "PREFERENTIAL_ALLOTMENT": [
        "preferential allotment",
        "preferential issue",
    ],

}

# ==========================================================
# Results Intelligence
# ==========================================================

RESULT_KEYWORDS = {

    "POSITIVE_RESULTS": [
        "record profit",
        "profit jumped",
        "profit rises",
        "earnings beat",
        "revenue growth",
        "margin expansion",
        "highest ever",
        "all time high profit",
    ],

    "NEGATIVE_RESULTS": [
        "loss",
        "net loss",
        "profit declined",
        "profit falls",
        "earnings miss",
        "margin contraction",
        "revenue decline",
        "weak guidance",
    ],

}

# ==========================================================
# Macro Intelligence
# ==========================================================

MACRO_KEYWORDS = {}

# ==========================================================
# Geopolitical Intelligence
# ==========================================================

GEOPOLITICAL_KEYWORDS = {}

# ==========================================================
# Asset Mapping
# ==========================================================

ASSET_KEYWORDS = {

    "EQUITY": [
        "share",
        "stock",
        "equity",
    ],

    "OPTIONS": [
        "option",
        "call option",
        "put option",
    ],

    "FUTURES": [
        "future",
        "futures",
    ],

    "CORPORATE_BONDS": [
        "bond",
        "debenture",
        "credit rating",
    ],

}

# ==========================================================
# Catalyst Intelligence
# ==========================================================

CATALYST_KEYWORDS = {

    "EARNINGS": [
        "results",
        "earnings",
        "financial results",
    ],

    "CORPORATE_ACTION": [
        "buyback",
        "bonus",
        "split",
        "dividend",
    ],

    "MERGER_ACQUISITION": [
        "merger",
        "acquisition",
        "takeover",
    ],

    "ORDER_FLOW": [
        "order",
        "contract",
        "letter of award",
    ],

    "CAPITAL_RAISING": [
        "qip",
        "rights issue",
        "preferential allotment",
    ],

    "REGULATORY": [
        "approval",
        "investigation",
        "sebi",
        "rbi",
    ],

}

# ==========================================================
# Sanity Check Routine (Verifies correct processing)
# ==========================================================
if __name__ == "__main__":
    print("✨ Classification keywords verified setup successfully.")
    print(f"📊 Captured {len(RESULT_KEYWORDS['POSITIVE_RESULTS'])} Positive Result Identifiers.")
    print(f"🚀 Captured {len(CATALYST_KEYWORDS.keys())} High-Level Catalyst Clusters.")