"""
==========================================================
Results Calendar Collector (BSE)
==========================================================

Auto-populates the Results Calendar: fetches the
official BSE corporate results calendar for the next
two weeks and maps announcements to our 750-stock
universe by name/keyword matching.

Answers: "Which of my stocks report results this week?"
— automatically, at every bot startup.

Runs in a background thread (network must never delay
the trading startup). Failures are logged and skipped.

Author : H&M ORB AUTO TRADER
==========================================================
"""

from datetime import datetime, timedelta


class ResultsCalendarCollector:

    LOOKAHEAD_DAYS = 14

    def __init__(
        self,
        results_calendar,
        harvester=None
    ):
        self.results_calendar = results_calendar
        self.harvester = harvester
        self.fetched = 0

    # --------------------------------------------------

    def fetch(self):
        """
        Fetch BSE result calendar and populate.
        Returns entries added (0 on any failure).
        """
        try:
            from bse import BSE
        except ImportError:
            print("[CALENDAR] bse package unavailable")
            return 0

        try:
            from news.symbol_matcher import symbol_matcher
        except Exception:
            symbol_matcher = None

        added = 0

        try:
            bse = BSE(download_folder=".")

            rows = bse.resultCalendar(
                from_date=datetime.now(),
                to_date=(
                    datetime.now()
                    + timedelta(days=self.LOOKAHEAD_DAYS)
                ),
            )

            for row in rows:
                if not isinstance(row, dict):
                    continue

                text = " ".join(
                    str(v) for v in row.values()
                )

                # Date: explicit field first, else regex
                event_date = None

                for key in (
                    "meeting_date", "MeetingDate",
                    "BoardMeetingDate", "date", "Date",
                ):
                    value = row.get(key)
                    if value:
                        event_date = self._parse_date(
                            str(value)
                        )
                        if event_date:
                            break

                if not event_date and self.harvester:
                    event_date = (
                        self.harvester.extract_date(text)
                    )

                if not event_date:
                    continue

                # Symbol: via universe matcher
                symbols = []
                if symbol_matcher is not None:
                    try:
                        symbols = symbol_matcher.match(
                            text
                        ) or []
                    except Exception:
                        symbols = []

                for symbol in symbols:
                    if self.results_calendar.add(
                        symbol, event_date, "RESULTS"
                    ):
                        added += 1

            try:
                bse.exit()
            except Exception:
                pass

            self.fetched = added
            print(
                f"[CALENDAR] BSE results calendar: "
                f"{added} entries added"
            )

        except Exception as e:
            print(
                f"[CALENDAR] BSE fetch failed: "
                f"{str(e)[:120]}"
            )

        return added

    # --------------------------------------------------

    @staticmethod
    def _parse_date(value):
        value = value.strip()[:20]

        for fmt in (
            "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y",
            "%d %b %Y", "%d-%b-%Y", "%Y%m%d",
        ):
            try:
                return datetime.strptime(
                    value.split("T")[0].split(" ")[0],
                    fmt
                ).strftime("%Y-%m-%d")
            except ValueError:
                continue

        return None
