"""
==========================================================
Results Calendar Collector (BSE)
==========================================================

Auto-populates the Results Calendar from the official
BSE corporate results calendar (next two weeks).

Matching policy (v3 — STRICT + NO GUESSING)
-------------------------------------------
Two hard rules, because wrong data is worse than no data:

1. NAME: resolved by EXACT normalized company-name match
   against the master universe. No fuzzy matching.

2. DATE: taken ONLY from a field that actually parses as
   a date. NEVER guessed from arbitrary row text (that
   was the bug that scattered companies onto wrong days).
   If no field parses as a date → the row is SKIPPED.

The date field is AUTO-DETECTED per feed: the collector
finds which column consistently parses as dates and uses
only that one.

Self-diagnostic: on every fetch it prints the row keys
and a sample of parsed (symbol, date, source-field) so
the structure is visible on the first real run.

Run: py tools/bse_calendar_probe.py  to dump raw BSE rows.

Author : H&M ORB AUTO TRADER
==========================================================
"""

import re
from datetime import datetime, timedelta


class ResultsCalendarCollector:

    LOOKAHEAD_DAYS = 14

    NAME_KEYS = (
        "short_name", "Short_Name", "SHORT_NAME",
        "long_name", "Long_Name", "LONG_NAME",
        "scrip_name", "ScripName", "SCRIP_NAME",
        "company", "Company", "COMPANY",
        "companyname", "CompanyName", "Company_Name",
        "sc_name", "SC_NAME", "name", "Name",
    )

    SUFFIX_TOKENS = (
        "LIMITED", "LTD", "LTD.", "CO", "CO.",
        "CORPORATION", "CORP", "COMPANY", "INDIA",
        "(INDIA)", "INDIA)", "(INDIA", "INDUSTRIES",
        "INDS", "THE",
    )

    DATE_FORMATS = (
        "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y",
        "%d %b %Y", "%d-%b-%Y", "%d %B %Y",
        "%Y%m%d", "%m/%d/%Y", "%d.%m.%Y",
        "%Y-%m-%dT%H:%M:%S",
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
        self.rows_no_date = 0
        self.rows_no_match = 0

        self._name_map = {}
        self._build_name_map()

    # --------------------------------------------------

    def _normalize(self, name):
        name = re.sub(r"[^A-Z0-9 ]", " ", str(name).upper())
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
            self._name_map[symbol.upper()] = symbol

        if self._name_map:
            print(
                f"[CALENDAR] Strict name map: "
                f"{len(self._name_map)} entries"
            )

    # --------------------------------------------------

    def resolve_symbol(self, raw_name):
        if not raw_name:
            return None

        normalized = self._normalize(raw_name)
        if not normalized:
            return None

        symbol = self._name_map.get(normalized)
        if symbol:
            return symbol

        compact = normalized.replace(" ", "")
        return self._name_map.get(compact)

    # --------------------------------------------------

    def _parse_date(self, value):
        """
        Return YYYY-MM-DD only if `value` genuinely parses
        as a date IN or NEAR the query window. Otherwise
        None. Never invents a date.
        """
        if value is None:
            return None

        raw = str(value).strip()
        if len(raw) < 6:
            return None

        # Try each known format on the leading date token
        candidate = raw.split("T")[0].split(" ")[0] \
            if ("T" in raw or " " in raw) else raw

        parsed = None
        for fmt in self.DATE_FORMATS:
            try:
                parsed = datetime.strptime(candidate, fmt)
                break
            except ValueError:
                continue

        if parsed is None:
            # Try the whole string for formats with spaces
            for fmt in self.DATE_FORMATS:
                try:
                    parsed = datetime.strptime(raw[:20], fmt)
                    break
                except ValueError:
                    continue

        if parsed is None:
            return None

        # Sanity: must be within a sane window of the query
        # (yesterday .. +30 days). Rejects record dates,
        # query echoes, and stray far-off dates.
        today = datetime.now().date()
        if not (
            today - timedelta(days=2)
            <= parsed.date()
            <= today + timedelta(days=30)
        ):
            return None

        return parsed.strftime("%Y-%m-%d")

    # --------------------------------------------------

    def _detect_date_key(self, rows):
        """
        Find which column most consistently parses as a
        valid in-window date. That is THE date field —
        no other column is trusted for dates.
        """
        if not rows or not isinstance(rows[0], dict):
            return None

        scores = {}
        sample = rows[:40]

        for key in rows[0].keys():
            hits = 0
            for row in sample:
                if self._parse_date(row.get(key)):
                    hits += 1
            if hits:
                scores[key] = hits

        if not scores:
            return None

        best = max(scores, key=scores.get)
        print(
            f"[CALENDAR] Date field auto-detected: "
            f"'{best}' ({scores[best]}/{len(sample)} "
            f"rows parsed)"
        )
        return best

    # --------------------------------------------------

    def fetch(self):
        try:
            from bse import BSE
        except ImportError:
            print("[CALENDAR] bse package unavailable")
            return 0

        added = 0
        self.rows_seen = 0
        self.rows_no_date = 0
        self.rows_no_match = 0

        try:
            bse = BSE(download_folder=".")

            rows = bse.resultCalendar(
                from_date=datetime.now(),
                to_date=(
                    datetime.now()
                    + timedelta(days=self.LOOKAHEAD_DAYS)
                ),
            )

            if not rows:
                print("[CALENDAR] BSE returned 0 rows")
                try:
                    bse.exit()
                except Exception:
                    pass
                return 0

            # Self-diagnostic: show real structure once
            if isinstance(rows[0], dict):
                print(
                    f"[CALENDAR] BSE row keys: "
                    f"{list(rows[0].keys())}"
                )

            # Auto-detect THE date field (no guessing)
            date_key = self._detect_date_key(rows)

            if date_key is None:
                print(
                    "[CALENDAR] ⚠ No parseable date field "
                    "found — refusing to guess. Run "
                    "tools/bse_calendar_probe.py and share "
                    "the output so the field can be mapped."
                )
                try:
                    bse.exit()
                except Exception:
                    pass
                return 0

            samples = []

            for row in rows:
                if not isinstance(row, dict):
                    continue
                self.rows_seen += 1

                # DATE — strictly from the detected field
                event_date = self._parse_date(
                    row.get(date_key)
                )
                if not event_date:
                    self.rows_no_date += 1
                    continue

                # NAME — strict exact match
                raw_name = ""
                for key in self.NAME_KEYS:
                    if row.get(key):
                        raw_name = str(row[key])
                        break

                symbol = self.resolve_symbol(raw_name)
                if symbol is None:
                    self.rows_no_match += 1
                    continue

                if self.results_calendar.add(
                    symbol, event_date, "RESULTS"
                ):
                    added += 1
                    if len(samples) < 8:
                        samples.append(
                            f"{symbol}→{event_date}"
                        )

            try:
                bse.exit()
            except Exception:
                pass

            # Enforce one-date-per-symbol after bulk add
            self.results_calendar.dedupe()

            self.fetched = added
            print(
                f"[CALENDAR] {self.rows_seen} rows → "
                f"{added} matched "
                f"({self.rows_no_match} outside universe, "
                f"{self.rows_no_date} no valid date)"
            )
            if samples:
                print(
                    f"[CALENDAR] Sample: "
                    f"{', '.join(samples)}"
                )

        except Exception as e:
            print(
                f"[CALENDAR] BSE fetch failed: "
                f"{str(e)[:150]}"
            )

        return added
