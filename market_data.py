import os
import threading
import time
import traceback
import queue
from datetime import datetime

from dotenv import load_dotenv
from dhanhq import DhanContext, MarketFeed

from config import WATCHDOG_TIMEOUT, HARD_EXIT_TIME
from core.watchlist import get_instruments
from core.instrument_loader import InstrumentLoader
from core.engine import Engine
from intelligence.price_engine import price_engine
from notifications.error_logger import ErrorLogger
from notifications.event_logger import event_logger
from notifications.telegram_command_center import TelegramCommandCenter

load_dotenv()

# --------------------------------------------------
# ENGINE INITIALIZATION
# --------------------------------------------------

engine = Engine()
loader = InstrumentLoader()
logger = ErrorLogger()
telegram_command_center = TelegramCommandCenter(
    engine,
    os.getenv("TELEGRAM_BOT_TOKEN"),
    os.getenv("TELEGRAM_CHAT_ID")
)

# --------------------------------------------------
# DHAN CONTEXT
# --------------------------------------------------

context = DhanContext(
    os.getenv("DHAN_CLIENT_ID"),
    os.getenv("DHAN_ACCESS_TOKEN")
)

# --------------------------------------------------
# WATCHLIST
# --------------------------------------------------

instruments = get_instruments()

expected_ticks = {
    str(item[1]): False
    for item in instruments
}

security_ids = [
    str(item[1]) for item in instruments
]

print(f"Loaded {len(instruments)} instruments")

engine.monitor.set_universe(len(instruments))

event_logger.system(
    event="ENGINE_STARTED",
    message="ORB Auto Trader Started",
    data={
        "universe": len(instruments),
        "paper_mode": True,
        "version": "1.0"
    }
)

# --------------------------------------------------
# SAME-DAY TRADE RECONCILIATION
#
# Fix for the re-entry bug found live on 2026-07-20: ORBEngine's
# entry_taken flag lives only in memory and gets wiped on every
# restart, with nothing telling it which symbols already have a
# trade today -- confirmed causing BANKINDIA and BHARATFORG to
# both re-enter the same day after a restart. This runs once at
# startup, BEFORE any ticks can create a fresh orb_data entry, and
# covers BOTH cases:
#   1. Already CLOSED today  -> read from trade_log_v2.csv
#   2. Currently OPEN        -> read from open_positions.json
#      (position_recovery.py has no entry_taken logic of its own,
#      so without this an open position is exposed to the same
#      re-entry risk as a closed one)
# --------------------------------------------------

import csv as _csv
from datetime import date as _date
from config import TRADE_LOG_FILE
from trading.position_recovery import PositionRecovery

already_traded_ids = set()

# 1. Currently open positions -- open_positions.json is already
#    keyed by security_id, so no symbol lookup needed here.
try:
    _open_positions = PositionRecovery().load()
    already_traded_ids.update(_open_positions.keys())
except Exception as e:
    print(f"[RECONCILE] Open positions check failed: {e}")

# 2. Already-closed trades today -- trade_log_v2.csv logs by
#    symbol, so build a symbol -> security_id map from the same
#    instruments/loader already set up above.
try:
    _symbol_to_id = {
        loader.get_symbol(str(item[1])): str(item[1])
        for item in instruments
    }

    today_str = _date.today().strftime("%Y-%m-%d")

    with open(TRADE_LOG_FILE, "r", newline="", encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            if row.get("Date") != today_str:
                continue

            symbol = row.get("Symbol", "")
            sid = _symbol_to_id.get(symbol)

            if sid is not None:
                already_traded_ids.add(sid)
            else:
                print(
                    f"[RECONCILE] Could not map symbol "
                    f"'{symbol}' from trade log to a "
                    f"security_id -- skipped."
                )

except FileNotFoundError:
    pass  # No trades logged yet today -- nothing to reconcile
except Exception as e:
    print(f"[RECONCILE] Closed-trade check failed: {e}")

engine.orb_engine.load_already_traded(already_traded_ids)

print(
    f"[RECONCILE] {len(already_traded_ids)} symbol(s) marked "
    f"already-traded-today (open + closed) -- protected from "
    f"re-entry after this restart."
)

# --------------------------------------------------
# HISTORICAL ORB SCHEDULER
# --------------------------------------------------

def historical_orb_scheduler():

    started = False

    while not started:

        current_time = datetime.now().strftime("%H:%M")

        if current_time >= "09:30":

            print("Starting Historical ORB Background Loader...")

            threading.Thread(
                target=engine.historical_data.preload_orb,
                args=(security_ids,),
                daemon=True
            ).start()

            print("Historical ORB Background Loader Started")

            started = True

        else:

            time.sleep(5)


threading.Thread(
    target=historical_orb_scheduler,
    daemon=True,
    name="HistoricalORBScheduler"
).start()


telegram_thread = threading.Thread(
    target=telegram_command_center.run,
    daemon=True,
    name="TelegramCommandCenter"
)

telegram_thread.start()

print("Telegram Command Center Started")

# --------------------------------------------------
# NOTE: News collection now runs as its own independent
# 24/7 service on Railway (railway_main.py + railway_news_engine.py),
# so it has been intentionally removed from here. This process
# is now purely focused on trading -- ticks, ORB, execution --
# with no news-related background work competing for resources
# during market hours.
# --------------------------------------------------

# --------------------------------------------------
# TICK QUEUE + WORKER THREAD
#
# Root cause fix: the previous design called feed.get_data()
# in a loop, which only kept the WebSocket's event loop alive
# for the instant of receiving ONE tick, then let it go fully
# idle until the next call. That idle time meant the server's
# keepalive pings were often missed, causing frequent disconnects
# -- worse under heavy tick load, exactly matching what was
# being observed live.
#
# Fix: use the SDK's persistent run() mode (continuous event
# loop, connection stays alive and responsive throughout) and
# hand off each tick to a queue immediately. A separate worker
# thread drains that queue and does the actual heavy processing
# (engine.process_tick). This means tick processing time can
# NEVER delay the WebSocket's ability to respond to keepalive
# pings, regardless of how many stocks/engines are involved.
# --------------------------------------------------

tick_queue = queue.Queue()


def tick_worker():
    """
    Consumes ticks from the queue and runs the actual engine
    processing, completely decoupled from the WebSocket thread.
    """
    while True:
        try:
            tick = tick_queue.get()

            if tick is None:
                continue

            tick_type = tick.get("type")

            # ---------------------------------
            # Previous Close Messages
            # ---------------------------------
            if tick_type == "Previous Close":

                security_id = str(tick["security_id"])
                symbol = loader.get_symbol(security_id)

                if symbol is not None:
                    price_engine.set_previous_close(
                        symbol,
                        float(tick["prev_close"])
                    )

                continue

            # ---------------------------------
            # Ignore everything except live ticks
            # ---------------------------------
            if tick_type != "Ticker Data":
                continue

            security_id = str(tick["security_id"])
            symbol = loader.get_symbol(security_id)

            if symbol is None:
                print(f"Unknown Security ID : {security_id}")
                continue

            if expected_ticks.get(security_id) is False:
                expected_ticks[security_id] = True

            engine.process_tick(
                security_id=security_id,
                symbol=symbol,
                ltp=float(tick["LTP"]),
                ltt=tick["LTT"]
            )

        except Exception:
            print("\n========== TICK WORKER ERROR ==========")
            traceback.print_exc()
            print("========================================\n")


threading.Thread(
    target=tick_worker,
    daemon=True,
    name="TickWorker"
).start()

print("Tick Worker Thread Started")

# --------------------------------------------------
# WATCHDOG MONITOR THREAD
#
# Fix for the silent hangs found live on 2026-07-20 (three
# separate incidents, zero warnings, one confirmed ₹8,093.60
# missed-profit cost on a single trade). Root cause: the OLD
# watchdog only ever checked itself from inside process_tick's
# own finally block -- so if ticks stopped arriving entirely,
# process_tick was never called again and the watchdog never
# fired either.
#
# This thread has ITS OWN timer, completely independent of
# whether ticks are flowing -- so it WILL fire during a genuine
# tick-flow stoppage, not just a brief gap that self-resolves.
#
# Deliberately NOT auto-restarting the connection or the process
# here. Two reasons: (1) a botched automatic reconnect/restart
# could itself cause problems -- e.g. the day-trade-tracking
# re-entry bug found the same day means a restart can currently
# make an already-closed symbol look freshly tradeable again,
# so an automatic restart loop could silently create MORE bad
# re-entries, not fewer; (2) a human noticing immediately via a
# loud, unmistakable Telegram alert and restarting deliberately
# is safer until that re-entry bug is fixed. Revisit automatic
# recovery once that's resolved.
# --------------------------------------------------

def watchdog_monitor():
    alerted = False

    while True:
        time.sleep(15)

        elapsed = engine.watchdog.seconds_since_last_tick()

        if elapsed >= WATCHDOG_TIMEOUT and not alerted:
            alerted = True

            message = (
                f"🚨 NO LIVE TICKS FOR {int(elapsed)}s\n\n"
                f"The engine has not received a single tick in "
                f"over {WATCHDOG_TIMEOUT}s. This usually means the "
                f"WebSocket has silently stopped delivering data "
                f"even though the process is still running.\n\n"
                f"ACTION NEEDED: check the terminal now. If it's "
                f"genuinely stuck, restart main.py -- open "
                f"positions are NOT protected (no stop/target/"
                f"square-off checks run) while ticks are stalled."
            )

            print("\n" + "=" * 60)
            print("WATCHDOG ALERT: NO LIVE TICKS")
            print("=" * 60)
            print(message)
            print("=" * 60 + "\n")

            try:
                engine.telegram.send(message)
            except Exception:
                pass

        elif elapsed < WATCHDOG_TIMEOUT and alerted:
            # Ticks resumed -- clear the alert so a FUTURE stall
            # triggers a fresh warning instead of staying silent.
            alerted = False

            try:
                engine.telegram.send(
                    "🟢 Ticks resumed — watchdog alert cleared."
                )
            except Exception:
                pass


threading.Thread(
    target=watchdog_monitor,
    daemon=True,
    name="WatchdogMonitor"
).start()

print("Watchdog Monitor Thread Started")

# --------------------------------------------------
# SQUARE-OFF MONITOR THREAD
#
# Fix for the missing 3:15 PM forced square-off -- confirmed
# completely absent from engine.py on 2026-07-20 (HARD_EXIT_TIME
# is defined in config.py but nothing anywhere ever read it; a
# full-file grep for HARD_EXIT_TIME/square_off/15:15 in engine.py
# returned zero matches).
#
# Built the same way as the watchdog fix, and for the same
# reason: anything embedded inside process_tick's own call chain
# goes silent during a tick-flow hang -- exactly what happened to
# the old watchdog and the news-staleness check today. This runs
# on its own independent timer instead, so the square-off REQUEST
# fires reliably at HARD_EXIT_TIME regardless of whether ticks
# happen to be flowing at that exact moment.
#
# Honest limitation: request_exit_all() flags positions for exit;
# actually CLOSING them still happens inside process_tick on the
# next tick, same as any other exit. So if a hang is ALSO
# happening exactly at 15:15, the request is queued correctly but
# won't execute until ticks resume -- the same tick-dependency
# every other exit (stop/target/trail) already has. The
# WatchdogMonitor above is what catches that scenario, typically
# well before 15:15, since it starts alerting after 60s of silence.
#
# Entry cutoff (15:14, one minute earlier) already blocks new
# entries via strategy.py's is_buy_signal -- this thread's only
# job is force-exiting whatever is still open at 15:15.
# --------------------------------------------------

def square_off_monitor():
    fired_today = False
    last_date = datetime.now().strftime("%Y-%m-%d")

    while True:
        time.sleep(10)

        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        # New trading day -- reset so square-off can fire again
        if today_str != last_date:
            last_date = today_str
            fired_today = False

        current_time = now.strftime("%H:%M")

        if current_time >= HARD_EXIT_TIME and not fired_today:
            fired_today = True

            print("\n" + "=" * 60)
            print("SQUARE-OFF: FORCED END-OF-DAY EXIT")
            print("=" * 60)
            print(
                f"Time: {current_time} >= HARD_EXIT_TIME "
                f"({HARD_EXIT_TIME})"
            )
            print("Requesting exit on all open positions...")
            print("=" * 60 + "\n")

            try:
                engine.exit_all()
            except Exception as e:
                print(f"[SQUARE-OFF ERROR] {e}")

            try:
                engine.telegram.send(
                    f"🔔 FORCED SQUARE-OFF\n\n"
                    f"Time: {current_time}\n"
                    f"All open positions have been requested to "
                    f"exit (MIS hard cutoff, "
                    f"HARD_EXIT_TIME={HARD_EXIT_TIME})."
                )
            except Exception:
                pass


threading.Thread(
    target=square_off_monitor,
    daemon=True,
    name="SquareOffMonitor"
).start()

print("Square-Off Monitor Thread Started")

# --------------------------------------------------
# LIVE MARKET LOOP -- PERSISTENT CALLBACK MODE
# --------------------------------------------------

startup_message_sent = False


def on_connect(instance):
    global startup_message_sent

    print("✅ Connected to Dhan MarketFeed")

    event_logger.system(
        event="MARKET_CONNECTED",
        message="Connected to Dhan MarketFeed"
    )

    try:
        if not startup_message_sent:
            print("Sending Telegram Startup Message...")

            engine.telegram.send(
                "🟢 ORB Auto Trader Started\n\n"
                f"Status      : RUNNING\n"
                f"Connection  : CONNECTED\n"
                f"Mode        : PAPER\n"
                f"Universe    : {len(instruments)}"
            )

            startup_message_sent = True

        else:
            print("Sending Telegram Reconnected Message...")

            engine.telegram.send(
                "🟢 Dhan Reconnected Successfully\n\n"
                "Status      : CONNECTED\n"
                "Connection  : RESTORED"
            )

    except Exception:
        pass


def on_error(instance, error):
    print(f"\n⚠️ MarketFeed error: {error}")

    event_logger.system(
        event="MARKET_FEED_ERROR",
        message=str(error)
    )

    try:
        engine.telegram.send(
            f"🟡 MarketFeed error.\n{str(error)[:150]}\nReconnecting..."
        )
    except Exception:
        pass


def on_message(instance, tick):
    """
    Called by the SDK the instant a tick arrives. Kept deliberately
    lightweight -- just hands off to the queue -- so the WebSocket's
    own event loop never gets blocked by heavy processing.
    """
    try:
        if tick is not None:
            # Fix (2026-07-20): record freshness HERE, at raw
            # receipt, not inside process_tick. This is what lets
            # the independent watchdog thread below detect a real
            # stoppage even if the tick_worker thread itself gets
            # stuck downstream -- freshness now reflects "is data
            # actually arriving," not "did processing succeed."
            engine.watchdog.tick_received()
            tick_queue.put(tick)
    except Exception:
        print("\n========== ON_MESSAGE ERROR ==========")
        traceback.print_exc()
        print("=======================================\n")


# --------------------------------------------------
# AUTO-RECONNECT WRAPPER (added 2026-07-21)
#
# Fix for the confirmed live failure: internet/feed outage
# killed the process with no restart. feed.run() threw, hit
# the old bare except block, sent one "connection lost"
# Telegram message, and the process ended -- meaning
# EVERYTHING downstream (tick processing, exits, the
# square-off monitor) went silent until a human noticed and
# manually restarted main.py. That day it took 34-38 minutes
# for someone to notice and manually close 3 open positions
# past HARD_EXIT_TIME.
#
# Fix: keep the SAME process alive and re-create + reconnect
# the feed on any failure, instead of letting the process
# die. Everything ELSE in this file (engine, threads,
# watchdog, square-off monitor, telegram command center) was
# already set up ONCE above and keeps running regardless --
# only the feed connection itself needs to retry, so this
# loop deliberately does NOT re-run any of that setup.
#
# Stops retrying after market hours (past 16:00 IST) so it
# doesn't spin forever overnight hammering a dead connection
# -- a fresh trading day needs a fresh process start anyway.
# --------------------------------------------------

RECONNECT_BACKOFF_SECONDS = 15
reconnect_count = 0

while True:

    current_time = datetime.now().strftime("%H:%M")
    if current_time >= "16:00":
        print(
            "[RECONNECT] Past 16:00 IST -- market day is over. "
            "Not reconnecting further; process will exit."
        )
        break

    feed = MarketFeed(
        context,
        instruments,
        "v2",
        on_connect=on_connect,
        on_message=on_message,
        on_error=on_error
    )

    print("✅ MarketFeed object created")
    print("Starting persistent connection (feed.run())...")

    try:
        # feed.run() is a BLOCKING call that keeps a single continuous
        # event loop alive for the whole session -- including automatic
        # reconnect handling inside the SDK itself -- so the keepalive
        # ping/pong exchange is never interrupted by idle gaps the way
        # the previous get_data()-in-a-loop pattern was.
        feed.run()

        # A clean return (no exception) from a BLOCKING call is itself
        # unexpected during market hours -- treat it the same as a
        # dropped connection and reconnect rather than letting the
        # process exit silently.
        print(
            "[RECONNECT] feed.run() returned without an exception "
            "-- reconnecting..."
        )

    except KeyboardInterrupt:
        event_logger.system(
            event="ENGINE_STOPPED",
            message="Stopped by KeyboardInterrupt"
        )
        print("\nStopping ORB Auto Trader...")
        try:
            feed.close_connection()
        except Exception:
            pass
        break

    except Exception as e:
        reconnect_count += 1

        event_logger.error(
            event="ENGINE_EXCEPTION",
            message=str(e)
        )
        logger.log(e)

        print("\n========== FULL TRACEBACK ==========")
        traceback.print_exc()
        print("====================================")

        try:
            engine.telegram.send(
                f"🔴 Dhan connection lost (reconnect attempt "
                f"#{reconnect_count})\n{str(e)[:200]}\n\n"
                f"Auto-reconnecting in "
                f"{RECONNECT_BACKOFF_SECONDS}s -- open positions "
                f"are NOT protected (no stop/target/square-off "
                f"checks run) until the connection is back."
            )
        except Exception:
            pass

    time.sleep(RECONNECT_BACKOFF_SECONDS)