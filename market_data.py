import os
import sys
import threading
import time
import traceback
import queue
from datetime import datetime

# --------------------------------------------------
# Auto-Capture Everything To A File (2026-07-22)
#
# Fix: today's biggest investigation (#14 in the after-close
# punch list) needed to know exactly what the bot printed at
# the moment of a specific trade decision, and the answer was
# "check the terminal scrollback" -- which is gone the instant
# the window closes or scrolls past its buffer. DecisionTrace
# (tools/decision_trace.py) only ever prints, never saves.
# From now on, EVERYTHING printed to this terminal is also
# written to a timestamped file under logs/, automatically, no
# manual `> bot_log.txt` redirect needed. One file per process
# start (not appended across restarts) so a specific morning's
# run is never mixed with a later restart's output -- exactly
# the kind of mixing that made today's timeline confusing to
# reconstruct.
# --------------------------------------------------
os.makedirs("logs", exist_ok=True)
_log_filename = (
    f"logs/bot_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.log"
)


class _Tee:
    def __init__(self, *streams):
        self._streams = streams

    def write(self, data):
        for s in self._streams:
            try:
                s.write(data)
            except Exception:
                pass

    def flush(self):
        for s in self._streams:
            try:
                s.flush()
            except Exception:
                pass


_log_file = open(_log_filename, "a", encoding="utf-8")
sys.stdout = _Tee(sys.stdout, _log_file)
sys.stderr = _Tee(sys.stderr, _log_file)
print(f"[LOGGING] Full session output also being saved to {_log_filename}")

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
# Fix (2026-07-22): news ingestion now runs on its own thread
# from process start, independent of ticks -- see
# Engine.start_news_thread() in core/engine.py. Started here,
# right after construction, same place the old tick-gated
# version used to only start working from.
engine.start_news_thread()
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
            # Fix (2026-07-21): now that the feed subscribes in
            # Quote mode (core/master_loader.py), packets arrive
            # tagged "Quote Data" instead of "Ticker Data" --
            # confirmed real packet shape from today's live
            # diagnostic (premarket_feed_test_20260721_085953.log):
            # {'type': 'Quote Data', 'security_id':..., 'LTP':...,
            # 'LTT':..., 'volume':..., 'total_buy_quantity':...,
            # 'total_sell_quantity':..., 'open'/'high'/'low'/
            # 'close':...}. Same LTP/LTT keys as the old Ticker
            # Data packets, plus volume -- accepting both types
            # here rather than assuming every environment/reconnect
            # is guaranteed to only ever send one or the other.
            if tick_type not in ("Ticker Data", "Quote Data"):
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
                ltt=tick["LTT"],
                volume=int(tick.get("volume", 0) or 0),
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

        # Fix (2026-07-22): the watchdog had no concept of market
        # hours -- it fires the exact same "NO LIVE TICKS, open
        # positions are NOT protected" alarm whether the feed
        # genuinely died at 11am, or it's simply 8:34am and Dhan
        # hasn't started sending pre-open data yet. Confirmed live
        # today: false alarms every ~60s from process start until
        # market opens, each one a scary Telegram message about
        # unprotected positions that don't even exist yet (no
        # entries are possible before market opens anyway).
        #
        # 09:07 -- not 09:00 -- because last night's real captured
        # diagnostic (premarket_feed_test log) confirmed genuine
        # pre-open discovered price only starts appearing around
        # 09:07:57; before that, packets carry stale prior-session
        # data even once the WebSocket itself is connected.
        #
        # Keep resetting the clock (not just skipping the check)
        # while we're outside the window, so the FIRST real check
        # once the window opens starts counting fresh -- otherwise
        # elapsed time silently accumulated since process start
        # would trip the alarm the instant the window opens.
        now_hm = datetime.now().strftime("%H:%M")
        if now_hm < "09:07" or now_hm > "15:30":
            engine.watchdog.tick_received()
            continue

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

# --------------------------------------------------
# Fix (2026-07-22): Ctrl+C didn't reliably stop main.py.
#
# Confirmed live today: the FIRST Ctrl+C during feed.run()
# doesn't always surface as a Python KeyboardInterrupt at all --
# the dhanhq SDK's own WebSocket close handshake can absorb it
# and feed.run() returns NORMALLY instead (seen live: "sent 1000
# (OK); no close frame received"). That hits the "clean return"
# branch below, which always assumed a silent connection drop
# and reconnected -- exactly backwards from what the user wanted.
# The SECOND Ctrl+C then landed inside the bare
# time.sleep(RECONNECT_BACKOFF_SECONDS) below, which had no
# try/except around it at all -- an unhandled KeyboardInterrupt
# and an ugly traceback, though the process did still exit.
#
# Fix, same proven pattern already used in railway_main.py: a
# real OS-level SIGINT handler that just sets a flag, checked
# everywhere a Ctrl+C might land -- doesn't depend on any
# particular exception actually propagating through the SDK's
# own blocking call.
# --------------------------------------------------
_shutdown_requested = False

# --------------------------------------------------
# Fix (2026-07-22, take 2): the flag-based custom signal.signal()
# handler from the first attempt was verified correct in
# simulation but confirmed NOT to work live, twice, on the real
# machine -- even after moving feed.run() to a background thread.
#
# Traced deeper into the dhanhq SDK itself: feed.run() internally
# does `self.loop.run_until_complete(self._run_async())` -- an
# asyncio event loop -- and its OWN internal handling is
# `except KeyboardInterrupt: self.close_connection()`. That only
# works if a genuine KeyboardInterrupt lands inside that exact
# call, which is ONLY possible on the main thread (Python can
# never raise KeyboardInterrupt on a background thread, no
# matter what). Moving feed.run() to a background thread (still
# correct and necessary -- see below) makes the SDK's own
# handling permanently unreachable, which is fine as long as our
# OWN detection on the main thread works instead.
#
# Replacing the custom signal.signal(SIGINT, ...) override with
# plain try/except KeyboardInterrupt around the main thread's
# polling loop -- Python's DEFAULT Ctrl+C behavior, the most
# battle-tested path in CPython on every platform including
# Windows, instead of a hand-rolled handler that may not be
# firing reliably on this machine for reasons that can't be
# diagnosed further without live access to reproduce it. This
# is the standard, simplest pattern for exactly this situation.
# --------------------------------------------------

# --------------------------------------------------
# Fix (2026-07-22, take 3): confirmed live -- the first Ctrl+C
# now DOES get caught ("Stopping ORB Auto Trader..." printed),
# but the cleanup step feed.close_connection() itself hung: it
# internally calls a concurrent.futures Future.result() with NO
# timeout, waiting on the SDK's own asyncio loop. If that never
# resolves and the user (reasonably, waiting with no feedback)
# presses Ctrl+C a SECOND time, that second KeyboardInterrupt
# lands inside Future.result()'s wait -- and "except Exception:
# pass" around close_connection() does NOT catch it, because
# KeyboardInterrupt subclasses BaseException, not Exception.
# Result: an ugly unhandled traceback instead of a clean exit.
#
# Fix: run close_connection() on its own short-lived thread with
# an explicit timeout, so the main thread is never stuck waiting
# on the SDK indefinitely, and print visible feedback while
# waiting. A second Ctrl+C during that wait is now caught
# explicitly and just forces the exit instead of crashing.
# --------------------------------------------------


def _safe_close_connection(_feed, timeout=5):
    done = threading.Event()

    def _closer():
        try:
            _feed.close_connection()
        except Exception:
            pass
        finally:
            done.set()

    threading.Thread(
        target=_closer, daemon=True, name="feed-close"
    ).start()

    print(f"[SHUTDOWN] Closing feed connection (up to {timeout}s)...")
    try:
        finished = done.wait(timeout=timeout)
    except KeyboardInterrupt:
        print(
            "\n[SHUTDOWN] Second Ctrl+C -- forcing exit without "
            "waiting for cleanup."
        )
        return

    if not finished:
        print(
            f"[SHUTDOWN] close_connection() did not finish within "
            f"{timeout}s -- abandoning cleanup and exiting anyway "
            f"(this is safe: PAPER mode, no live orders pending)."
        )

while True:

    if _shutdown_requested:
        print("\nStopping ORB Auto Trader (Ctrl+C)...")
        event_logger.system(
            event="ENGINE_STOPPED",
            message="Stopped by Ctrl+C"
        )
        break

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
    print("Starting persistent connection (feed.run(), on its own thread)...")

    _feed_error = {"exc": None}

    def _run_feed(_feed=feed, _err=_feed_error):
        try:
            _feed.run()
        except Exception as e:
            _err["exc"] = e

    feed_thread = threading.Thread(
        target=_run_feed, daemon=True, name="dhan-feed"
    )
    feed_thread.start()

    # Main thread stays free the entire time the feed thread is
    # alive -- this loop is what's actually interruptible now.
    # Plain try/except KeyboardInterrupt (Python's default
    # Ctrl+C behavior) instead of a custom signal handler --
    # see the fix note above for why.
    try:
        while feed_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        _shutdown_requested = True

    if _shutdown_requested:
        print("\nStopping ORB Auto Trader (Ctrl+C)...")
        event_logger.system(
            event="ENGINE_STOPPED",
            message="Stopped by Ctrl+C"
        )
        _safe_close_connection(feed, timeout=5)
        try:
            feed_thread.join(timeout=5)
        except KeyboardInterrupt:
            pass
        break

    # feed_thread finished on its own -- either a clean return
    # (unexpected during market hours, treat like a drop) or it
    # raised (captured into _feed_error above, since exceptions
    # on a background thread don't propagate to the main thread
    # the way a direct call's would).
    exc = _feed_error["exc"]

    if exc is None:
        print(
            "[RECONNECT] feed.run() returned without an exception "
            "-- reconnecting..."
        )
    else:
        reconnect_count += 1

        event_logger.error(
            event="ENGINE_EXCEPTION",
            message=str(exc)
        )
        logger.log(exc)

        print("\n========== FULL TRACEBACK ==========")
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        print("====================================")

        try:
            engine.telegram.send(
                f"🔴 Dhan connection lost (reconnect attempt "
                f"#{reconnect_count})\n{str(exc)[:200]}\n\n"
                f"Auto-reconnecting in "
                f"{RECONNECT_BACKOFF_SECONDS}s -- open positions "
                f"are NOT protected (no stop/target/square-off "
                f"checks run) until the connection is back."
            )
        except Exception:
            pass

    # Responsive 1s-at-a-time sleep so Ctrl+C during the
    # reconnect backoff is caught within 1 second, same pattern
    # as railway_main.py's shutdown loop.
    try:
        for _ in range(RECONNECT_BACKOFF_SECONDS):
            time.sleep(1)
    except KeyboardInterrupt:
        _shutdown_requested = True

if _shutdown_requested:
    print("Shutdown complete.")