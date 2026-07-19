"""
Adapter Configuration

Responsibilities
----------------
Global configuration shared by every external source adapter.

Owns
----
• HTTP Configuration
• Retry Configuration
• SSL Verification
• Default Headers
• Timing Defaults

Does NOT
---------
• Store source-specific URLs
• Store source-specific credentials
• Know NSE/BSE/RBI/SEBI
"""

# --------------------------------------------------
# HTTP
# --------------------------------------------------

CONNECT_TIMEOUT = 5

READ_TIMEOUT = 30

REQUEST_TIMEOUT = (
    CONNECT_TIMEOUT,
    READ_TIMEOUT,
)

VERIFY_SSL = True

# --------------------------------------------------
# Retry
# --------------------------------------------------

MAX_RETRIES = 3

RETRY_BACKOFF_SECONDS = 2

# --------------------------------------------------
# Polling Defaults
# --------------------------------------------------

DEFAULT_POLL_INTERVAL = 60

# --------------------------------------------------
# User Agent
# --------------------------------------------------

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/138.0 Safari/537.36"
)

# --------------------------------------------------
# Headers
# --------------------------------------------------

DEFAULT_HEADERS = {

    "User-Agent": USER_AGENT,

    "Accept": "application/json, text/plain, */*",

    "Accept-Language": "en-US,en;q=0.9",

    "Connection": "keep-alive",

    "Cache-Control": "no-cache",

    "Pragma": "no-cache",

}

# --------------------------------------------------
# Health
# --------------------------------------------------

MAX_CONSECUTIVE_FAILURES = 3

# --------------------------------------------------
# Statistics
# --------------------------------------------------

ENABLE_STATISTICS = True

# --------------------------------------------------
# Logging
# --------------------------------------------------

ENABLE_DEBUG_LOGGING = False