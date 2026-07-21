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

    # BSE's confirmed date field (with fallbacks).
    # "bm_date" added 2026-07-21 -- NSE's boardMeetings() field
    # (confirmed via the nse package's sample response), used by
    # NseResultsCalendarCollector below which inherits this list.
    DATE_KEYS = (
        "meeting_date", "Meeting_Date", "MEETING_DATE",
        "meetingDate", "date", "Date", "bm_date",
    )

    # Ticker field (short_name) and full-name field.
    # "bm_symbol"/"sm_name" added 2026-07-21 for the NSE collector
    # (confirmed field names from nse package sample response).
    TICKER_KEYS = (
        "short_name", "Short_Name", "SHORT_NAME",
        "scrip_name", "ScripName", "bm_symbol",
    )
    LONGNAME_KEYS = (
        "Long_Name", "long_name", "LONG_NAME",
        "company", "Company", "companyname", "sm_name",
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


# ==========================================================
# NSE Results Calendar Collector (added 2026-07-21)
# ==========================================================
#
# Second, independent source for the same calendar. BSE's
# own results-calendar fetch (above) has been observed
# failing to connect (HTTPSConnectionPool / max retries) --
# suspected IP-level blocking on cloud/datacenter origins,
# though this has only been confirmed from a cloud sandbox
# so far, not from the machine that actually runs the bot.
# Rather than guess at a fix for BSE, this adds NSE's own
# official board-meetings feed as a genuinely separate
# source, using the `nse` package (BennyThadikaran/
# NseIndiaApi on GitHub, pip install nse). Both collectors
# run and both feed the SAME results_calendar -- neither is
# a fallback that masks the other being broken; either one
# working is enough to keep the watchlist alive, and if both
# work, that's cross-confirmation.
#
# Confirmed real NSE.boardMeetings() row shape (from the
# package's own sample response, not guessed):
#   bm_symbol  = 'SIYSIL'                      <- ticker
#   sm_name    = 'Siyaram Silk Mills Limited'  <- full name
#   bm_date    = '30-Oct-2023'                 <- '%d-%b-%Y'
#   bm_purpose = 'SIYARAM SILK MILLS LIMITED has informed
#                 the Exchange about Board Meeting ... to
#                 consider and approve the Quarterly
#                 Unaudited Financial results ...'
#
# Extra filter BSE's feed doesn't need: NSE's board-meetings
# list includes meetings for OTHER purposes too (buybacks,
# fundraising, M&A, etc.) alongside results. bm_purpose is
# checked for a results-shaped keyword before a row is
# accepted -- otherwise a buyback-only board meeting would
# wrongly freeze a stock under the results binary-event
# block. Never guessed: if bm_purpose doesn't clearly say
# "results", the row is skipped, not assumed.
# ==========================================================

class NseResultsCalendarCollector(ResultsCalendarCollector):

    RESULTS_PURPOSE_KEYWORDS = (
        "financial result",
        "quarterly result",
        "unaudited financial",
        "audited financial",
        "annual result",
    )

    def fetch(self):
        try:
            from nse import NSE
        except ImportError:
            print(
                "[CALENDAR-NSE] nse package unavailable "
                "(pip install nse)"
            )
            return 0

        added = 0
        self.rows_seen = 0
        self.rows_no_date = 0
        self.rows_no_match = 0

        try:
            # server=False: this collector runs as part of the
            # Engine, which runs locally (market_data.py on the
            # machine actually trading) -- not on Railway. If
            # that ever changes, flip this to True to use the
            # package's cloud-friendly session handling (httpx).
            with NSE(download_folder=".", server=False) as nse:
                rows = nse.boardMeetings(
                    index="equities",
                    from_date=datetime.now(),
                    to_date=(
                        datetime.now()
                        + timedelta(days=self.LOOKAHEAD_DAYS)
                    ),
                )

            if not rows:
                print("[CALENDAR-NSE] NSE returned 0 rows")
                return 0

            if isinstance(rows[0], dict):
                print(
                    f"[CALENDAR-NSE] NSE row keys: "
                    f"{list(rows[0].keys())}"
                )

            samples = []
            skipped_purpose = 0

            for row in rows:
                if not isinstance(row, dict):
                    continue
                self.rows_seen += 1

                # PURPOSE FILTER — NSE-specific, see class
                # docstring. Skip anything not clearly a
                # results-related board meeting.
                #
                # Fix (2026-07-21, after seeing REAL live rows
                # via tools/nse_calendar_probe.py): NSE files
                # each board meeting as MULTIPLE rows -- one
                # generically tagged bm_purpose="Board Meeting
                # Intimation", and often a second more specific
                # one tagged bm_purpose="Financial Results".
                # Checking bm_purpose alone missed any company
                # whose only row happened to be the generic
                # variant, even though its bm_desc explicitly
                # says "...consider and approve the Unaudited
                # Financial results...". Now checks both fields
                # combined -- still keyword-gated (a genuinely
                # unrelated board meeting, e.g. buyback-only,
                # still gets skipped), just no longer blind to
                # which of NSE's two row variants carried the
                # word.
                purpose_text = (
                    str(row.get("bm_purpose", "")) + " "
                    + str(row.get("bm_desc", ""))
                ).lower()
                if not any(
                    kw in purpose_text
                    for kw in self.RESULTS_PURPOSE_KEYWORDS
                ):
                    skipped_purpose += 1
                    continue

                # DATE
                event_date = self._parse_date(
                    row.get("bm_date")
                )
                if not event_date:
                    self.rows_no_date += 1
                    continue

                # NAME — bm_symbol (ticker) then sm_name
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

            # Enforce one-date-per-symbol after bulk add
            self.results_calendar.dedupe()

            self.fetched = added
            print(
                f"[CALENDAR-NSE] {self.rows_seen} rows → "
                f"{added} matched "
                f"({self.rows_no_match} outside universe, "
                f"{self.rows_no_date} no valid date, "
                f"{skipped_purpose} not results-related)"
            )
            if samples:
                print(
                    f"[CALENDAR-NSE] Sample: "
                    f"{', '.join(samples)}"
                )

        except Exception as e:
            print(
                f"[CALENDAR-NSE] NSE fetch failed: "
                f"{str(e)[:150]}"
            )

        return added
