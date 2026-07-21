"""
Trade Controller

Responsibilities
----------------
Single authority for trading permissions and manual trading controls.

This module DOES NOT:
    • Place orders
    • Exit positions
    • Communicate with broker
    • Parse Telegram commands

It only maintains the current trading control state.

Future modules (Telegram, GUI, Brain, News Engine, etc.)
must communicate through this controller.
"""

from threading import RLock


class TradeController:
    """
    Central trading control authority.
    """

    def __init__(self):
        self._lock = RLock()

        # Master controls
        self._trading_enabled = True
        self._entries_enabled = True

        # One-shot request
        self._exit_all_requested = False

        # Per-symbol manual exit requests (2026-07-21) --
        # keyed by security_id. Same one-shot semantics as
        # exit-all above, just scoped to a single position --
        # this is what powers the dashboard's per-position
        # Sell button (PAPER-mode simulated manual close).
        self._exit_requested_ids = set()

    # --------------------------------------------------
    # Trading Controls
    # --------------------------------------------------

    def enable_trading(self):
        with self._lock:
            self._trading_enabled = True

    def disable_trading(self):
        with self._lock:
            self._trading_enabled = False

    def is_trading_enabled(self):
        with self._lock:
            return self._trading_enabled

    # --------------------------------------------------
    # Entry Controls
    # --------------------------------------------------

    def enable_entries(self):
        with self._lock:
            self._entries_enabled = True

    def disable_entries(self):
        with self._lock:
            self._entries_enabled = False

    def is_entries_enabled(self):
        with self._lock:
            return self._entries_enabled

    # --------------------------------------------------
    # Exit Controls
    # --------------------------------------------------

    def request_exit_all(self):
        with self._lock:
            self._exit_all_requested = True

    def clear_exit_all(self):
        with self._lock:
            self._exit_all_requested = False

    def is_exit_all_requested(self):
        with self._lock:
            return self._exit_all_requested

    # --------------------------------------------------
    # Per-Symbol Manual Exit (2026-07-21)
    # --------------------------------------------------

    def request_exit_symbol(self, security_id):
        with self._lock:
            self._exit_requested_ids.add(security_id)

    def clear_exit_requested(self, security_id):
        with self._lock:
            self._exit_requested_ids.discard(security_id)

    def is_exit_requested(self, security_id):
        with self._lock:
            return security_id in self._exit_requested_ids