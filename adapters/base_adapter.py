"""
Base Adapter

Responsibilities
----------------
Defines the common interface and shared infrastructure for all
external market/news data adapters.

Every adapter (NSE, BSE, RBI, SEBI, PIB, etc.) must inherit
from this class.

Owns
----
• Adapter Identity
• Source Metadata
• Poll Statistics
• Health Status
• Retry Tracking
• Enable / Disable
• Lifecycle

Does NOT
---------
• Fetch source-specific data
• Parse JSON/XML/RSS
• Normalize events
• Classify news
• Calculate impact

Child adapters must implement:
    connect()
    disconnect()
    poll()
"""

from abc import ABC, abstractmethod
from datetime import datetime


class BaseAdapter(ABC):

    def __init__(
        self,
        adapter_name: str,
        source_name: str,
        poll_interval: int,
        priority: int,
        reliability: float,
    ):

        # --------------------------------------------------
        # Identity
        # --------------------------------------------------

        self._adapter_name = adapter_name
        self._source_name = source_name

        # --------------------------------------------------
        # Configuration
        # --------------------------------------------------

        self._poll_interval = int(poll_interval)
        self._priority = int(priority)
        self._reliability = float(reliability)

        # --------------------------------------------------
        # State
        # --------------------------------------------------

        self._enabled = True
        self._connected = False

        # --------------------------------------------------
        # Statistics
        # --------------------------------------------------

        self.reset_statistics()

    # ==================================================
    # Lifecycle
    # ==================================================

    @abstractmethod
    def connect(self):
        """Connect to external source."""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from external source."""
        pass

    @abstractmethod
    def poll(self):
        """
        Poll source and return list of raw events.

        Returns
        -------
        list[dict]
        """
        pass

    # ==================================================
    # Statistics
    # ==================================================

    def reset_statistics(self):

        self._poll_count = 0

        self._success_count = 0
        self._failure_count = 0

        self._events_received = 0

        self._last_poll = None
        self._last_success = None
        self._last_failure = None

        self._last_error = None

        self._consecutive_failures = 0

        self._last_latency_ms = 0.0

    # ==================================================
    # Success / Failure Recording
    # ==================================================

    def record_success(self, latency_ms, events_received):

        self._poll_count += 1

        self._success_count += 1

        self._events_received += int(events_received)

        self._last_success = datetime.now()
        self._last_poll = self._last_success

        self._last_latency_ms = float(latency_ms)

        self._consecutive_failures = 0

        self._last_error = None

    def record_failure(self, error):

        self._poll_count += 1

        self._failure_count += 1

        self._consecutive_failures += 1

        self._last_failure = datetime.now()
        self._last_poll = self._last_failure

        self._last_error = str(error)

    # ==================================================
    # Enable / Disable
    # ==================================================

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def enabled(self):
        return self._enabled

    # ==================================================
    # Connection State
    # ==================================================

    def set_connected(self, connected: bool):
        self._connected = bool(connected)

    def connected(self):
        return self._connected

    # ==================================================
    # Metadata
    # ==================================================

    def adapter_name(self):
        return self._adapter_name

    def source_name(self):
        return self._source_name

    def priority(self):
        return self._priority

    def reliability(self):
        return self._reliability

    def poll_interval(self):
        return self._poll_interval

    # ==================================================
    # Health
    # ==================================================

    def healthy(self):

        return (
            self._enabled
            and self._connected
            and self._consecutive_failures < 3
        )

    def health(self):

        return {

            "adapter": self._adapter_name,

            "source": self._source_name,

            "enabled": self._enabled,

            "connected": self._connected,

            "healthy": self.healthy(),

            "consecutive_failures": self._consecutive_failures,

            "last_poll": self._last_poll,

            "last_success": self._last_success,

            "last_failure": self._last_failure,

            "last_error": self._last_error,

            "last_latency_ms": self._last_latency_ms,

        }

    # ==================================================
    # Statistics
    # ==================================================

    def statistics(self):

        return {

            "polls": self._poll_count,

            "successes": self._success_count,

            "failures": self._failure_count,

            "events_received": self._events_received,

        }