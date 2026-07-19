"""
==========================================================
Results Calendar
==========================================================

Mission
-------
Know the scheduled binary events BEFORE they happen.

The institutional rule this module enforces:

    No NEW risk into a binary event.

A stock reporting results today is a coin flip with a
gap risk attached — the system should not initiate
fresh intraday positions on it.

Sources
-------
1. Masterdata/results_calendar.csv  (SYMBOL,DATE[,TYPE])
   — maintained manually or by future collectors
2. Board-meeting announcements recorded as structured
   events (future enrichment)

Storage: results_calendar table in institutional memory,
so entries survive restarts and accumulate history.

This module NEVER:
    • trades
    • fetches data over the network

Author : H&M ORB AUTO TRADER
==========================================================
"""

import csv
import os
from datetime import datetime, timedelta

from intelligence.evidence import Evidence


class ResultsCalendar:

    CSV_FILE = os.path.join(
        "Masterdata", "results_calendar.csv"
    )

    def __init__(self, repository=None):
        self.repository = repository

        # date(str) → set of symbols
        self._calendar = {}

        self._ensure_table()
        self._load_from_db()
        self._load_from_csv()

        # Self-heal legacy corruption on every startup
        self.dedupe()

    # --------------------------------------------------

    def _ensure_table(self):
        if self.repository is None:
            return

        try:
            with self.repository._lock:
                self.repository.cursor.execute("""
                CREATE TABLE IF NOT EXISTS results_calendar(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    event_date TEXT,
                    event_type TEXT,
                    UNIQUE(symbol, event_date, event_type)
                )
                """)
                self.repository.db.commit()
        except Exception as e:
            print(f"[CALENDAR] Table init failed: {e}")

    # --------------------------------------------------

    def _load_from_db(self):
        if self.repository is None:
            return

        try:
            cutoff = (
                datetime.now() - timedelta(days=2)
            ).strftime("%Y-%m-%d")

            with self.repository._lock:
                self.repository.cursor.execute(
                    """
                    SELECT symbol, event_date
                    FROM results_calendar
                    WHERE event_date >= ?
                    """,
                    (cutoff,),
                )
                rows = self.repository.cursor.fetchall()

            for symbol, event_date in rows:
                self._calendar.setdefault(
                    event_date, set()
                ).add(symbol)

        except Exception as e:
            print(f"[CALENDAR] DB load failed: {e}")

    # --------------------------------------------------

    def _load_from_csv(self):
        """
        Optional operator-maintained CSV:
        SYMBOL,DATE[,TYPE] with DATE as YYYY-MM-DD.
        """
        if not os.path.exists(self.CSV_FILE):
            return

        loaded = 0

        try:
            with open(
                self.CSV_FILE, newline="", encoding="utf-8"
            ) as f:
                for row in csv.reader(f):
                    if len(row) < 2:
                        continue

                    symbol = row[0].strip().upper()
                    event_date = row[1].strip()
                    event_type = (
                        row[2].strip().upper()
                        if len(row) > 2 else "RESULTS"
                    )

                    if symbol.upper() == "SYMBOL":
                        continue  # header

                    if self.add(
                        symbol, event_date, event_type
                    ):
                        loaded += 1

            if loaded:
                print(
                    f"[CALENDAR] Loaded {loaded} entries "
                    f"from CSV"
                )

        except Exception as e:
            print(f"[CALENDAR] CSV load failed: {e}")

    # --------------------------------------------------
    # PUBLIC : Maintain
    # --------------------------------------------------

    def add(self, symbol, event_date, event_type="RESULTS"):
        symbol = symbol.strip().upper()
        event_date = event_date.strip()

        try:
            datetime.strptime(event_date, "%Y-%m-%d")
        except ValueError:
            return False

        # --------------------------------------------------
        # HARD RULE: one symbol = one RESULTS date.
        # A company reports once per quarter. If this
        # symbol already has a future results date, keep
        # the EARLIER one (the scheduled board meeting)
        # and drop the rest. This kills the
        # "AIIL-on-every-day" corruption at the source.
        # --------------------------------------------------
        today = datetime.now().strftime("%Y-%m-%d")

        existing_dates = [
            d for d, syms in self._calendar.items()
            if symbol in syms and d >= today
        ]

        if existing_dates:
            keep = min(existing_dates + [event_date])

            # Remove the symbol from every other future date
            for d in existing_dates:
                if d != keep:
                    self._calendar[d].discard(symbol)
                    if not self._calendar[d]:
                        del self._calendar[d]

            self._db_remove_symbol_except(symbol, keep)

            # If an earlier date already existed, keep it
            if keep != event_date:
                return True

            event_date = keep

        self._calendar.setdefault(
            event_date, set()
        ).add(symbol)

        if self.repository is not None:
            try:
                with self.repository._lock:
                    self.repository.cursor.execute(
                        """
                        INSERT OR IGNORE INTO
                        results_calendar(
                            symbol, event_date, event_type
                        )
                        VALUES(?,?,?)
                        """,
                        (symbol, event_date, event_type),
                    )
                    self.repository.db.commit()
            except Exception:
                pass

        return True

    # --------------------------------------------------

    def _db_remove_symbol_except(self, symbol, keep_date):
        """Delete a symbol's future rows except keep_date."""
        if self.repository is None:
            return

        today = datetime.now().strftime("%Y-%m-%d")
        try:
            with self.repository._lock:
                self.repository.cursor.execute(
                    "DELETE FROM results_calendar "
                    "WHERE symbol = ? "
                    "AND event_date >= ? "
                    "AND event_date != ?",
                    (symbol, today, keep_date),
                )
                self.repository.db.commit()
        except Exception:
            pass

    # --------------------------------------------------

    def dedupe(self):
        """
        Self-heal: enforce one-date-per-symbol across
        the whole calendar (keeps earliest future date).
        Run at startup to clean legacy garbage.
        """
        today = datetime.now().strftime("%Y-%m-%d")

        symbol_dates = {}
        for date, symbols in self._calendar.items():
            if date < today:
                continue
            for symbol in symbols:
                symbol_dates.setdefault(
                    symbol, []
                ).append(date)

        cleaned = 0
        for symbol, dates in symbol_dates.items():
            if len(dates) <= 1:
                continue

            keep = min(dates)
            for date in dates:
                if date != keep:
                    self._calendar[date].discard(symbol)
                    if not self._calendar[date]:
                        del self._calendar[date]
                    cleaned += 1

            self._db_remove_symbol_except(symbol, keep)

        if cleaned:
            print(
                f"[CALENDAR] Deduped {cleaned} duplicate "
                f"symbol-dates (one company = one results "
                f"date)"
            )

        return cleaned

    # --------------------------------------------------
    # PUBLIC : Query
    # --------------------------------------------------

    def has_event_today(self, symbol):
        today = datetime.now().strftime("%Y-%m-%d")
        return symbol.upper() in self._calendar.get(
            today, set()
        )

    # --------------------------------------------------

    def upcoming(self, days=5):
        """
        {date: [symbols]} for the next N days.
        """
        result = {}
        today = datetime.now()

        for offset in range(days + 1):
            date = (
                today + timedelta(days=offset)
            ).strftime("%Y-%m-%d")

            symbols = self._calendar.get(date)

            if symbols:
                result[date] = sorted(symbols)

        return result

    # --------------------------------------------------
    # PUBLIC : Maintenance
    # --------------------------------------------------

    def clear_future(self):
        """
        Purge today-and-future entries (bad matches,
        stale data) so a strict re-fetch can rebuild
        cleanly. Past entries (performance history)
        are kept.
        """
        today = datetime.now().strftime("%Y-%m-%d")

        removed = 0
        for date in list(self._calendar.keys()):
            if date >= today:
                removed += len(self._calendar[date])
                del self._calendar[date]

        if self.repository is not None:
            try:
                with self.repository._lock:
                    self.repository.cursor.execute(
                        "DELETE FROM results_calendar "
                        "WHERE event_date >= ?",
                        (today,),
                    )
                    self.repository.db.commit()
            except Exception:
                pass

        print(
            f"[CALENDAR] Cleared {removed} future "
            f"entries"
        )
        return removed

    # --------------------------------------------------
    # PUBLIC : Evidence
    # --------------------------------------------------

    def build_evidence(self, symbol):
        """
        EVENT_RISK evidence: results today = binary
        event = no new risk.
        """
        if not self.has_event_today(symbol):
            return []

        return [
            Evidence(
                provider="EVENT_RISK",
                symbol=symbol,
                recommendation="AVOID",
                score=90,
                confidence=95,
                reason=(
                    f"{symbol} has results/board meeting "
                    f"TODAY — binary event risk"
                ),
                facts={"event": "RESULTS_TODAY"},
            )
        ]

    # --------------------------------------------------

    def report(self, days=7):
        """
        Week-ahead view, grouped by weekday
        (Earnings Pulse style).
        """
        upcoming = self.upcoming(days)

        if not upcoming:
            return (
                "RESULTS CALENDAR — WEEK AHEAD\n\n"
                f"No scheduled events in next {days} days.\n\n"
                "/fetchresults — pull BSE calendar\n"
                "/calendar REFRESH — purge + refetch\n"
                "/calendar SYMBOL YYYY-MM-DD — add manually"
            )

        lines = ["📅 RESULTS — WEEK AHEAD", ""]

        today = datetime.now().strftime("%Y-%m-%d")

        for date, symbols in sorted(upcoming.items()):
            weekday = datetime.strptime(
                date, "%Y-%m-%d"
            ).strftime("%A").upper()

            marker = " ← TODAY" if date == today else ""

            lines.append(
                f"━ {weekday} {date}{marker} "
                f"({len(symbols)})"
            )

            shown = symbols[:20]
            lines.append("  " + ", ".join(shown))

            if len(symbols) > len(shown):
                lines.append(
                    f"  … +{len(symbols) - len(shown)} more"
                )

            lines.append("")

        lines.append(
            "⚠ Stocks listed TODAY are blocked from "
            "new entries (binary-event rule). Timing "
            "note: BSE publishes the DATE only — boards "
            "meet any time; announcements often land "
            "mid-session or after close, so the block "
            "covers the whole day."
        )

        return "\n".join(lines)
