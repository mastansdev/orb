import time


class Watchdog:

    def __init__(self):

        self.last_tick_time = time.time()
        self.warning_printed = False

    # -----------------------------------------

    def tick_received(self):

        self.last_tick_time = time.time()
        self.warning_printed = False

    # -----------------------------------------

    def check(self):

        elapsed = time.time() - self.last_tick_time

        if elapsed >= 60 and not self.warning_printed:

            print()
            print("=" * 60)
            print("WARNING : NO LIVE MARKET TICKS")
            print("=" * 60)
            print(f"No market data received for {int(elapsed)} seconds.")
            print("Possible reasons:")
            print(" - Internet disconnected")
            print(" - Dhan WebSocket disconnected")
            print(" - Market closed")
            print("=" * 60)
            print()

            self.warning_printed = True