"""
==========================================================
Causal Knowledge Base
==========================================================

Mission
-------
The permanent institutional memory of HOW events
propagate through the economy to listed companies.

This is NOT a list of news rules. Each model encodes a
complete causal chain:

    root cause → 1st order → 2nd order → 3rd order

with signs, strengths, horizons, and what institutions
monitor — so the Brain never reasons from scratch.

Model format
------------
key        : unique id
category   : taxonomy family
triggers   : lowercase substrings matched against the
             event's combined text (type + catalyst +
             headline + sector/theme)
root_cause : the economic mechanism (explanation)
horizon    : INTRADAY / SHORT / MEDIUM / LONG
base_confidence : how reliable this chain has been
effects    : list of dicts:
             {order: 1|2|3,
              target: UPPERCASE substring matched vs
                      sector / industry / theme names,
              sign: +1 / -1,
              strength: 0-100 (1st order raw; engine
              damps 2nd=×0.5, 3rd=×0.25)}
monitor    : what institutional investors watch
leading    : leading indicators
note       : historical behaviour / examples

Extend freely — every model added compounds the
Brain's reasoning permanently.

Author : H&M ORB AUTO TRADER
==========================================================
"""

CAUSAL_MODELS = [

    # ======================================================
    # MONETARY POLICY — RBI
    # ======================================================
    {
        "key": "RBI_RATE_CUT",
        "category": "MONETARY",
        "triggers": ["repo rate cut", "rbi cuts", "rate cut",
                     "policy rate reduced", "repo reduced"],
        "root_cause": (
            "Cheaper money: borrowing costs fall, credit "
            "demand rises, discount rates fall (valuations "
            "expand), rate-sensitive demand revives."
        ),
        "horizon": "MEDIUM",
        "base_confidence": 75,
        "effects": [
            {"order": 1, "target": "BANK", "sign": 1, "strength": 70},
            {"order": 1, "target": "NBFC", "sign": 1, "strength": 80},
            {"order": 1, "target": "HOUSING FINANCE", "sign": 1, "strength": 80},
            {"order": 1, "target": "REALTY", "sign": 1, "strength": 75},
            {"order": 1, "target": "AUTO", "sign": 1, "strength": 65},
            {"order": 2, "target": "CEMENT", "sign": 1, "strength": 60},
            {"order": 2, "target": "CONSUMER DURABLE", "sign": 1, "strength": 55},
            {"order": 2, "target": "INFRA", "sign": 1, "strength": 55},
            {"order": 2, "target": "CAPITAL GOODS", "sign": 1, "strength": 50},
            {"order": 3, "target": "PAINT", "sign": 1, "strength": 40},
            {"order": 3, "target": "TILE", "sign": 1, "strength": 40},
        ],
        "monitor": "Transmission speed (MCLR cuts), credit growth, bond yields, banks' NIM guidance",
        "leading": "OIS curve pricing, inflation prints below target, RBI stance change to accommodative",
        "note": (
            "NBFC/HFC/realty react hardest (funding-cost beta). "
            "Banks mixed: NIM compresses short-term, credit growth wins long-term. "
            "If cut was fully priced by OIS, expect sell-the-news fade in 1-3 days."
        ),
    },
    {
        "key": "RBI_RATE_HIKE",
        "category": "MONETARY",
        "triggers": ["repo rate hike", "rbi hikes", "rate hike",
                     "policy rate raised", "repo increased"],
        "root_cause": (
            "Costlier money: EMIs rise, credit demand slows, "
            "discount rates rise (valuations compress), "
            "leveraged businesses squeezed."
        ),
        "horizon": "MEDIUM",
        "base_confidence": 75,
        "effects": [
            {"order": 1, "target": "NBFC", "sign": -1, "strength": 80},
            {"order": 1, "target": "REALTY", "sign": -1, "strength": 75},
            {"order": 1, "target": "AUTO", "sign": -1, "strength": 60},
            {"order": 1, "target": "HOUSING FINANCE", "sign": -1, "strength": 75},
            {"order": 1, "target": "BANK", "sign": 1, "strength": 40},
            {"order": 2, "target": "CEMENT", "sign": -1, "strength": 50},
            {"order": 2, "target": "CONSUMER DURABLE", "sign": -1, "strength": 50},
            {"order": 2, "target": "INFRA", "sign": -1, "strength": 45},
            {"order": 3, "target": "HIGH DEBT", "sign": -1, "strength": 50},
        ],
        "monitor": "Deposit repricing vs lending repricing, real-estate registrations, auto financing share",
        "leading": "Inflation surprises above tolerance band, hawkish MPC minutes, US yields",
        "note": (
            "Banks initially gain NIM (assets reprice faster), lose later if credit slows. "
            "Highly leveraged names (infra, some realty) underperform for the whole cycle."
        ),
    },
    {
        "key": "RBI_LIQUIDITY_EASING",
        "category": "MONETARY",
        "triggers": ["crr cut", "slr cut", "omo purchase",
                     "liquidity infusion", "ltro", "variable rate repo"],
        "root_cause": (
            "System liquidity rises: short rates soften, "
            "bond yields fall, credit availability improves."
        ),
        "horizon": "SHORT",
        "base_confidence": 65,
        "effects": [
            {"order": 1, "target": "BANK", "sign": 1, "strength": 60},
            {"order": 1, "target": "NBFC", "sign": 1, "strength": 65},
            {"order": 2, "target": "REALTY", "sign": 1, "strength": 45},
            {"order": 2, "target": "SMALL CAP", "sign": 1, "strength": 40},
        ],
        "monitor": "Overnight rates vs repo corridor, banking system liquidity surplus/deficit",
        "leading": "Advance tax outflow calendar, government spending pace",
        "note": "Gentler than rate action; mostly supports financials and risk appetite broadly.",
    },
    {
        "key": "RBI_INR_DEFENSE",
        "category": "MONETARY",
        "triggers": ["rbi intervention", "forex intervention",
                     "defends rupee", "dollar sales rbi"],
        "root_cause": (
            "RBI sells dollars to slow INR fall — drains "
            "rupee liquidity, signals stress but caps panic."
        ),
        "horizon": "SHORT",
        "base_confidence": 55,
        "effects": [
            {"order": 1, "target": "IT", "sign": -1, "strength": 40},
            {"order": 1, "target": "BANK", "sign": 1, "strength": 30},
            {"order": 2, "target": "IMPORT", "sign": 1, "strength": 35},
        ],
        "monitor": "Forex reserves weekly change, forward premia, NDF spreads",
        "leading": "FII outflow streaks, crude spikes, DXY strength",
        "note": "Signal value > direct effect: persistent intervention = macro stress regime.",
    },

    # ======================================================
    # US FEDERAL RESERVE
    # ======================================================
    {
        "key": "FED_HIKE_HAWKISH",
        "category": "FED",
        "triggers": ["fed hike", "fomc raises", "hawkish fed",
                     "fed raises rates", "quantitative tightening", "qt "],
        "root_cause": (
            "Dollar tightening: US yields rise → dollar "
            "strengthens → FII money leaves EM → INR weakens "
            "→ Indian valuations compress."
        ),
        "horizon": "MEDIUM",
        "base_confidence": 70,
        "effects": [
            {"order": 1, "target": "BANK", "sign": -1, "strength": 50},
            {"order": 1, "target": "SMALL CAP", "sign": -1, "strength": 55},
            {"order": 1, "target": "IT", "sign": 1, "strength": 40},
            {"order": 1, "target": "PHARMA", "sign": 1, "strength": 35},
            {"order": 2, "target": "REALTY", "sign": -1, "strength": 40},
            {"order": 2, "target": "GOLD", "sign": -1, "strength": 35},
            {"order": 3, "target": "IMPORT", "sign": -1, "strength": 35},
        ],
        "monitor": "FII flow data (daily), DXY, US 10Y, USDINR, India VIX",
        "leading": "US CPI prints, dot plot shifts, US labor data",
        "note": (
            "FII-heavy large caps and high-multiple names derate first. "
            "Exporters (IT/pharma) cushioned by INR depreciation. "
            "Historically 1-3 day gap-down, then dependent on guidance tone."
        ),
    },
    {
        "key": "FED_CUT_DOVISH",
        "category": "FED",
        "triggers": ["fed cut", "fomc cuts", "dovish fed",
                     "fed pivot", "quantitative easing", "qe "],
        "root_cause": (
            "Dollar easing: US yields fall → dollar weakens → "
            "risk-on flows into EM → FII buying → INR firms."
        ),
        "horizon": "MEDIUM",
        "base_confidence": 70,
        "effects": [
            {"order": 1, "target": "BANK", "sign": 1, "strength": 55},
            {"order": 1, "target": "SMALL CAP", "sign": 1, "strength": 55},
            {"order": 1, "target": "GOLD", "sign": 1, "strength": 45},
            {"order": 1, "target": "IT", "sign": -1, "strength": 30},
            {"order": 2, "target": "REALTY", "sign": 1, "strength": 40},
            {"order": 2, "target": "METAL", "sign": 1, "strength": 40},
        ],
        "monitor": "FII flows, EM fund allocations, USDINR trend",
        "leading": "US recession signals, unemployment upticks, Fed speaker tone",
        "note": "Broad risk-on for EM equities; IT loses its currency cushion.",
    },

    # ======================================================
    # COMMODITY CYCLES
    # ======================================================
    {
        "key": "CRUDE_SPIKE",
        "category": "COMMODITY",
        "triggers": ["crude spike", "oil surge", "crude above",
                     "oil above", "brent rall", "opec cut",
                     "oil supply disruption"],
        "root_cause": (
            "India imports ~85% of crude: input costs rise "
            "across the economy, CAD widens, INR pressured, "
            "inflation risk pushes rates higher."
        ),
        "horizon": "SHORT",
        "base_confidence": 80,
        "effects": [
            {"order": 1, "target": "OIL", "sign": 1, "strength": 70},
            {"order": 1, "target": "AVIATION", "sign": -1, "strength": 80},
            {"order": 1, "target": "PAINT", "sign": -1, "strength": 70},
            {"order": 1, "target": "OMC", "sign": -1, "strength": 65},
            {"order": 1, "target": "TYRE", "sign": -1, "strength": 60},
            {"order": 2, "target": "CHEMICAL", "sign": -1, "strength": 50},
            {"order": 2, "target": "ADHESIVE", "sign": -1, "strength": 50},
            {"order": 2, "target": "FMCG", "sign": -1, "strength": 40},
            {"order": 2, "target": "CEMENT", "sign": -1, "strength": 40},
            {"order": 3, "target": "NBFC", "sign": -1, "strength": 30},
            {"order": 3, "target": "GAS", "sign": 1, "strength": 35},
        ],
        "monitor": "Brent level vs OMC marketing margins, ATF price resets, gross refining margins",
        "leading": "OPEC meetings, US inventories (EIA), geopolitical supply threats",
        "note": (
            "Paints/aviation/tyres = crude-derivative COGS; upstream (ONGC/Oil India) "
            "gains directly. OMCs lose on marketing freeze, gain on GRM. Persistent "
            ">$95 historically triggers macro derating of whole market."
        ),
    },
    {
        "key": "CRUDE_CRASH",
        "category": "COMMODITY",
        "triggers": ["crude crash", "oil fall", "crude below",
                     "oil slump", "brent drop", "opec raises output"],
        "root_cause": (
            "Import bill shrinks: margin tailwind for crude "
            "consumers, CAD improves, inflation cools."
        ),
        "horizon": "SHORT",
        "base_confidence": 80,
        "effects": [
            {"order": 1, "target": "AVIATION", "sign": 1, "strength": 80},
            {"order": 1, "target": "PAINT", "sign": 1, "strength": 70},
            {"order": 1, "target": "OMC", "sign": 1, "strength": 65},
            {"order": 1, "target": "TYRE", "sign": 1, "strength": 60},
            {"order": 1, "target": "OIL", "sign": -1, "strength": 60},
            {"order": 2, "target": "FMCG", "sign": 1, "strength": 40},
            {"order": 2, "target": "CHEMICAL", "sign": 1, "strength": 45},
            {"order": 2, "target": "LOGISTICS", "sign": 1, "strength": 40},
        ],
        "monitor": "Whether price fall is demand-led (bad globally) or supply-led (good for India)",
        "leading": "OPEC quota politics, global growth downgrades",
        "note": "Demand-led crashes drag everything; supply-led crashes are a clean India positive.",
    },
    {
        "key": "STEEL_RALLY",
        "category": "COMMODITY",
        "triggers": ["steel price rise", "steel rally", "hrc price",
                     "china steel stimulus", "steel demand surge"],
        "root_cause": (
            "Steel realizations rise (usually China stimulus "
            "or supply cuts): producer margins expand, "
            "consumer margins squeeze."
        ),
        "horizon": "MEDIUM",
        "base_confidence": 65,
        "effects": [
            {"order": 1, "target": "STEEL", "sign": 1, "strength": 75},
            {"order": 1, "target": "IRON ORE", "sign": 1, "strength": 65},
            {"order": 1, "target": "AUTO", "sign": -1, "strength": 45},
            {"order": 1, "target": "CONSUMER DURABLE", "sign": -1, "strength": 45},
            {"order": 2, "target": "CAPITAL GOODS", "sign": -1, "strength": 40},
            {"order": 2, "target": "REALTY", "sign": -1, "strength": 30},
            {"order": 2, "target": "PIPE", "sign": -1, "strength": 40},
        ],
        "monitor": "China property data, HRC spreads over coking coal, anti-dumping filings",
        "leading": "Chinese PMI, iron ore port inventories, Beijing stimulus announcements",
        "note": "Indian metal stocks are a leveraged China trade; moves front-run domestic fundamentals.",
    },
    {
        "key": "METALS_RALLY_BASE",
        "category": "COMMODITY",
        "triggers": ["copper rall", "aluminium ris", "zinc ris",
                     "nickel ris", "lme rall", "base metals surge"],
        "root_cause": (
            "Global growth / supply squeeze lifts LME complex; "
            "Indian producers get realization windfall."
        ),
        "horizon": "MEDIUM",
        "base_confidence": 60,
        "effects": [
            {"order": 1, "target": "METAL", "sign": 1, "strength": 70},
            {"order": 1, "target": "MINING", "sign": 1, "strength": 60},
            {"order": 2, "target": "CABLE", "sign": -1, "strength": 45},
            {"order": 2, "target": "CONSUMER DURABLE", "sign": -1, "strength": 40},
            {"order": 2, "target": "EV", "sign": -1, "strength": 30},
        ],
        "monitor": "LME inventories, dollar index (inverse), China credit impulse",
        "leading": "Global PMIs, China property starts, energy costs of smelters",
        "note": "Cables/wires and durables carry copper/aluminium COGS — margin squeeze with a 1-2 quarter lag.",
    },
    {
        "key": "GOLD_RALLY",
        "category": "COMMODITY",
        "triggers": ["gold surge", "gold rall", "gold record",
                     "gold all-time"],
        "root_cause": (
            "Fear/liquidity trade: real yields falling or "
            "geopolitical stress. India: jewellery demand "
            "shifts, gold-loan collateral values rise."
        ),
        "horizon": "MEDIUM",
        "base_confidence": 60,
        "effects": [
            {"order": 1, "target": "GOLD FINANCE", "sign": 1, "strength": 65},
            {"order": 1, "target": "JEWELLERY", "sign": -1, "strength": 40},
            {"order": 2, "target": "NBFC", "sign": 1, "strength": 25},
        ],
        "monitor": "Gold-loan LTV headroom, jewellery volume vs value growth",
        "leading": "US real yields, central bank buying, ETF flows",
        "note": "Gold-loan NBFCs (collateral appreciation) are the cleanest Indian expression.",
    },
    {
        "key": "COAL_GAS_SPIKE",
        "category": "COMMODITY",
        "triggers": ["coal price surge", "coal shortage", "gas price spike",
                     "lng price", "power fuel cost"],
        "root_cause": (
            "Power/energy input costs jump: generators with "
            "fuel pass-through survive, merchant power gains, "
            "energy-intensive industries squeeze."
        ),
        "horizon": "SHORT",
        "base_confidence": 60,
        "effects": [
            {"order": 1, "target": "POWER", "sign": 1, "strength": 45},
            {"order": 1, "target": "COAL", "sign": 1, "strength": 60},
            {"order": 1, "target": "CERAMIC", "sign": -1, "strength": 55},
            {"order": 1, "target": "GLASS", "sign": -1, "strength": 50},
            {"order": 2, "target": "CEMENT", "sign": -1, "strength": 45},
            {"order": 2, "target": "ALUMINIUM", "sign": -1, "strength": 40},
            {"order": 2, "target": "CITY GAS", "sign": -1, "strength": 45},
            {"order": 2, "target": "FERTILIZER", "sign": -1, "strength": 40},
        ],
        "monitor": "Merchant power rates (IEX), e-auction coal premiums, spot LNG",
        "leading": "Monsoon hydro output, heat-wave demand forecasts, global gas geopolitics",
        "note": "Ceramics/glass (gas-fired) and cement (coal/pet-coke) are textbook margin victims.",
    },
    {
        "key": "AGRI_COMMODITY_MOVES",
        "category": "COMMODITY",
        "triggers": ["sugar price", "wheat price", "cotton price",
                     "palm oil", "rubber price", "agri commodity"],
        "root_cause": (
            "Farm-gate/global agri prices shift input costs "
            "for FMCG/textiles/tyres and realizations for "
            "producers."
        ),
        "horizon": "MEDIUM",
        "base_confidence": 55,
        "effects": [
            {"order": 1, "target": "SUGAR", "sign": 1, "strength": 60},
            {"order": 1, "target": "FMCG", "sign": -1, "strength": 45},
            {"order": 1, "target": "TEXTILE", "sign": -1, "strength": 45},
            {"order": 1, "target": "TYRE", "sign": -1, "strength": 40},
            {"order": 2, "target": "RURAL", "sign": 1, "strength": 35},
        ],
        "monitor": "Which side of the trade the specific commodity places each sector",
        "leading": "Monsoon, MSP announcements, export bans, global crop reports",
        "note": (
            "Direction depends on the commodity: palm oil up hurts FMCG (soap/food), "
            "helps nothing listed big; sugar up helps mills; cotton up hurts spinners "
            "initially, helps if they carry inventory."
        ),
    },

    # ======================================================
    # CURRENCY
    # ======================================================
    {
        "key": "INR_DEPRECIATION",
        "category": "CURRENCY",
        "triggers": ["rupee falls", "rupee weakens", "inr depreciat",
                     "rupee record low", "rupee slide"],
        "root_cause": (
            "Dollar earnings worth more in INR; dollar costs "
            "hurt importers; FII returns erode (can trigger "
            "outflow spiral)."
        ),
        "horizon": "MEDIUM",
        "base_confidence": 70,
        "effects": [
            {"order": 1, "target": "IT", "sign": 1, "strength": 65},
            {"order": 1, "target": "PHARMA", "sign": 1, "strength": 55},
            {"order": 1, "target": "TEXTILE", "sign": 1, "strength": 50},
            {"order": 1, "target": "OMC", "sign": -1, "strength": 50},
            {"order": 1, "target": "AVIATION", "sign": -1, "strength": 55},
            {"order": 2, "target": "CONSUMER DURABLE", "sign": -1, "strength": 40},
            {"order": 2, "target": "AUTO", "sign": -1, "strength": 30},
            {"order": 3, "target": "CHEMICAL", "sign": 1, "strength": 30},
        ],
        "monitor": "Speed of move (gradual = manageable; gap = risk-off), RBI intervention, FII flows",
        "leading": "DXY, crude, FII selling streaks, US yields",
        "note": "Exporters with low import content win cleanly (IT best). Fast depreciation = risk-off for everything first.",
    },
    {
        "key": "INR_APPRECIATION",
        "category": "CURRENCY",
        "triggers": ["rupee gains", "rupee strengthens", "inr appreciat",
                     "rupee rall"],
        "root_cause": "Mirror of depreciation: importers relieved, exporters' realizations shrink.",
        "horizon": "MEDIUM",
        "base_confidence": 65,
        "effects": [
            {"order": 1, "target": "IT", "sign": -1, "strength": 55},
            {"order": 1, "target": "PHARMA", "sign": -1, "strength": 45},
            {"order": 1, "target": "AVIATION", "sign": 1, "strength": 45},
            {"order": 1, "target": "OMC", "sign": 1, "strength": 40},
            {"order": 2, "target": "CONSUMER DURABLE", "sign": 1, "strength": 35},
        ],
        "monitor": "FII inflow persistence, RBI reserve accumulation (caps appreciation)",
        "leading": "Dollar weakness, EM inflow cycles, IPO/FDI pipelines",
        "note": "RBI historically caps sharp appreciation by buying dollars — fades fast.",
    },

    # ======================================================
    # GOVERNMENT POLICY
    # ======================================================
    {
        "key": "BUDGET_CAPEX_PUSH",
        "category": "POLICY",
        "triggers": ["budget capex", "infrastructure outlay",
                     "capital expenditure budget", "capex allocation",
                     "union budget"],
        "root_cause": (
            "Government capex multiplier: orders flow to "
            "infra/capital goods over 1-3 years, then to "
            "their entire supply chains."
        ),
        "horizon": "LONG",
        "base_confidence": 65,
        "effects": [
            {"order": 1, "target": "INFRA", "sign": 1, "strength": 65},
            {"order": 1, "target": "CAPITAL GOODS", "sign": 1, "strength": 65},
            {"order": 1, "target": "CEMENT", "sign": 1, "strength": 55},
            {"order": 1, "target": "STEEL", "sign": 1, "strength": 50},
            {"order": 2, "target": "PIPE", "sign": 1, "strength": 45},
            {"order": 2, "target": "CONSTRUCTION", "sign": 1, "strength": 50},
            {"order": 2, "target": "BANK", "sign": 1, "strength": 35},
            {"order": 3, "target": "LOGISTICS", "sign": 1, "strength": 30},
        ],
        "monitor": "Actual award/tender velocity vs announcement (slippage is the norm), NHAI/railway ordering",
        "leading": "Pre-budget expectations (priced-in risk!), fiscal space, election calendar",
        "note": (
            "Budget-day moves often reverse within a week (expectations game). "
            "The real trade is the ORDER FLOW over following quarters — track tenders, not speeches."
        ),
    },
    {
        "key": "DEFENCE_SPENDING",
        "category": "POLICY",
        "triggers": ["defence procurement", "defence acquisition",
                     "defence budget", "defence order", "aon approval",
                     "defence indigenisation", "defence export"],
        "root_cause": (
            "Indigenization policy + procurement pipeline: "
            "multi-year revenue visibility for domestic "
            "defence manufacturers and their tier-2 chain."
        ),
        "horizon": "LONG",
        "base_confidence": 70,
        "effects": [
            {"order": 1, "target": "DEFENCE", "sign": 1, "strength": 75},
            {"order": 2, "target": "ELECTRONICS", "sign": 1, "strength": 45},
            {"order": 2, "target": "FORGING", "sign": 1, "strength": 40},
            {"order": 3, "target": "SPECIALTY STEEL", "sign": 1, "strength": 30},
        ],
        "monitor": "Stage (AoN → RFP → contract: years of slippage), order book/revenue conversion rates",
        "leading": "Border tensions, import-ban lists (positive for domestic), MoD budget utilization",
        "note": (
            "Announcement stage matters enormously: AoN ≠ contract. In hot theme phases, "
            "later-stage announcements are pre-priced and fade — check theme heat first."
        ),
    },
    {
        "key": "RAILWAY_CAPEX",
        "category": "POLICY",
        "triggers": ["railway capex", "railway order", "vande bharat",
                     "railway modernisation", "rail tender", "railway budget"],
        "root_cause": "Rolling stock + track + electrification orders flow to a small, identifiable supplier set.",
        "horizon": "LONG",
        "base_confidence": 65,
        "effects": [
            {"order": 1, "target": "RAILWAY", "sign": 1, "strength": 70},
            {"order": 2, "target": "WAGON", "sign": 1, "strength": 55},
            {"order": 2, "target": "CAPITAL GOODS", "sign": 1, "strength": 40},
            {"order": 3, "target": "STEEL", "sign": 1, "strength": 25},
        ],
        "monitor": "Tender-to-award timelines, execution capacity of winners (over-ordered books)",
        "leading": "Budget allocations, election-year acceleration",
        "note": "Small listed universe concentrates the flow — moves are violent both ways.",
    },
    {
        "key": "PLI_SCHEME",
        "category": "POLICY",
        "triggers": ["pli scheme", "production linked incentive",
                     "pli approval", "pli allocation"],
        "root_cause": (
            "Subsidized capacity building: winners get margin "
            "support + capex justification; import "
            "substitution reshapes supply chains."
        ),
        "horizon": "LONG",
        "base_confidence": 60,
        "effects": [
            {"order": 1, "target": "ELECTRONICS", "sign": 1, "strength": 55},
            {"order": 1, "target": "PHARMA", "sign": 1, "strength": 40},
            {"order": 1, "target": "SOLAR", "sign": 1, "strength": 50},
            {"order": 2, "target": "COMPONENT", "sign": 1, "strength": 40},
            {"order": 2, "target": "INDUSTRIAL REAL ESTATE", "sign": 1, "strength": 30},
        ],
        "monitor": "Actual disbursement vs allocation (chronically slow), named beneficiary lists",
        "leading": "Scheme-specific application windows, import dependency data",
        "note": "Trade the NAMED beneficiaries, not the theme — PLI headlines lift whole sectors that mostly don't qualify.",
    },
    {
        "key": "RENEWABLE_EV_POLICY",
        "category": "POLICY",
        "triggers": ["renewable energy target", "solar policy", "green hydrogen",
                     "ev policy", "ev subsidy", "fame scheme", "battery policy",
                     "semiconductor policy", "chip incentive"],
        "root_cause": "Energy-transition subsidies redirect capex: new-economy winners, old-economy questions.",
        "horizon": "LONG",
        "base_confidence": 55,
        "effects": [
            {"order": 1, "target": "RENEWABLE", "sign": 1, "strength": 60},
            {"order": 1, "target": "SOLAR", "sign": 1, "strength": 60},
            {"order": 1, "target": "EV", "sign": 1, "strength": 55},
            {"order": 2, "target": "CABLE", "sign": 1, "strength": 40},
            {"order": 2, "target": "POWER", "sign": 1, "strength": 35},
            {"order": 2, "target": "BATTERY", "sign": 1, "strength": 45},
            {"order": 3, "target": "COPPER", "sign": 1, "strength": 25},
            {"order": 3, "target": "AUTO ANCILLARY", "sign": -1, "strength": 20},
        ],
        "monitor": "Subsidy per unit economics, execution bottlenecks (land/grid), Chinese competition",
        "leading": "Global energy prices, COP commitments, state tender pipelines",
        "note": "ICE-ancillary makers (exhaust, fuel systems) are the slow-motion 3rd-order losers of EV policy.",
    },
    {
        "key": "RURAL_HOUSING_PUSH",
        "category": "POLICY",
        "triggers": ["rural spending", "pm awas", "housing scheme",
                     "rural development", "mgnrega", "farm income",
                     "msp hike"],
        "root_cause": "Rural purchasing power injection: consumption staples, 2-wheelers, affordable housing chains benefit.",
        "horizon": "MEDIUM",
        "base_confidence": 60,
        "effects": [
            {"order": 1, "target": "FMCG", "sign": 1, "strength": 50},
            {"order": 1, "target": "TWO WHEELER", "sign": 1, "strength": 55},
            {"order": 1, "target": "AGRO", "sign": 1, "strength": 50},
            {"order": 2, "target": "CEMENT", "sign": 1, "strength": 40},
            {"order": 2, "target": "MICROFINANCE", "sign": 1, "strength": 45},
            {"order": 2, "target": "FERTILIZER", "sign": 1, "strength": 35},
        ],
        "monitor": "Rural volume growth in FMCG results, tractor/2W sales, rural wage data",
        "leading": "Monsoon, election calendar (pre-election rural pushes are seasonal)",
        "note": "Effects show in volumes with a 1-2 quarter lag; stocks move on announcement, verify on volumes.",
    },

    # ======================================================
    # TRADE POLICY
    # ======================================================
    {
        "key": "CHINA_PLUS_ONE",
        "category": "TRADE",
        "triggers": ["china+1", "china plus one", "tariff on china",
                     "us tariffs china", "supply chain shift",
                     "manufacturing relocation"],
        "root_cause": (
            "Global buyers diversify from China: Indian "
            "manufacturers gain RFQs in chemicals, "
            "electronics, textiles; logistics chain benefits."
        ),
        "horizon": "LONG",
        "base_confidence": 55,
        "effects": [
            {"order": 1, "target": "CHEMICAL", "sign": 1, "strength": 55},
            {"order": 1, "target": "ELECTRONICS", "sign": 1, "strength": 50},
            {"order": 1, "target": "TEXTILE", "sign": 1, "strength": 45},
            {"order": 2, "target": "PORT", "sign": 1, "strength": 35},
            {"order": 2, "target": "LOGISTICS", "sign": 1, "strength": 35},
            {"order": 2, "target": "INDUSTRIAL REAL ESTATE", "sign": 1, "strength": 30},
            {"order": 3, "target": "CAPITAL GOODS", "sign": 1, "strength": 25},
        ],
        "monitor": "Export data by category, new client announcements in specialty chem/EMS",
        "leading": "US/EU tariff announcements, China production costs, geopolitics",
        "note": "Slow structural trade measured in years; spikes on tariff headlines, compounds on order wins.",
    },
    {
        "key": "IMPORT_DUTY_PROTECTION",
        "category": "TRADE",
        "triggers": ["import duty", "anti-dumping", "safeguard duty",
                     "customs duty hike", "import restriction", "import ban"],
        "root_cause": "Protection raises domestic realizations for the protected industry; user industries pay more.",
        "horizon": "MEDIUM",
        "base_confidence": 65,
        "effects": [
            {"order": 1, "target": "PROTECTED", "sign": 1, "strength": 60},
            {"order": 2, "target": "USER INDUSTRY", "sign": -1, "strength": 40},
        ],
        "monitor": "Which industry is protected (dynamic) — read the notification's HS codes",
        "leading": "DGTR investigations (public months before duty), industry lobbying",
        "note": (
            "Generic model: identify protected industry from the event text; steel duties "
            "help steelmakers hurt auto; solar-cell duties help domestic cell makers hurt developers."
        ),
    },

    # ======================================================
    # GEOPOLITICS
    # ======================================================
    {
        "key": "WAR_CONFLICT",
        "category": "GEOPOLITICAL",
        "triggers": ["war", "military conflict", "border clash",
                     "missile strike", "invasion", "attack on"],
        "root_cause": (
            "Risk-off + supply fears: crude/gold spike, "
            "equities derate, defence spending expectations "
            "rise."
        ),
        "horizon": "SHORT",
        "base_confidence": 60,
        "effects": [
            {"order": 1, "target": "DEFENCE", "sign": 1, "strength": 60},
            {"order": 1, "target": "OIL", "sign": 1, "strength": 45},
            {"order": 1, "target": "AVIATION", "sign": -1, "strength": 55},
            {"order": 1, "target": "PAINT", "sign": -1, "strength": 40},
            {"order": 2, "target": "IT", "sign": -1, "strength": 30},
            {"order": 2, "target": "FERTILIZER", "sign": -1, "strength": 35},
            {"order": 2, "target": "GOLD FINANCE", "sign": 1, "strength": 30},
        ],
        "monitor": "Crude/gold as real-time conflict gauges, shipping insurance rates, escalation vs de-escalation",
        "leading": "Diplomatic breakdown news, troop movements (already priced when public)",
        "note": (
            "Initial panic typically overshoots and mean-reverts unless supply chains "
            "actually break (Russia-Ukraine 2022: fertilizer/gas effects persisted; most conflicts fade in days)."
        ),
    },
    {
        "key": "SHIPPING_DISRUPTION",
        "category": "GEOPOLITICAL",
        "triggers": ["red sea", "suez", "shipping disruption",
                     "freight rates surge", "container shortage",
                     "port congestion", "strait of hormuz"],
        "root_cause": "Freight costs and transit times jump: shipowners win, importers/exporters with thin margins lose.",
        "horizon": "SHORT",
        "base_confidence": 65,
        "effects": [
            {"order": 1, "target": "SHIPPING", "sign": 1, "strength": 70},
            {"order": 1, "target": "LOGISTICS", "sign": 1, "strength": 40},
            {"order": 2, "target": "TEXTILE", "sign": -1, "strength": 40},
            {"order": 2, "target": "CHEMICAL", "sign": -1, "strength": 35},
            {"order": 2, "target": "OMC", "sign": -1, "strength": 30},
        ],
        "monitor": "Baltic indices, container spot rates, rerouting announcements",
        "leading": "Regional conflict news near chokepoints",
        "note": "Shipping stocks are pure freight-rate torque — fastest, cleanest expression both ways.",
    },
    {
        "key": "ELECTION_EVENT",
        "category": "GEOPOLITICAL",
        "triggers": ["election result", "exit poll", "lok sabha",
                     "assembly election", "coalition", "mandate"],
        "root_cause": "Policy-continuity repricing: capex/PSU themes live or die on the expected regime.",
        "horizon": "SHORT",
        "base_confidence": 55,
        "effects": [
            {"order": 1, "target": "PSU", "sign": 1, "strength": 50},
            {"order": 1, "target": "INFRA", "sign": 1, "strength": 45},
            {"order": 1, "target": "DEFENCE", "sign": 1, "strength": 40},
            {"order": 2, "target": "BANK", "sign": 1, "strength": 35},
        ],
        "monitor": "Continuity vs change probability; signs flip on upset results",
        "leading": "Exit polls (unreliable — 2004/2024 lessons), betting markets",
        "note": (
            "SIGNS FLIP with the outcome: continuity = capex themes rally; upset = violent "
            "unwind (Jun-2024: -6% day on reduced majority, recovered in days). Trade small, "
            "expect gaps, distrust exit polls."
        ),
    },

    # ======================================================
    # REGULATORY
    # ======================================================
    {
        "key": "REGULATORY_MOAT_COMPRESSION",
        "category": "REGULATORY",
        "triggers": ["market coupling", "license opened", "monopoly ends",
                     "price cap", "tariff cap", "margin cap", "fee cap",
                     "open access", "interoperability mandate"],
        "root_cause": (
            "The IEX lesson: when a regulator changes market "
            "structure, a business whose moat WAS the market "
            "structure gets structurally re-rated. Earnings "
            "may be fine; the MULTIPLE compresses because "
            "the monopoly premium is gone."
        ),
        "horizon": "LONG",
        "base_confidence": 75,
        "effects": [
            {"order": 1, "target": "AFFECTED", "sign": -1, "strength": 80},
            {"order": 2, "target": "CHALLENGER", "sign": 1, "strength": 45},
        ],
        "monitor": (
            "Any listed company whose margin/moat exists by regulatory grace: "
            "exchanges, depositories, registrars, gas utilities with area monopolies, "
            "credit bureaus, rating agencies — screen the portfolio for regulatory-moat exposure"
        ),
        "leading": "Consultation papers (months of warning!), regulator speeches, court directions",
        "note": (
            "AI rule: consultation paper = the warning shot, not noise. Structural derating "
            "is NOT a dip to buy — multiples don't mean-revert when the moat is gone. "
            "Exit/avoid on structure-change proposals affecting held names."
        ),
    },
    {
        "key": "SEBI_TIGHTENING",
        "category": "REGULATORY",
        "triggers": ["sebi curbs", "f&o restrictions", "margin norms",
                     "sebi circular", "surveillance measure", "asm list"],
        "root_cause": "Market-microstructure tightening: leverage/volume shrinks, broker/exchange revenue pools reprice.",
        "horizon": "MEDIUM",
        "base_confidence": 60,
        "effects": [
            {"order": 1, "target": "BROKER", "sign": -1, "strength": 55},
            {"order": 1, "target": "EXCHANGE", "sign": -1, "strength": 45},
            {"order": 2, "target": "SMALL CAP", "sign": -1, "strength": 35},
        ],
        "monitor": "Derivative volume trends post-implementation, broker ARPU guidance",
        "leading": "SEBI consultation papers, F&O-losses studies, regulator commentary",
        "note": "2024-25 F&O curbs: broking/exchange volumes hit exactly as consultation papers signaled.",
    },

    # ======================================================
    # NATURAL EVENTS
    # ======================================================
    {
        "key": "GOOD_MONSOON",
        "category": "NATURAL",
        "triggers": ["above normal monsoon", "good monsoon",
                     "imd normal forecast", "surplus rainfall"],
        "root_cause": "Rural income visibility: kharif sowing up, food inflation contained (rate-cut space), rural demand cycle.",
        "horizon": "LONG",
        "base_confidence": 60,
        "effects": [
            {"order": 1, "target": "AGRO", "sign": 1, "strength": 55},
            {"order": 1, "target": "FERTILIZER", "sign": 1, "strength": 55},
            {"order": 1, "target": "TWO WHEELER", "sign": 1, "strength": 45},
            {"order": 1, "target": "TRACTOR", "sign": 1, "strength": 55},
            {"order": 2, "target": "FMCG", "sign": 1, "strength": 40},
            {"order": 2, "target": "MICROFINANCE", "sign": 1, "strength": 35},
            {"order": 3, "target": "CEMENT", "sign": 1, "strength": 25},
        ],
        "monitor": "Spatial distribution (aggregate can lie), sowing progress weekly, reservoir levels",
        "leading": "IMD/Skymet forecasts (April-May), El Niño/La Niña status",
        "note": "Forecast moves stocks in May; reality moves earnings in Oct-Mar. Distribution > aggregate.",
    },
    {
        "key": "WEAK_MONSOON_DROUGHT",
        "category": "NATURAL",
        "triggers": ["below normal monsoon", "deficient rainfall",
                     "drought", "el nino monsoon", "monsoon deficit"],
        "root_cause": "Rural stress + food inflation: consumption slows, rate cuts postponed, irrigation/agri-input demand shifts.",
        "horizon": "LONG",
        "base_confidence": 60,
        "effects": [
            {"order": 1, "target": "TWO WHEELER", "sign": -1, "strength": 50},
            {"order": 1, "target": "FMCG", "sign": -1, "strength": 45},
            {"order": 1, "target": "TRACTOR", "sign": -1, "strength": 50},
            {"order": 1, "target": "MICROFINANCE", "sign": -1, "strength": 45},
            {"order": 2, "target": "IRRIGATION", "sign": 1, "strength": 35},
            {"order": 2, "target": "SUGAR", "sign": 1, "strength": 30},
        ],
        "monitor": "Food CPI trajectory, rural wage growth, MSP/loan-waiver policy responses",
        "leading": "El Niño declarations, June-July rainfall tracking",
        "note": "Government typically responds with rural stimulus — the 2nd-order policy offset arrives with a lag.",
    },
    {
        "key": "FLOODS_CYCLONE",
        "category": "NATURAL",
        "triggers": ["flood", "cyclone", "heavy rains disrupt",
                     "waterlogging", "landfall"],
        "root_cause": "Localized destruction: insurance claims, crop damage, logistics disruption, then reconstruction demand.",
        "horizon": "SHORT",
        "base_confidence": 50,
        "effects": [
            {"order": 1, "target": "INSURANCE", "sign": -1, "strength": 40},
            {"order": 1, "target": "LOGISTICS", "sign": -1, "strength": 30},
            {"order": 2, "target": "CEMENT", "sign": 1, "strength": 30},
            {"order": 2, "target": "PIPE", "sign": 1, "strength": 25},
        ],
        "monitor": "Affected industrial clusters (plant-level exposure of held names)",
        "leading": "IMD warnings, cyclone tracking",
        "note": "Mostly noise at index level; matters when a held company's PLANT is in the path — check facilities.",
    },
    {
        "key": "HEAT_WAVE",
        "category": "NATURAL",
        "triggers": ["heat wave", "heatwave", "record temperature",
                     "power demand record"],
        "root_cause": "Cooling demand spikes: power demand records, beverages/ACs sell, outdoor labor productivity falls.",
        "horizon": "SHORT",
        "base_confidence": 60,
        "effects": [
            {"order": 1, "target": "POWER", "sign": 1, "strength": 50},
            {"order": 1, "target": "CONSUMER DURABLE", "sign": 1, "strength": 50},
            {"order": 1, "target": "BEVERAGE", "sign": 1, "strength": 45},
            {"order": 2, "target": "COAL", "sign": 1, "strength": 35},
            {"order": 2, "target": "CONSTRUCTION", "sign": -1, "strength": 20},
        ],
        "monitor": "Peak power demand data (daily), AC channel inventories",
        "leading": "IMD seasonal outlooks (Feb-Mar)",
        "note": "Seasonal and partially anticipated; surprise = intensity/duration beyond forecasts.",
    },
]
