"""
==========================================================
Results Calendar Collector (BSE)
==========================================================

Auto-populates the Results Calendar from the official
BSE corporate results calendar (next two weeks).

Matching policy (v2 — STRICT)
-----------------------------
v1 text-blasted whole rows through the news keyword
matcher, which over-matched badly (one company row
matched many symbols; some symbols matched every day).

v2 matches ONLY the company-name field of each row,
via exact normalized-name comparison against the
master universe:

    "Bharat Forge Ltd"  →  BHARATFORG   (exact)
    "AIA Engineering"   →  AIAENG       (exact)
    random row text     →  NO MATCH     (skipped)

One row = one company = at most one calendar entry.

Runs in a background thread at startup; /fetchresults
and /calendar REFRESH re-run it manually.

Author : H&M ORB AUTO TRADER
==========================================================
"""

import re
from datetime import datetime, timedelta


class ResultsCalendarCollector:

    LOOKAHEAD_DAYS = 14

    # Row keys that may carry the company name
    NAME_KEYS = (
        "short_name", "Short_Name", "SHORT_NAME",
        "long_name", "Long_Name", "LONG_NAME",
        "scrip_name", "ScripName", "SCRIP_NAME",
        "company", "Company", "COMPANY",
        "companyname", "CompanyName",
    )

    # Row keys that may carry the meeting date
    DATE_KEYS = (
        "meeting_date", "MeetingDate", "MEETING_DATE",
        "BoardMeetingDate", "board_meeting_date",
        "date", "Date", "DATE", "meetingdate",
    )

    # Suffix noise stripped during name normalization
    SUFFIX_TOKENS = (
        "LIMITED", "LTD", "LTD.", "CO", "CO.",
        "CORPORATION", "CORP", "COMPANY", "INDIA",
        "(INDIA)", "INDUSTRIES", "INDS",
    )

    def __init__(
        self,
        results_calendar,
        harvester=None,
        company_intelligence=None,
    ):
        self.results_calendar = results_calendar
        self.harvester = harvester
        self.company_intelligence = company_intelligence

        self.fetched = 0
        self.rows_seen = 0
        self.rows_unmatched = 0

        # normalized company name → symbol
        self._name_map = {}
        self._build_name_map()

    # --------------------------------------------------
    # Strict name resolution
    # --------------------------------------------------

    def _normalize(self, name):
        name = re.sub(
            r"[^A-Z0-9 ]", " ", str(name).upper()
        )
        tokens = [
            t for t in name.split()
            if t not in self.SUFFIX_TOKENS
        ]
        return " ".join(tokens)

    # --------------------------------------------------

    def _build_name_map(self):
        if self.company_intelligence is None:
            return

        for symbol, profile in (
            self.company_intelligence.profiles.items()
        ):
            company_name = profile.get("company_name", "")

            if company_name:
                normalized = self._normalize(company_name)
                if len(normalized) >= 4:
                    self._name_map[normalized] = symbol

            # The symbol itself is also a valid key
            self._name_map[symbol.upper()] = symbol

        if self._name_map:
            print(
                f"[CALENDAR] Strict name map: "
                f"{len(self._name_map)} entries"
            )

    # --------------------------------------------------

    def resolve_symbol(self, raw_name):
        """
        STRICT: exact normalized match only.
        Returns symbol or None. Never guesses.
        """
        if not raw_name:
            return None

        normalized = self._normalize(raw_name)

        if not normalized:
            return None

        # 1. Exact normalized-name match
        symbol = self._name_map.get(normalized)
        if symbol:
            return symbol

        # 2. Exact symbol match (row carries the ticker)
        compact = normalized.replace(" ", "")
        symbol = self._name_map.get(compact)
        if symbol:
            return symbol

        return None

    # --------------------------------------------------
    # Fetch
    # --------------------------------------------------

    def fetch(self):
        try:
            from bse import BSE
        except ImportError:
            print("[CALENDAR] bse package unavailable")
            return 0

        added = 0
        self.rows_seen = 0
        self.rows_unmatched = 0

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

                self.rows_seen += 1

                # --- Company name (strict field access)
                raw_name = ""
                for key in self.NAME_KEYS:
                    if row.get(key):
                        raw_name = str(row[key])
                        break

                symbol = self.resolve_symbol(raw_name)

                if symbol is None:
                    self.rows_unmatched += 1
                    continue

                # --- Meeting date
                event_date = None
                for key in self.DATE_KEYS:
                    if row.get(key):
                        event_date = self._parse_date(
                            str(row[key])
                        )
                        if event_date:
                            break

                if (
                    not event_date
                    and self.harvester is not None
                ):
                    event_date = self.harvester.extract_date(
                        " ".join(
                            str(v) for v in row.values()
                        )
                    )

                if not event_date:
                    continue

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
                f"[CALENDAR] BSE calendar: "
                f"{self.rows_seen} rows → {added} matched "
                f"({self.rows_unmatched} outside universe)"
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
