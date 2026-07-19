"""
ORB Auto Trader Configuration
"""

# ---------------------------------
# Decision Trace
# ---------------------------------

DECISION_TRACE = True


# ==========================
# ACCOUNT
# ==========================
CAPITAL = 10000000

# ==========================
# POSITION
# ==========================
RISK_MODE = "PERCENT"        # PERCENT / FIXED
RISK_PER_TRADE = 0.01        # 1% of Capital
FIXED_RISK = 1000            #  Used when RISK_MODE = "FIXED"

MAX_CAPITAL_PER_TRADE = 100000

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
# DAILY LIMITS
# ==========================
DAILY_MAX_LOSS = 5000
DAILY_MAX_PROFIT = 50000

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
MAX_PORTFOLIO_HEAT = 25000

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