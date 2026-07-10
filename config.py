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
CAPITAL = 50000

# ==========================
# POSITION
# ==========================
RISK_MODE = "PERCENT"        # PERCENT / FIXED
RISK_PER_TRADE = 0.01        # 1% of Capital
FIXED_RISK = 1000            #  Used when RISK_MODE = "FIXED"

MAX_CAPITAL_PER_TRADE = CAPITAL

MAX_OPEN_POSITIONS = 20


# ==========================
# LIVE ACCOUNT
# ==========================

BROKER_ACCOUNT = "PRIMARY"

LIVE_CAPITAL = 50000

# ==========================
# STRATEGY
# ==========================
MIN_PRICE = 200
ENTRY_BUFFER = 1.0
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
TRADING_MODE = "LIVE"      # PAPER / LIVE
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

TRADE_LOG_FILE = "trade_log.csv"

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


ENTRY_CUTOFF_TIME = "15:00"

HARD_EXIT_TIME = "15:15"

ORDER_RETRY_COUNT = 3

API_TIMEOUT_SECONDS = 10

VERSION = "2.0.0-LIVE-READY"