"""
==========================================================
News Normalizer

Institutional Grade ORB Auto Trading Bot

Responsibilities
----------------
• Normalize news from all adapters
• Produce canonical news events
• Validate mandatory fields
• Ensure downstream compatibility

Never
-----
• Download news
• Classify news
• Calculate impact
• Make trading decisions
==========================================================
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime


class NewsNormalizer:
    """
    News Normalizer

    Flow
    ----
    Raw Adapter Event
            ↓
        Validate
            ↓
        Normalize
            ↓
     Canonical Event
    """

    # ======================================================
    # Canonical Schema
    # ======================================================

    REQUIRED_FIELDS = (
        "id",
        "source",
        "title",
        "link",
        "published_at",
    )

    # ======================================================

    def __init__(self):
        self.events_processed = 0
        self.events_normalized = 0
        self.events_rejected = 0
        self.last_processed = None

    # ======================================================
    # Public API
    # ======================================================

    def normalize(
        self,
        event,
    ):
        """
        Normalize one adapter event.

        Parameters
        ----------
        event : dict

        Returns
        -------
        dict | None
        """
        self.events_processed += 1
        self.last_processed = datetime.now()

        if not self.validate(event):
            self.events_rejected += 1
            return None

        normalized = deepcopy(event)
        self.events_normalized += 1

        return normalized

    # ======================================================
    # Validation
    # ======================================================

    def validate(
        self,
        event,
    ):
        """
        Validate adapter event.

        Parameters
        ----------
        event : dict

        Returns
        -------
        bool
        """
        if not isinstance(event, dict):
            return False

        for field in self.REQUIRED_FIELDS:
            if field not in event:
                return False

            value = event[field]

            if value is None:
                return False

            if isinstance(value, str):
                if not value.strip():
                    return False

        return True

    # ======================================================
    # Statistics
    # ======================================================

    def statistics(
        self,
    ):
        """
        Return normalizer statistics.

        Returns
        -------
        dict
        """
        return {
            "events_processed": self.events_processed,
            "events_normalized": self.events_normalized,
            "events_rejected": self.events_rejected,
            "last_processed": self.last_processed,
        }

    # ======================================================
    # Reset
    # ======================================================

    def reset(
        self,
    ):
        """
        Reset runtime statistics.
        """
        self.events_processed = 0
        self.events_normalized = 0
        self.events_rejected = 0
        self.last_processed = None