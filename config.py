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

MAX_OPEN_POSITIONS = 999

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
ORDER_TYPE = "STOP_LIMIT"
SLIPPAGE = 5

# ==========================
# TRADING
# ==========================
TRADE_MODE = "PAPER"      # PAPER / LIVE
PRODUCT_TYPE = "MIS"      # MIS / CNC / MTF
BROKER = "DHAN"

# ==========================
# TEST
# ==========================
TEST_MODE = True
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


VERSION = "1.0.0-PAPER"