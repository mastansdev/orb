from config import (
    BOT_NAME,
    VERSION,
    MODE,
    BROKER,
    CAPITAL,
    ORB_START_HOUR,
    ORB_START_MINUTE,
    ORB_END_HOUR,
    ORB_END_MINUTE,
    RISK_MODE,
    RISK_PER_TRADE,
    RISK_REWARD,
    MAX_OPEN_POSITIONS,
    SEND_STARTUP_ALERT,
    SEND_BUY_ALERT,
    SEND_SELL_ALERT,
    SEND_DAILY_REPORT,
    TRADE_LOG_FILE,
    UNIVERSE_FILE,
)


class StartupBanner:

    @staticmethod
    def show(universe):

        print()
        print("=" * 70)
        print(f"{BOT_NAME:^70}")
        print("=" * 70)
        print(f"Version               : {VERSION}")
        print(f"Mode                  : {MODE}")
        print(f"Broker                : {BROKER}")
        print(f"Capital               : ₹{CAPITAL:,}")
        print()
        print("Trading Configuration")
        print("-" * 70)
        print(f"ORB Time              : {ORB_START_HOUR:02}:{ORB_START_MINUTE:02} - {ORB_END_HOUR:02}:{ORB_END_MINUTE:02}")
        print(f"Risk Mode             : {RISK_MODE}")
        print(f"Risk Per Trade        : {RISK_PER_TRADE}")
        print(f"Risk Reward           : {RISK_REWARD}")
        print(f"Max Open Positions    : {MAX_OPEN_POSITIONS}")
        print(f"Universe Size         : {universe}")
        print()
        print("Notifications")
        print("-" * 70)
        print(f"Startup Alert         : {SEND_STARTUP_ALERT}")
        print(f"BUY Alert             : {SEND_BUY_ALERT}")
        print(f"SELL Alert            : {SEND_SELL_ALERT}")
        print(f"Daily Report          : {SEND_DAILY_REPORT}")
        print()
        print("System")
        print("-" * 70)
        print(f"Trade Log             : {TRADE_LOG_FILE}")
        print(f"Universe File         : {UNIVERSE_FILE}")
        print()
        print("STATUS : READY TO TRADE")
        print("=" * 70)
        print()