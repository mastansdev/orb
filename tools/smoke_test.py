"""
End-to-End Paper Smoke Test

Simulates a full trading sequence through the REAL
Engine.process_tick pipeline without any network:

    1. ORB formation (09:15 – 09:29)
    2. ORB completion (09:31)
    3. Breakout candles (evaluation pipeline fires:
       evidence → conviction → brain → risk governor)
    4. Forced position injection + stoploss exit
       (exit pipeline fires: memory recording,
       risk governor feedback, company history)

External services (Railway Postgres) are replaced with
fakes so the test runs anywhere.

Run:
    py tools/smoke_test.py
"""

import io
import os
import sys
import contextlib

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# ==========================================================
# Patch network-backed repositories BEFORE engine import
# ==========================================================

import tempfile

import repositories.intelligence_repository as intel_repo_module


class FakeIntelligenceRepository:

    def __init__(self, *args, **kwargs):
        pass

    def load_new_intelligence(self):
        return []

    def save_story(self, story):
        pass


intel_repo_module.IntelligenceRepository = (
    FakeIntelligenceRepository
)

# ==========================================================
# Isolate ALL smoke-test state from the real bot
# ==========================================================

# 1. Memory database goes to a temp file, never the
#    production institutional_memory.db
import repositories.memory_repository as memory_repo_module

SMOKE_DB = os.path.join(
    tempfile.gettempdir(), "smoke_institutional_memory.db"
)
if os.path.exists(SMOKE_DB):
    os.remove(SMOKE_DB)

memory_repo_module.MEMORY_DB_FILE = SMOKE_DB

# 1b. Trade log goes to a temp file too — smoke trades
#     must never pollute the real edge-analysis data
import trading.trade_logger as trade_logger_module

trade_logger_module.TRADE_LOG_FILE = os.path.join(
    tempfile.gettempdir(), "smoke_trade_log.csv"
)

# 1c. Fills log isolated too
import trading.execution_quality as execution_quality_module

execution_quality_module.ExecutionQuality.FILE_NAME = (
    os.path.join(tempfile.gettempdir(), "smoke_fills.csv")
)

# 1d. Market recorder isolated (avoids touching the
#     real session database)
import core.market_recorder as market_recorder_module

SMOKE_RECORDER = os.path.join(
    tempfile.gettempdir(), "smoke_recorder.db"
)
if os.path.exists(SMOKE_RECORDER):
    os.remove(SMOKE_RECORDER)

market_recorder_module.MarketRecorder.DB_FILE = (
    SMOKE_RECORDER
)

# 2. Position recovery file must not leak a fake paper
#    position into the real bot on next startup
RECOVERY_FILE = "open_positions.json"


def clean_recovery_file():
    if not os.path.exists(RECOVERY_FILE):
        return

    try:
        os.remove(RECOVERY_FILE)
        print(f"[SMOKE] Removed {RECOVERY_FILE}")
    except OSError:
        # Fallback: neutralize instead of delete
        with open(RECOVERY_FILE, "w", encoding="utf-8") as f:
            f.write("{}")
        print(f"[SMOKE] Emptied {RECOVERY_FILE}")


clean_recovery_file()

# news_engine / brain resolve the class at import time,
# so make sure they import AFTER the patch.
import news.news_engine as news_engine_module
news_engine_module.IntelligenceRepository = (
    FakeIntelligenceRepository
)

import intelligence.brain as brain_module
brain_module.IntelligenceRepository = (
    FakeIntelligenceRepository
)

# ==========================================================

from core.engine import Engine
from core.master_loader import master_loader

PASSED = 0
FAILED = 0


def check(name, condition):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  ✓ {name}")
    else:
        FAILED += 1
        print(f"  ✗ {name}")


def run():
    print("=" * 60)
    print("END-TO-END PAPER SMOKE TEST")
    print("=" * 60)

    engine = Engine()

    # Silence Telegram for the whole test — no real
    # messages while smoke testing.
    engine.telegram.send = lambda message: None
    engine.risk_governor.telegram = None

    check("engine constructed", engine is not None)
    check("risk governor attached", engine.risk_governor is not None)
    check(
        "pattern engine attached",
        engine.trade_selection_engine.pattern_engine is not None
    )
    check(
        "company intelligence attached",
        engine.trade_selection_engine.company_intelligence
        is not None
    )

    # ---------------------------------
    # Pick a real symbol from the master
    # ---------------------------------
    symbols = master_loader.get_all_symbols()
    symbol = sorted(symbols)[0]
    security_id = master_loader.symbol_to_security.get(symbol)

    check(
        f"test symbol resolved ({symbol})",
        security_id is not None
    )

    errors = io.StringIO()

    def tick(ltp, ltt):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            engine.process_tick(
                security_id=security_id,
                symbol=symbol,
                ltp=ltp,
                ltt=ltt
            )
        output = buffer.getvalue()
        if "TICK PROCESSING ERROR" in output:
            errors.write(output)
        return output

    # ---------------------------------
    # 1. ORB formation
    # ---------------------------------
    tick(500.0, "09:16:00")
    tick(505.0, "09:20:00")
    tick(495.0, "09:25:00")

    orb = engine.get_orb(security_id)
    check("ORB building", orb is not None and not orb["completed"])

    # ---------------------------------
    # 2. ORB completion
    # ---------------------------------
    tick(500.0, "09:31:00")
    orb = engine.get_orb(security_id)
    check("ORB completed", orb is not None and orb["completed"])
    check("ORB high correct", orb["high"] == 505.0)
    check("ORB low correct", orb["low"] == 495.0)

    # ---------------------------------
    # 3. Breakout → full evaluation pipeline
    #    (candle must CLOSE above ORB high + buffer)
    # ---------------------------------
    tick(507.0, "09:32:00")   # candle 09:32 building
    tick(508.0, "09:32:30")
    output = tick(509.0, "09:33:00")  # 09:32 candle closes at 508

    pipeline_fired = (
        "LIVE ORB CANDIDATE" in output
        or "BRAIN" in output
        or "TRADE SELECTION" in output
        or "ENGINE SKIPPED" in output
    )
    check("evaluation pipeline fired on breakout", pipeline_fired)
    check("no tick processing errors", errors.getvalue() == "")

    decision_record = engine.decision_audit.get(security_id)
    check("decision audited", decision_record is not None)

    # ---------------------------------
    # 4. Exit pipeline with real position
    #    (inject a paper position, then hit its stop)
    # ---------------------------------
    entry_price = 508.0
    stop_loss = 495.0 - 2.0

    injected = engine.risk_manager.create_trade(
        entry_price, stop_loss
    )
    injected["qty"] = 10
    injected["symbol"] = symbol
    injected["entry_time"] = "09:33:00"
    injected["entry_date"] = "2026-07-18"
    injected["capital_used"] = entry_price * 10
    injected["sector"] = "SMOKETEST_SECTOR"
    injected["industry"] = "SMOKETEST_IND"
    injected["theme"] = "SMOKETEST"
    injected["conviction"] = 61.5

    engine.trades[security_id] = injected
    engine.position_manager.recover_position(
        security_id, symbol, entry_price, stop_loss, 10
    )
    engine.open_position_manager.add(security_id, injected)

    closed_before = engine.risk_governor.trades_closed

    #

    output = tick(490.0, "09:45:00")   # below stop → STOPLOSS exit

    check(
        "stoploss exit executed",
        security_id not in engine.trades
    )
    check(
        "risk governor learned the loss",
        engine.risk_governor.trades_closed == closed_before + 1
    )
    check(
        "loss streak updated",
        engine.risk_governor.consecutive_losses >= 1
    )

    # Memory recorded?
    stats = engine.market_memory.orb_stats(symbol)
    check("ORB outcome remembered", stats["samples"] >= 1)

    failures = engine.market_memory.orb_failures_today(symbol)
    check("failure counted for pattern engine", failures >= 1)

    trade_stats = engine.market_memory.symbol_trade_stats(symbol)
    check("trade outcome remembered", trade_stats["trades"] >= 1)

    events = engine.company_intelligence.repository.company_events(
        symbol
    )
    check("company history recorded", len(events) >= 1)

    # ---------------------------------
    # 5. Pattern engine now sees the failure
    # ---------------------------------
    report = engine.memory_report(symbol)
    check("memory report generated", symbol in report)

    # ---------------------------------
    # 6. Telegram accessors
    # ---------------------------------
    risk_status = engine.risk_status()
    check(
        "risk status accessor",
        "day_pnl" in risk_status
        and "portfolio_heat" in risk_status
    )

    company_report = engine.company_report(symbol)
    check("company dossier accessor", symbol in company_report)

    pool_report = engine.opportunity_pool_report()
    check("pool accessor", "OPPORTUNITY POOL" in pool_report)

    engine.shutdown()

    # Never leave smoke-test positions behind for the
    # real bot to "recover" on next startup.
    clean_recovery_file()

    print()
    print("=" * 60)
    print(f"PASSED : {PASSED}")
    print(f"FAILED : {FAILED}")
    print("=" * 60)

    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(run())
