import os
import threading
import time
import traceback
from datetime import datetime

from dotenv import load_dotenv
from dhanhq import DhanContext, MarketFeed
from websockets.exceptions import ConnectionClosedError

from watchlist import get_instruments
from instrument_loader import InstrumentLoader
from engine import Engine
from price_engine import price_engine
from error_logger import ErrorLogger
from event_logger import event_logger
from telegram_command_center import TelegramCommandCenter

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

# Extract security IDs for historical preloading
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
# NEWS INTELLIGENCE SCHEDULER
# --------------------------------------------------
def news_scheduler():
    """
    Periodically collect and process market news.

    Runs independently from the live trading
    thread so news processing never blocks
    tick handling.
    """

    while True:

        try:

            print("[NEWS] Scheduler Wakeup")

            collected = engine.news_engine.collect()

            print(f"[NEWS] Collected = {collected}")

            if collected > 0:

                evidence = engine.news_engine.process()
                

                print(
                    f"[NEWS] Evidence = {len(evidence)}"
                )

        except Exception as e:

             print("\n========== NEWS TRACEBACK ==========")
             traceback.print_exc()
             print("====================================\n")

        print("[NEWS] Scheduler Sleeping")

        time.sleep(60)

threading.Thread(
    target=news_scheduler,
    daemon=True,
    name="NewsScheduler"
).start()

print("News Intelligence Scheduler Started")

# --------------------------------------------------
# LIVE MARKET LOOP INITIALIZATION
# --------------------------------------------------

startup_message_sent = False

while True:

    try:

        print("Connecting to Dhan...")

        feed = MarketFeed(
            context,
            instruments,
            "v2"
        )

        print("✅ MarketFeed object created")

        event_logger.system(
            event="MARKET_CONNECTED",
            message="Connected to Dhan MarketFeed"
        )

        # Send Telegram notification BEFORE blocking execution
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

        print("Calling run_forever()...")
        
        # Note: If your framework runs asynchronously in the background, 
        # the tick loop below captures the data.
        feed.run_forever()
        
        print("Processing live feed ticks...")

        while True:

            tick = feed.get_data()
            if tick is None:
                time.sleep(0.001)
                continue

            # ---------------------------------
            # Previous Close Messages
            # ---------------------------------
            if tick.get("type") == "Previous Close":

                security_id = str(tick["security_id"])

                symbol = loader.get_symbol(security_id)

                if symbol is not None:
                    price_engine.set_previous_close(
                        symbol,
                        float(tick["prev_close"])
                    )
                    print(f"PREV CLOSE SET -> {symbol} = {tick['prev_close']}")

                continue

            # ---------------------------------
            # Ignore everything except live ticks
            # ---------------------------------
            if tick.get("type") != "Ticker Data":
                continue

            security_id = str(tick["security_id"])

            symbol = loader.get_symbol(security_id)

            if symbol is None:
                print(f"Unknown Security ID : {security_id}")
                continue
            
            # Optional: Flip the expected_ticks flag to True when the first tick arrives
            if expected_ticks.get(security_id) is False:
                expected_ticks[security_id] = True
                
            
            engine.process_tick(
                security_id=security_id,
                symbol=symbol,
                ltp=float(tick["LTP"]),
                ltt=tick["LTT"]
            )

    except KeyboardInterrupt:

        event_logger.system(
            event="ENGINE_STOPPED",
            message="Stopped by KeyboardInterrupt"
        )

        print("\nStopping ORB Auto Trader...")
        break

    except ConnectionClosedError as e:

        event_logger.system(
            event="WEBSOCKET_RECONNECT",
            message=str(e)
        )

        print("\n⚠️ WebSocket keepalive timeout.")
        print("Reconnecting in 5 seconds...")

        try:
            engine.telegram.send(
                "🟡 WebSocket timeout.\n"
                "Reconnecting in 5 seconds..."
            )
        except Exception:
            pass

        time.sleep(5)

        print("Reconnecting...")

    except TimeoutError as e:

        event_logger.system(
            event="CONNECTION_TIMEOUT",
            message=str(e)
        )

        print("\n⚠️ Connection timeout.")
        print("Reconnecting in 5 seconds...")

        try:
            engine.telegram.send(
                "🟡 Connection timeout.\n"
                "Reconnecting in 5 seconds..."
            )
        except Exception:
            pass

        time.sleep(5)

        print("Reconnecting...")

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
                "🔴 Dhan Connection Lost\n"
                "Reconnecting in 5 seconds..."
            )
        except Exception:
            pass

        time.sleep(5)

        print("Reconnecting...")