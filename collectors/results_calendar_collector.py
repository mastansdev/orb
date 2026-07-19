"""
==========================================================
Results Calendar Collector (BSE)
==========================================================

Auto-populates the Results Calendar from the official
BSE corporate results calendar (next two weeks).

Matching policy (v4 — mapped to REAL BSE fields)
------------------------------------------------
Confirmed BSE resultCalendar() row shape:

    scrip_Code   = '532762'
    short_name   = 'ACE'                 ← the ticker
    Long_Name    = 'Action Construction Equipment Ltd'
    meeting_date = '20 Jul 2026'         ← '%d %b %Y'
    URL          = 'https://...'

Two hard rules, because wrong data is worse than none:

1. NAME: match short_name DIRECTLY against the universe
   (it is the ticker). Fall back to exact normalized
   Long_Name match. No fuzzy matching.

2. DATE: parsed strictly from meeting_date; only accepted
   inside the query window (yesterday..+30d). If it does
   not parse → the row is SKIPPED. Never guessed.

Self-diagnostic: prints row keys + a sample of parsed
(symbol → date) on every fetch.

Run: py tools/bse_calendar_probe.py  to dump raw BSE rows.

Author : H&M ORB AUTO TRADER
==========================================================
"""

import re
from datetime import datetime, timedelta


class ResultsCalendarCollector:

    LOOKAHEAD_DAYS = 14

    # BSE's confirmed date field (with fallbacks)
    DATE_KEYS = (
        "meeting_date", "Meeting_Date", "MEETING_DATE",
        "meetingDate", "date", "Date",
    )

    # Ticker field (short_name) and full-name field
    TICKER_KEYS = (
        "short_name", "Short_Name", "SHORT_NAME",
        "scrip_name", "ScripName",
    )
    LONGNAME_KEYS = (
        "Long_Name", "long_name", "LONG_NAME",
        "company", "Company", "companyname",
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

        self._name_map = {}     # normalized company name → symbol
        self._symbol_set = set()  # exact tickers in universe
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
            self._symbol_set.add(symbol.upper())

            company_name = profile.get("company_name", "")
            if company_name:
                normalized = self._normalize(company_name)
                if len(normalized) >= 4:
                    self._name_map[normalized] = symbol
            self._name_map[symbol.upper()] = symbol

        if self._symbol_set:
            print(
                f"[CALENDAR] Universe map: "
                f"{len(self._symbol_set)} tickers, "
                f"{len(self._name_map)} names"
            )

    # --------------------------------------------------

    def resolve(self, ticker, long_name):
        """
        Resolve a BSE row to a universe symbol.
        1. short_name IS the ticker → direct exact match.
        2. else exact normalized Long_Name match.
        Never fuzzy. Returns symbol or None.
        """
        # 1. Ticker (short_name) direct
        t = str(ticker or "").strip().upper()
        if t and t in self._symbol_set:
            return t

        # 2. Long name exact-normalized
        normalized = self._normalize(long_name)
        if normalized:
            symbol = self._name_map.get(normalized)
            if symbol:
                return symbol
            compact = normalized.replace(" ", "")
            symbol = self._name_map.get(compact)
            if symbol:
                return symbol

        return None

    # Back-compat alias (tests / callers)
    def resolve_symbol(self, raw_name):
        return self.resolve(raw_name, raw_name)

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

        parsed = None

        # Full string first (handles '20 Jul 2026',
        # '2026-07-20', '20-07-2026', ISO, etc.)
        for fmt in self.DATE_FORMATS:
            try:
                parsed = datetime.strptime(raw[:20], fmt)
                break
            except ValueError:
                continue

        # Then the leading token (handles trailing time)
        if parsed is None:
            token = raw.split("T")[0].split(" ")[0]
            for fmt in self.DATE_FORMATS:
                try:
                    parsed = datetime.strptime(token, fmt)
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

            # Date field: known BSE key first, else detect
            date_key = None
            for key in self.DATE_KEYS:
                if isinstance(rows[0], dict) and key in rows[0]:
                    date_key = key
                    break
            if date_key is None:
                date_key = self._detect_date_key(rows)

            if date_key is None:
                print(
                    "[CALENDAR] ⚠ No date field found — "
                    "refusing to guess. Run "
                    "tools/bse_calendar_probe.py and share "
                    "the output."
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

                # DATE — strictly from the date field
                event_date = self._parse_date(
                    row.get(date_key)
                )
                if not event_date:
                    self.rows_no_date += 1
                    continue

                # NAME — short_name (ticker) then Long_Name
                ticker = ""
                for key in self.TICKER_KEYS:
                    if row.get(key):
                        ticker = str(row[key])
                        break

                long_name = ""
                for key in self.LONGNAME_KEYS:
                    if row.get(key):
                        long_name = str(row[key])
                        break

                symbol = self.resolve(ticker, long_name)
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
