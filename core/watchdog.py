import time
import threading


class Watchdog:
    """
    Tracks tick freshness.

    IMPORTANT: this class only tracks state -- it does NOT decide
    when to alert. That decision now lives in an independent
    background thread (watchdog_monitor() in market_data.py),
    started once at process startup and running on its own timer,
    completely decoupled from process_tick.

    Why this changed: the previous check() method only ever ran
    from inside process_tick's own finally block. If ticks stopped
    arriving entirely, process_tick was never called again, so the
    watchdog never fired either -- a heartbeat monitor that only
    checks the pulse when the heart is already beating. It could
    only ever detect a brief gap that later self-resolved on its
    own, never a genuine sustained hang. This was confirmed live on
    2026-07-20: three real hangs, zero watchdog warnings, ever.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.last_tick_time = time.time()

    # -----------------------------------------

    def tick_received(self):
        """
        Call this the MOMENT a tick is confirmed received --
        ideally from on_message itself (raw WebSocket receipt),
        not from inside process_tick. That way freshness tracking
        reflects "is the connection actually alive," independent
        of whether downstream processing succeeds or the queue
        backs up.
        """
        with self._lock:
            self.last_tick_time = time.time()

    # -----------------------------------------

    def seconds_since_last_tick(self):
        with self._lock:
            return time.time() - self.last_tick_time

    # -----------------------------------------

    def check(self):
        """
        Deprecated no-op. Kept only so existing call sites inside
        engine.py's process_tick don't need to change -- calling
        this is now harmless but does nothing. Real detection
        happens in market_data.py's watchdog_monitor() thread.
        """
        pass