"""
==========================================================
Sector Sensitivity Taxonomy
==========================================================

Mission
-------
Which macro factors (commodities, currencies, government
policy) actually move each sector, in WHICH direction, and
why. This is domain knowledge -- the same kind of thing as
news/news_taxonomy.py's SECTOR_KEYWORDS or MINISTRY_KEYWORDS
-- a curated relationships table, not a live data feed. It
does not go stale the way a price or a headline does;
sector-to-commodity exposure is a structural fact about how
these businesses work.

What this is NOT: a source of live commodity/currency prices.
The bot doesn't currently subscribe to MCX/currency instruments
on the Dhan feed (equities only, 750 symbols) -- confirmed
2026-07-21, no price_engine coverage for crude/gold/USDINR etc.
Adding that is a separate, larger integration (new instrument
subscriptions) and is NOT part of this file.

What this DOES enable now, without that live feed: the bot
already collects MACRO and COMMODITY category news (see
news/news_taxonomy.py). When a macro/commodity story breaks
("crude oil surges", "dollar strengthens against rupee"), this
taxonomy lets the bot know WHICH of the 750 stocks that story
actually matters for, and whether it's a tailwind or a
headwind for them -- see CompanyIntelligence.sensitivity_
evidence() and trade_selection_engine.py's wiring.

Direction semantics (2026-07-21 -- added after finding the
list-only v1 couldn't answer "is dollar strength good or bad
for TCS")
----------------------------------------------------------
Commodities: "cost" (rising price is a HEADWIND -- it's an
input) or "revenue" (rising price is a TAILWIND -- it's what
the company sells/realizes).

Currencies: "exporter" (rupee depreciation / dollar strength
is a TAILWIND -- majority foreign-currency revenue against
INR costs) or "importer" (rupee depreciation is a HEADWIND --
costs are foreign-currency, revenue is domestic).

Sectors where the direction genuinely varies WITHIN the
sector (Oil & Gas: upstream explorers vs downstream refiners
react oppositely to crude) are handled in
INDUSTRY_SENSITIVITY_OVERRIDE below at the finer industry
grain, rather than forcing one wrong blanket direction on the
whole sector.

Author : H&M ORB AUTO TRADER
==========================================================
"""

# Keys match the real SECTOR column values in
# Masterdata/master_database.xlsx exactly (confirmed
# 2026-07-21) -- not the coarser SECTOR_KEYWORDS categories
# used for news classification, which are a different,
# simplified taxonomy for a different purpose.

SECTOR_SENSITIVITY = {

    "OIL & GAS": {
        # Deliberately empty at sector level -- see
        # INDUSTRY_SENSITIVITY_OVERRIDE below. Upstream
        # explorers and downstream refiners react OPPOSITELY
        # to crude price; a single sector-wide direction
        # would be wrong for half the sector.
        "commodities": {},
        "currencies": {"usd/inr": "importer", "dollar": "importer", "rupee": "importer"},
        "government": "fuel pricing policy, subsidies, export duties on fuel",
        "notes": (
            "Direction depends on upstream vs downstream -- see "
            "industry-level override. Rupee weakness raises "
            "import cost for the sector as a whole (India is a "
            "large net crude importer)."
        ),
    },

    "METALS & MINING": {
        "commodities": {
            "steel": "revenue", "iron ore": "revenue",
            "aluminium": "revenue", "copper": "revenue",
            "zinc": "revenue", "coal": "cost",
            "gold": "revenue", "silver": "revenue",
        },
        "currencies": {"usd/inr": "exporter", "dollar": "exporter"},
        "government": "export duties, mining lease policy, China trade action",
        "notes": (
            "Global metal prices (largely dollar-denominated) set "
            "realizations directly -- rising prices are a tailwind "
            "for producers. Coal is the exception where it's an "
            "input (e.g. for steel/aluminium smelting). China "
            "demand/supply is a major swing factor for base metals."
        ),
    },

    "POWER & UTILITIES": {
        "commodities": {"coal": "cost", "natural gas": "cost", "crude oil": "cost"},
        "currencies": {},
        "government": "tariff policy, PLF norms, renewable purchase obligations",
        "notes": (
            "Fuel cost (coal/gas) is a major input for thermal "
            "generators; tariffs are regulator-set, not market-set, "
            "so pass-through is often lagged/incomplete."
        ),
    },

    "BANKING": {
        "commodities": {},
        "currencies": {"usd/inr": "importer"},
        "government": "RBI repo rate, CRR/SLR, priority sector lending norms",
        "notes": (
            "Net interest margins move directly with RBI policy "
            "rate decisions -- not a commodity/currency play in "
            "the classic sense. Asset quality is macro-cycle "
            "sensitive."
        ),
    },

    "FINANCIAL SERVICES": {
        "commodities": {},
        "currencies": {"usd/inr": "importer"},
        "government": "RBI/SEBI regulation, repo rate",
        "notes": (
            "NBFCs are rate-sensitive on both borrowing cost and "
            "loan demand; capital markets businesses track index levels."
        ),
    },

    "INSURANCE": {
        "commodities": {},
        "currencies": {},
        "government": "IRDAI regulation, tax treatment of premiums",
        "notes": "Bond yields (rate-linked) affect investment income.",
    },

    "INFORMATION TECHNOLOGY": {
        "commodities": {},
        "currencies": {
            "usd/inr": "exporter", "dollar": "exporter",
            "euro": "exporter", "gbp": "exporter",
        },
        "government": "H-1B/visa policy (US), data protection regulation",
        "notes": (
            "Revenue is majority USD/EUR/GBP-billed against INR "
            "costs -- rupee depreciation (dollar strength) directly "
            "helps margins. US client budget cycles matter more "
            "than Indian domestic macro."
        ),
    },

    "TELECOM": {
        "commodities": {},
        "currencies": {},
        "government": "spectrum policy, AGR dues, tariff regulation",
        "notes": "Regulatory/spectrum decisions are the dominant driver.",
    },

    "AUTOMOBILE": {
        "commodities": {
            "steel": "cost", "aluminium": "cost",
            "copper": "cost", "crude oil": "cost", "rubber": "cost",
        },
        "currencies": {"usd/inr": "importer", "yen": "importer"},
        "government": "emission norms (BS-VI etc.), EV subsidy (FAME), import duty",
        "notes": (
            "Steel/aluminium/rubber are direct input costs; fuel "
            "prices also affect end-demand for the vehicles "
            "themselves (double exposure to crude)."
        ),
    },

    "CONSUMER DURABLES": {
        "commodities": {"copper": "cost", "aluminium": "cost", "steel": "cost", "crude oil": "cost"},
        "currencies": {"usd/inr": "importer", "yuan": "importer"},
        "government": "import duty on components, PLI scheme",
        "notes": "Component imports (often from China) are cost-sensitive to rupee/yuan.",
    },

    "CONSUMER DISCRETIONARY": {
        "commodities": {},
        "currencies": {},
        "government": "GST rate changes on discretionary goods",
        "notes": "Demand-cycle and disposable-income sensitive rather than input-cost sensitive.",
    },

    "FMCG": {
        "commodities": {
            "crude oil": "cost", "palm oil": "cost",
            "sugar": "cost", "wheat": "cost", "milk": "cost",
        },
        "currencies": {},
        "government": "GST rates, rural spending schemes (MGNREGA etc.)",
        "notes": (
            "Palm oil/crude (packaging) are real input costs; rural "
            "demand tracks monsoon and government rural spending "
            "more than any single commodity."
        ),
    },

    "PHARMACEUTICALS": {
        "commodities": {},
        "currencies": {"usd/inr": "exporter"},
        "government": "USFDA inspection outcomes, drug price control (NPPA), patent rulings",
        "notes": (
            "US-generic exporters are USD-revenue, INR-cost -- "
            "similar dynamic to IT. USFDA plant inspection results "
            "are single-stock, high-impact events, not macro."
        ),
    },

    "HEALTHCARE SERVICES": {
        "commodities": {},
        "currencies": {},
        "government": "healthcare/insurance policy (Ayushman Bharat etc.)",
        "notes": "Domestic demand and insurance-penetration driven.",
    },

    "CHEMICALS": {
        "commodities": {"crude oil": "cost", "natural gas": "cost"},
        "currencies": {"usd/inr": "exporter", "yuan": "importer"},
        "government": "anti-dumping duty (esp. vs China), environmental clearance",
        "notes": (
            "Crude/gas are feedstock (cost side). Many specialty "
            "chemical names are also export-revenue (dollar "
            "tailwind) while competing against Chinese imports "
            "(yuan-linked headwind) -- both currency exposures "
            "can be live at once for the same stock."
        ),
    },

    "CEMENT & BUILDING MATERIALS": {
        "commodities": {"coal": "cost", "petcoke": "cost", "crude oil": "cost"},
        "currencies": {},
        "government": "infrastructure spending, housing policy",
        "notes": "Fuel cost is the main input; demand tracks government infra capex.",
    },

    "CAPITAL GOODS": {
        "commodities": {"steel": "cost", "copper": "cost", "aluminium": "cost"},
        "currencies": {},
        "government": "infrastructure/defence capex, PLI scheme, order inflow from PSUs",
        "notes": "Order-book driven; government capex cycle is the dominant demand driver.",
    },

    "INFRASTRUCTURE": {
        "commodities": {"steel": "cost", "cement": "cost", "crude oil": "cost"},
        "currencies": {},
        "government": "budget allocation (roads/rail/ports), land acquisition policy",
        "notes": "Directly tracks government infrastructure spending announcements.",
    },

    "REAL ESTATE": {
        "commodities": {"steel": "cost", "cement": "cost"},
        "currencies": {},
        "government": "home loan rates (RBI), stamp duty, RERA",
        "notes": "Rate-sensitive on buyer affordability; input-cost sensitive on construction.",
    },

    "LOGISTICS & TRANSPORTATION": {
        "commodities": {"crude oil": "cost", "diesel": "cost"},
        "currencies": {},
        "government": "fuel pricing, GST e-way bill policy",
        "notes": "Fuel is the largest variable operating cost.",
    },

    "AGRICULTURE & FERTILIZERS": {
        "commodities": {"natural gas": "cost", "urea": "cost", "phosphate": "cost", "potash": "cost"},
        "currencies": {"usd/inr": "importer"},
        "government": "fertilizer subsidy, MSP (minimum support price)",
        "notes": "Subsidy policy and monsoon are the dominant drivers, more than open-market pricing.",
    },

    "TEXTILES & APPAREL": {
        "commodities": {"cotton": "cost", "crude oil": "cost"},
        "currencies": {"usd/inr": "exporter"},
        "government": "export incentive schemes (RoDTEP etc.), cotton MSP",
        "notes": "Cotton price is direct input cost; export-oriented names are USD-revenue.",
    },

    "PAPER & PACKAGING": {
        "commodities": {"pulp": "cost", "crude oil": "cost"},
        "currencies": {},
        "government": "environmental/forestry regulation",
        "notes": "Pulp/energy are the main input costs.",
    },

    "MEDIA & ENTERTAINMENT": {
        "commodities": {},
        "currencies": {},
        "government": "content/broadcast regulation, ad-spend cyclicality",
        "notes": "Ad-spend cycle tracks broader economic sentiment rather than a commodity.",
    },

    "INTERNET & DIGITAL PLATFORMS": {
        "commodities": {},
        "currencies": {},
        "government": "data protection regulation, e-commerce FDI policy",
        "notes": "Regulatory and funding-cycle sensitive rather than commodity sensitive.",
    },

    "BUSINESS SERVICES": {
        "commodities": {},
        "currencies": {"usd/inr": "exporter"},
        "government": "labour policy",
        "notes": "Export-oriented services (BPO/staffing) carry similar USD-revenue dynamics to IT, smaller scale.",
    },

    "HOSPITALITY & TOURISM": {
        "commodities": {"crude oil": "cost"},
        "currencies": {"usd/inr": "exporter"},
        "government": "tourism policy, visa rules",
        "notes": "Fuel affects travel cost; INR weakness can help inbound tourism (cheaper for foreign visitors).",
    },

    "DIVERSIFIED": {
        "commodities": {},
        "currencies": {},
        "government": "",
        "notes": (
            "Conglomerate -- sensitivity depends on which "
            "subsidiary/segment is driving the story at a given "
            "time, not a single sector factor. Deliberately left "
            "empty rather than guessed."
        ),
    },

}

# ==========================================================
# Industry-level overrides
# ==========================================================
# For the handful of sectors where direction genuinely splits
# WITHIN the sector. Checked first; sector-level is the
# fallback. Confirmed real industry names from
# Masterdata/master_database.xlsx (2026-07-21).

INDUSTRY_SENSITIVITY_OVERRIDE = {

    "OIL & GAS EXPLORATION": {
        # Upstream (e.g. ONGC, OIL): higher crude = better
        # realizations on what they pump out of the ground.
        "commodities": {"crude": "revenue", "crude oil": "revenue", "natural gas": "revenue"},
        "currencies": {},
        "government": "fuel pricing policy, exploration licensing (OALP/HELP)",
        "notes": "Upstream explorer -- rising crude/gas price is a tailwind (realization), not a cost.",
    },

    "OIL REFINING": {
        # Downstream (e.g. OMCs): higher crude raises the
        # feedstock cost; retail fuel price pass-through is
        # often lagged/regulated, squeezing margins short-term.
        "commodities": {"crude": "cost", "crude oil": "cost", "brent": "cost"},
        "currencies": {"usd/inr": "importer"},
        "government": "retail fuel pricing policy (pass-through lag), subsidy sharing",
        "notes": "Downstream refiner/OMC -- rising crude is a headwind (input cost, margin squeeze) unless retail prices are raised in step.",
    },

    "GAS DISTRIBUTION / LNG": {
        "commodities": {"natural gas": "cost", "lng": "cost"},
        "currencies": {"usd/inr": "importer"},
        "government": "city gas distribution licensing, gas pricing policy (APM)",
        "notes": "Buys gas as input, sells to retail/industrial/CNG customers -- rising gas cost is a margin headwind unless passed through.",
    },

}


def get_sensitivity(sector, industry=""):
    """
    Returns the sensitivity profile for a stock, preferring
    an industry-level override (where direction genuinely
    differs within the sector) and falling back to the
    sector-level entry. Returns an empty shell for anything
    unmapped -- never guesses.
    """
    industry_key = str(industry).strip().upper()
    if industry_key in INDUSTRY_SENSITIVITY_OVERRIDE:
        return INDUSTRY_SENSITIVITY_OVERRIDE[industry_key]

    return SECTOR_SENSITIVITY.get(
        str(sector).strip().upper(),
        {"commodities": {}, "currencies": {}, "government": "", "notes": ""},
    )
