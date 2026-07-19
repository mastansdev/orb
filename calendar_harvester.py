"""
==========================================================
Calendar Harvester
==========================================================

Mission
-------
Auto-populate the Results Calendar from the news flow.

BSE/NSE board-meeting intimations follow recognizable
headline patterns:

    "Board Meeting Intimation for Quarterly Results"
    "... board meeting scheduled on July 25, 2026 ..."
    "... Board Meeting on 25/07/2026 to consider ..."
    "... meeting of the Board ... on 25-Jul-2026 ..."

This module extracts (symbol, date) pairs from stories
whose headlines look like board-meeting/results
intimations and feeds them into the Results Calendar —
so the "no new risk into binary events" protection
maintains itself.

This module NEVER:
    • fetches anything
    • blocks trades itself (the calendar does)

Author : H&M ORB AUTO TRADER
==========================================================
"""

import re
from datetime import datetime


class CalendarHarvester:

    # Headline must look like a board-meeting /
    # results intimation
    TRIGGER = re.compile(
        r"board\s+meeting|meeting\s+of\s+the\s+board"
        r"|results?\s+(?:on|date|intimation)"
        r"|financial\s+results",
        re.IGNORECASE,
    )

    MONTHS = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4,
        "may": 5, "jun": 6, "jul": 7, "aug": 8,
        "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }

    # "25 July 2026" / "July 25, 2026" / "25-Jul-2026"
    DATE_WORDY = re.compile(
        r"(?:(\d{1,2})(?:st|nd|rd|th)?[\s\-/]*)?"
        r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
        r"[a-z]*[\s\-/,]+(\d{1,2})?(?:st|nd|rd|th)?"
        r"[\s\-/,]*(\d{4})",
        re.IGNORECASE,
    )

    # "25/07/2026" or "25-07-2026"
    DATE_NUMERIC = re.compile(
        r"\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b"
    )

    def __init__(self, results_calendar):
        self.results_calendar = results_calendar
        self.harvested = 0

    # --------------------------------------------------

    def extract_date(self, text):
        """
        First plausible future-ish date in the text,
        as YYYY-MM-DD, or None.
        """
        if not text:
            return None

        # Wordy: day-month-year or month-day-year
        match = self.DATE_WORDY.search(text)
        if match:
            day_a, month_name, day_b, year = match.groups()
            day = day_a or day_b

            if day:
                month = self.MONTHS.get(
                    month_name.lower()[:3]
                )
                candidate = self._build(
                    year, month, day
                )
                if candidate:
                    return candidate

        # Numeric: assume DD/MM/YYYY (Indian convention)
        match = self.DATE_NUMERIC.search(text)
        if match:
            day, month, year = match.groups()
            return self._build(year, month, day)

        return None

    # --------------------------------------------------

    @staticmethod
    def _build(year, month, day):
        try:
            date = datetime(
                int(year), int(month), int(day)
            )
        except (ValueError, TypeError):
            return None

        # Sanity: within ~1 year around today
        delta_days = abs(
            (date - datetime.now()).days
        )
        if delta_days > 370:
            return None

        return date.strftime("%Y-%m-%d")

    # --------------------------------------------------

    def harvest_story(self, story):
        """
        Inspect one story; add calendar entries for any
        board-meeting intimation with an extractable
        date. Returns entries added.
        """
        headline = (
            getattr(story, "name", "")
            or getattr(story, "headline", "")
            or ""
        )

        if not self.TRIGGER.search(headline):
            return 0

        # Search headline first, then notes/summary
        text_pool = headline

        for attr in ("notes", "summary", "description"):
            value = getattr(story, attr, None)
            if isinstance(value, list):
                text_pool += " " + " ".join(
                    str(v) for v in value
                )
            elif value:
                text_pool += " " + str(value)

        event_date = self.extract_date(text_pool)

        if not event_date:
            return 0

        symbols = (
            getattr(story, "affected_symbols", None)
            or []
        )
        if isinstance(symbols, str):
            symbols = [symbols]

        added = 0

        for symbol in symbols:
            if not symbol:
                continue

            if self.results_calendar.add(
                symbol, event_date, "BOARD_MEETING"
            ):
                added += 1
                self.harvested += 1
                print(
                    f"[CALENDAR] Harvested: {symbol} "
                    f"board meeting {event_date}"
                )

        return added
