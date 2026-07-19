from __future__ import annotations

import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

from adapters.adapter_config import DEFAULT_HEADERS, REQUEST_TIMEOUT
from adapters.base_adapter import BaseAdapter


# ==========================================================
# NSE Adapter Description & Responsibilities
# ==========================================================
# Production-grade adapter for fetching official NSE RSS feeds.
#
# Owns:
# • RSS Download
# • XML Parsing
# • Event Validation
# • Canonical Event Building
# • Adapter Health
# • Statistics
#
# Does NOT:
# • Classify News
# • Score Impact
# • Normalize News
# • Store Memory
# • Influence Trading
# ==========================================================
class NSEAdapter(BaseAdapter):

    RSS_URL = "https://www.nseindia.com/rss/corporate-announcements.xml"

    SOURCE_NAME = "NSE"

    ADAPTER_NAME = "nse_adapter"

    PRIORITY = 1

    RELIABILITY = 0.99

    POLL_INTERVAL = 60

    # ------------------------------------------------------

    def __init__(self):

        super().__init__(
            adapter_name=self.ADAPTER_NAME,
            source_name=self.SOURCE_NAME,
            poll_interval=self.POLL_INTERVAL,
            priority=self.PRIORITY,
            reliability=self.RELIABILITY,
        )

    # ======================================================
    # Lifecycle
    # ======================================================

    def connect(self):

        self.set_connected(True)

        return True

    # ------------------------------------------------------

    def disconnect(self):

        self.set_connected(False)

        return True

    # ======================================================
    # Poll
    # ======================================================

    def poll(self):
        """Poll official NSE RSS feed.

        Returns
        -------
        list[dict]
            Canonical raw adapter events.
        """

        if not self.enabled():

            return []

        if not self.connected():

            self.connect()

        start_time = time.perf_counter()

        try:

            xml_data = self._download()

            events = self._parse(xml_data)

            latency_ms = (time.perf_counter() - start_time) * 1000

            self.record_success(
                latency_ms=latency_ms,
                events_received=len(events),
            )

            return events

        except Exception as exc:

            self.record_failure(exc)

            return []

    # ======================================================
    # Download
    # ======================================================

    def _download(self):
        """Download RSS feed from NSE.

        Returns
        -------
        bytes
            Raw XML response.

        Raises
        ------
        RuntimeError
            If download fails or invalid response received.
        """

        request = urllib.request.Request(
            url=self.RSS_URL,
            headers=DEFAULT_HEADERS,
            method="GET",
        )

        with urllib.request.urlopen(
            request,
            timeout=REQUEST_TIMEOUT[0],
        ) as response:

            status = response.getcode()

            if status != 200:

                raise RuntimeError(f"NSE RSS HTTP {status}")

            content_type = response.headers.get("Content-Type", "").lower()

            if "xml" not in content_type and "rss" not in content_type:

                # Don't fail immediately.
                # Some servers incorrectly return text/plain.
                pass

            data = response.read()

            if not data:

                raise RuntimeError("Empty RSS response received.")

            return data

    # ======================================================
    # Parse
    # ======================================================

    def _parse(self, xml_data):
        """Parse RSS XML.

        Parameters
        ----------
        xml_data : bytes

        Returns
        -------
        list[dict]
        """

        events = []

        root = ET.fromstring(xml_data)

        channel = root.find("channel")

        if channel is None:

            return events

        for item in channel.findall("item"):

            try:

                event = self._build_event(item)

                if event is None:

                    continue

                if not self._validate_event(event):

                    continue

                events.append(event)

            except Exception:

                # Never stop parsing because
                # one item is malformed.
                continue

        return events

    # ======================================================
    # Build Event
    # ======================================================

    def _build_event(self, item):
        """Build one canonical adapter event from an RSS item.

        Parameters
        ----------
        item : xml.etree.ElementTree.Element

        Returns
        -------
        dict | None
        """

        title = self._safe_text(item.find("title"))

        description = self._safe_text(item.find("description"))

        link = self._safe_text(item.find("link"))

        guid = self._safe_text(item.find("guid"))

        category = self._safe_text(item.find("category"))

        pub_date = self._safe_text(item.find("pubDate"))

        published_at = self._parse_datetime(pub_date)

        event = {
            # ------------------------------------------
            # Identity
            # ------------------------------------------
            "id": guid if guid else link,
            "source": self.SOURCE_NAME,
            "category": category,
            # ------------------------------------------
            # Content
            # ------------------------------------------
            "title": title,
            "summary": description,
            "link": link,
            # ------------------------------------------
            # Metadata
            # ------------------------------------------
            "published_at": published_at,
            "received_at": datetime.now(),
            "symbol": None,
            "priority": "UNKNOWN",
            "language": "EN",
            # ------------------------------------------
            # Original RSS Item
            # ------------------------------------------
            "raw": {
                "title": title,
                "description": description,
                "link": link,
                "guid": guid,
                "category": category,
                "pubDate": pub_date,
            },
        }

        return event

    # ======================================================
    # Validate Event
    # ======================================================

    def _validate_event(self, event):
        """Validate canonical adapter event.

        Parameters
        ----------
        event : dict

        Returns
        -------
        bool
        """

        if not isinstance(event, dict):
            return False

        required_fields = (
            "id",
            "source",
            "title",
            "link",
            "published_at",
        )

        for field in required_fields:

            value = event.get(field)

            if value is None:
                return False

            if isinstance(value, str):

                if not value.strip():
                    return False

        return True

    # ======================================================
    # Helpers
    # ======================================================

    def _parse_datetime(self, value):
        """Parse RSS datetime.

        Parameters
        ----------
        value : str

        Returns
        -------
        datetime | None
        """

        if not value:

            return None

        try:

            return parsedate_to_datetime(value)

        except Exception:

            return None

    # ------------------------------------------------------

    @staticmethod
    def _safe_text(element):
        """Safely extract XML text.

        Parameters
        ----------
        element : xml.etree.ElementTree.Element

        Returns
        -------
        str
        """

        if element is None:

            return ""

        if element.text is None:

            return ""

        return element.text.strip()

    # ======================================================
    # Metadata
    # ======================================================

    def __repr__(self):

        return (
            f"<NSEAdapter "
            f"connected={self.connected()} "
            f"healthy={self.healthy()} "
            f"polls={self.statistics()['polls']}>"
        )

    # ------------------------------------------------------

    def source_url(self):
        """Returns the configured RSS source.

        Returns
        -------
        str
        """

        return self.RSS_URL

    # ------------------------------------------------------

    def adapter_version(self):
        """Adapter implementation version."""

        return "1.0.0"

    # ------------------------------------------------------

    def capabilities(self):
        """Adapter capability declaration.

        This allows future collectors to discover
        adapter functionality without hardcoding.

        Returns
        -------
        dict
        """

        return {
            "rss": True,
            "json": False,
            "xml": True,
            "html": False,
            "authentication": False,
            "streaming": False,
            "supports_symbol_detection": False,
            "supports_incremental_polling": False,
        }

    # ======================================================
    # Diagnostics
    # ======================================================

    def diagnostics(self):
        """Complete adapter diagnostics.

        Useful for future dashboard /
        Telegram admin commands.

        Returns
        -------
        dict
        """

        return {
            "adapter": self.adapter_name(),
            "source": self.source_name(),
            "version": self.adapter_version(),
            "url": self.source_url(),
            "health": self.health(),
            "statistics": self.statistics(),
            "capabilities": self.capabilities(),
        }