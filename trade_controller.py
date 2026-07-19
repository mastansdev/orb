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