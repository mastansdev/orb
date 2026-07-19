import os
import threading
import time
import traceback
import queue
from datetime import datetime

from dotenv import load_dotenv
from dhanhq import DhanContext, MarketFeed

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
            tick_queue.put(tick)
    except Exception:
        print("\n========== ON_MESSAGE ERROR ==========")
        traceback.print_exc()
        print("=======================================\n")


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

except KeyboardInterrupt:
    event_logger.system(
        event="ENGINE_STOPPED",
        message="Stopped by KeyboardInterrupt"
    )
    print("\nStopping ORB Auto Trader...")
    feed.close_connection()

except Exception as e:
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
            "🔴 Dhan Connection Lost (fatal)\n"
            f"{str(e)[:200]}"
        )
    except Exception:
        pass