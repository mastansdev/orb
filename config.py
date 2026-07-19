"""
ORB Auto Trader Configuration
"""

# ---------------------------------
# Decision Trace
# ---------------------------------

DECISION_TRACE = True


# ==========================
# CAPITAL PROFILE  (plug & play)
# ==========================
#
# Change ONE line to test a different account size —
# every derived limit below scales automatically.
#
# Options: "30K" "50K" "1L" "2L" "5L" "10L" "20L"
#          "30L" "50L" "1CR"   (or a raw number)

CAPITAL_PROFILE = "10L"

CAPITAL_PROFILES = {
    "30K": 30_000,
    "50K": 50_000,
    "1L": 100_000,
    "2L": 200_000,
    "5L": 500_000,
    "10L": 1_000_000,
    "20L": 2_000_000,
    "30L": 3_000_000,
    "50L": 5_000_000,
    "1CR": 10_000_000,
}

# ==========================
# MIS LEVERAGE (Dhan/Kite style)
# ==========================
# Intraday equity margin: SEBI peak-margin floor is 20%
# of trade value = max 5× leverage. Brokers give 4-5×
# on liquid names. Paper mode now blocks MARGIN
# (value ÷ leverage), not full value — so capital
# requirements match reality.

MIS_LEVERAGE = 5

# ==========================
# DERIVED ACCOUNT LIMITS
# (scale with the profile — same % risk at every size)
# ==========================

CAPITAL = CAPITAL_PROFILES.get(
    str(CAPITAL_PROFILE).upper(),
    CAPITAL_PROFILE if isinstance(CAPITAL_PROFILE, int)
    else 100_000,
)

BUYING_POWER = CAPITAL * MIS_LEVERAGE

# Position VALUE cap: each position ≤20% of buying
# power → up to ~5 full-size concurrent positions.
MAX_CAPITAL_PER_TRADE = int(BUYING_POWER * 0.20)

# ==========================
# POSITION
# ==========================
RISK_MODE = "PERCENT"        # PERCENT / FIXED
RISK_PER_TRADE = 0.01        # 1% of CAPITAL (equity, not BP)
FIXED_RISK = 1000            #  Used when RISK_MODE = "FIXED"

MAX_OPEN_POSITIONS = 25


# ==========================
# LIVE ACCOUNT
# ==========================

BROKER_ACCOUNT = "PRIMARY"

LIVE_CAPITAL = 10000000

# ==========================
# STRATEGY
# ==========================
MIN_PRICE = 200
ENTRY_BUFFER_PCT = 0.1   # 0.1% above ORB high — replaces old flat-rupee ENTRY_BUFFER
ORB_BUFFER = 2.0
MAX_BREAKOUT_PERCENT = 1.0
RISK_REWARD = 1.0
TRAIL_STEP = 1.0
MIN_QTY = 10
MIN_TRADE_VALUE = 25000
MIN_ORB_RANGE_PERCENT = 1.0

# ==========================
# DAILY LIMITS  (scale with the profile)
# ==========================
# Expressed as % of EQUITY so a 30K account and a 1CR
# account both risk the same proportion. The Risk
# Governor further scales these by live market regime.

DAILY_MAX_LOSS_PCT = 0.03     # stop the day at -3% of equity
DAILY_MAX_PROFIT_PCT = 0.06   # lock the day at +6% of equity

DAILY_MAX_LOSS = int(CAPITAL * DAILY_MAX_LOSS_PCT)
DAILY_MAX_PROFIT = int(CAPITAL * DAILY_MAX_PROFIT_PCT)

# ==========================
# RISK GOVERNOR
# ==========================

# Master switch for the independent risk authority.
RISK_GOVERNOR_ENABLED = True

# Daily loss lockout uses DAILY_MAX_LOSS above.
# Loss is measured as realized + floating MTM.
DAILY_LOSS_INCLUDES_FLOATING = True

# When the daily loss lockout fires, also exit all
# open positions (not just block new entries).
KILL_SWITCH_EXIT_ALL = True

# Pause new entries after N consecutive losing trades.
MAX_CONSECUTIVE_LOSSES = 4

# Maximum simultaneous open positions in one sector.
MAX_POSITIONS_PER_SECTOR = 3

# Maximum total open risk (sum of entry-to-stop distance
# multiplied by quantity across open positions).
# Scales with equity: max 5% of equity at risk across
# all open positions simultaneously.
MAX_PORTFOLIO_HEAT = int(CAPITAL * 0.05)

# ==========================
# CONVICTION
# ==========================

# Minimum conviction score (0-100) required before the
# Brain may approve capital allocation.
CONVICTION_MIN_SCORE = 55

# Conviction grade boundaries
CONVICTION_GRADE_A_PLUS = 85
CONVICTION_GRADE_A = 70
CONVICTION_GRADE_B = 55

# ==========================
# DYNAMIC TRADE MANAGEMENT
# ==========================

DYNAMIC_MANAGEMENT_ENABLED = True

# Book a fraction of the position at this R-multiple
PARTIAL_BOOK_AT_R = 1.0
PARTIAL_BOOK_FRACTION = 0.5

# After this R-multiple, ratchet the trail to
# highest_price - TRAIL_DISTANCE_R * risk
TRAIL_AFTER_R = 1.5
TRAIL_DISTANCE_R = 0.75

# Block new entries on stocks with results today
RESULTS_DAY_BLOCK = True

# ==========================
# EVENT-DRIVEN ENTRY (Brain override — Rule-001)
# ==========================

# Massive catalysts can trigger entry WITHOUT waiting
# for an ORB breakout, any time before the cutoff.
EVENT_ENTRY_ENABLED = True
EVENT_ENTRY_MIN_IMPORTANCE = 75     # watchlist catalyst strength
EVENT_ENTRY_MIN_CONVICTION = 65     # higher bar than ORB entries
EVENT_ENTRY_FRESH_MINUTES = 45      # catalyst must be this fresh
EVENT_ENTRY_STOP_PCT = 1.2          # stop % when no ORB exists yet

# When the book is full, a stronger candidate REPLACES
# the weakest open position (advantage handled by
# PortfolioRiskManager.min_replacement_advantage).
POSITION_REPLACEMENT_ENABLED = True

# ==========================
# ADAPTIVE DAILY LIMITS (Brain-controlled risk)
# ==========================

# DAILY_MAX_LOSS / DAILY_MAX_PROFIT above become BASE
# values; the governor scales them with market regime.
ADAPTIVE_LIMITS_ENABLED = True

# Regime multipliers (loss_mult, profit_mult)
REGIME_LIMIT_MULTIPLIERS = {
    "TRENDING_UP":   (1.0, 3.0),
    "TRENDING_DOWN": (0.6, 1.0),
    "BEARISH":       (0.5, 0.8),
    "CHOPPY":        (0.7, 1.0),
    "FLAT":          (0.8, 1.0),
    "WARMUP":        (1.0, 1.0),
}

# ==========================
# SHOCK PROTECTION
# ==========================

# Peak-giveback guard (the +53k → -1.4L lesson):
# once day profit exceeds the floor, giving back this
# fraction of the peak = market reversal → exit all.
PEAK_GUARD_MIN_PROFIT = 8000
PEAK_GIVEBACK_PCT = 0.40

# Fast-drop guard: PnL falling this much within the
# window = shock → exit all.
FAST_DROP_RUPEES = 6000
FAST_DROP_WINDOW_MINUTES = 10

# Market-wide shock responder (breadth collapse →
# flatten + weakest-sector PE recommendation)
SHOCK_RESPONDER_ENABLED = True
SHOCK_BREADTH_PCT = 20       # ≤20% stocks advancing
SHOCK_AVG_CHANGE = -1.5      # and avg change ≤ -1.5%

# ==========================
# PRICED-IN DETECTION (buy the rumor, sell the news)
# ==========================

# If a stock already moved this much BEFORE its news
# arrived, the news is partially priced → evidence
# score is halved and tagged.
PRICED_IN_WARN_PCT = 3.0

# Above this pre-news move, positive news is treated
# as fully priced → no BUY evidence, no event entry
# (fade risk).
PRICED_IN_FADE_PCT = 5.0

# ==========================
# NEWS PIPELINE MONITOR
# ==========================

# During market hours, no story from Railway for this
# long → Telegram alarm (feed break detection).
NEWS_STALENESS_MINUTES = 45

# ==========================
# HOLD BRAIN (continuous thesis re-evaluation)
# ==========================
# "Withdraw capital immediately when probability
# deteriorates." Re-score every open position; exit when
# the reason to own it has decayed.

THESIS_ENGINE_ENABLED = True

# Exit if current conviction falls below this fraction
# of the conviction at entry (thesis has decayed).
THESIS_DECAY_FRACTION = 0.55

# Grace period after entry before thesis-exit can fire
# (let the trade breathe past entry noise).
THESIS_GRACE_MINUTES = 5

# ==========================
# PROFIT PROTECTION (every winner returns something)
# ==========================
# Once a trade reaches this R-multiple, the stop can
# NEVER fall below the locked floor — a real winner
# will not become a loser.
PROFIT_LOCK_AT_R = 0.6
PROFIT_LOCK_FLOOR_R = 0.15   # lock at least +0.15R

# ==========================
# MEMORY / PATTERNS
# ==========================

MEMORY_DB_FILE = "institutional_memory.db"

# A symbol that fails this many ORB breakouts today is
# penalized by the Pattern Engine.
MAX_ORB_FAILURES_PER_DAY = 2

# ==========================
# ORDER
# ==========================
ORDER_TYPE_MARKET = "MARKET"
ORDER_TYPE_LIMIT = "LIMIT"
ORDER_TYPE_STOP_LIMIT = "STOP_LIMIT"

ORDER_TYPE = ORDER_TYPE_MARKET
SLIPPAGE = 5

# ==========================
# EXECUTION
# ==========================
TRADING_MODE = "PAPER"      # PAPER / LIVE
PRODUCT_TYPE = "MIS"      # MIS / CNC / MTF
BROKER = "DHAN"

# ==========================
# ATM OPTION LEG (additive)
# ==========================
# On every confirmed breakout entry the bot ALSO buys 1 lot of the
# nearest-monthly ATM option (CE on breakout), IN ADDITION to the equity
# position. The equity trade is never changed or replaced.
ENABLE_OPTION_LEG = True            # master switch for the option leg
OPTION_LOTS = 1                     # lots per breakout (1 lot = 1x contract lot size)
OPTION_EXPIRY_PREF = "MONTHLY"      # MONTHLY (nearest monthly) — per strategy choice
OPTION_EXIT_WITH_EQUITY = True      # backstop: also close the leg if its equity exits first
OPTION_TIME_STOP = "15:10"          # force-close any open leg past this (IST) — no overnight
SCRIP_MASTER_PATH = "data/api-scrip-master.csv"   # source of option contracts

# ---- Greeks-aware premium exit management (independent of the equity) ----
# An option's P&L is driven by delta/gamma/theta/vega + time-to-expiry, all of
# which are already embedded in the live traded premium. So we manage the real
# premium: a ratcheting trailing stop that only moves UP (never gives profit
# back), a hard initial stop, an optional hard target, and a same-day time stop
# (so multi-day theta never accrues). Greeks are captured for context/logging.
OPTION_INDEPENDENT_EXIT = True      # manage the leg on its own premium (recommended)
OPTION_INITIAL_STOP_PCT = 25.0      # hard stop: exit if premium falls 25% below entry
OPTION_TRAIL_ACTIVATE_PCT = 20.0    # arm the trailing stop once premium is +20% in profit
OPTION_TRAIL_GIVEBACK_PCT = 15.0    # trail 15% below the PEAK premium; the stop never widens
OPTION_TARGET_PCT = 0.0             # 0 = disabled; else hard take-profit at +X% premium
OPTION_POLL_SECONDS = 5             # min seconds between premium/greeks polls per leg

# ==========================
# TEST
# ==========================
TEST_MODE = False
TEST_ORB_HIGH = 1300
TEST_ORB_LOW = 1290

# ==========================
# ORB
# ==========================

ORB_START_HOUR = 9
ORB_START_MINUTE = 15

ORB_END_HOUR = 9
ORB_END_MINUTE = 30

ORB_DURATION = 15

# ==========================
# BOT
# ==========================

STATUS_PRINT_INTERVAL = 300

WATCHDOG_TIMEOUT = 60

# ==========================
# TELEGRAM
# ==========================

SEND_STARTUP_ALERT = True
SEND_BUY_ALERT = True
SEND_SELL_ALERT = True
SEND_DAILY_REPORT = True

# ==========================
# FILES
# ==========================

DATA_FOLDER = "data"

TRADE_LOG_FILE = "trade_log_v2.csv"

UNIVERSE_FILE = "data/universe.csv"

API_SCRIP_MASTER_FILE = "data/api-scrip-master.csv"

MARKET_DATABASE_FILE = "data/market_database.csv"

SECTOR_DATABASE_FILE = "Masterdata/sector_database.csv"

# ==========================
# SYSTEM
# ==========================

BOT_NAME = "ORB AUTO TRADER"

# ==========================
# LIVE SAFETY
# ==========================

LIVE_CONFIRMATION_REQUIRED = False

ENABLE_ORDER_PLACEMENT = False

ENABLE_AUTO_EXIT = True

ENABLE_TELEGRAM_CONFIRMATION = True


ENTRY_CUTOFF_TIME = "15:14"   # GLOBAL hard rule: no new entries after this (MIS)

HARD_EXIT_TIME = "15:15"

ORDER_RETRY_COUNT = 3

API_TIMEOUT_SECONDS = 10

VERSION = "2.0.0-LIVE-READY"