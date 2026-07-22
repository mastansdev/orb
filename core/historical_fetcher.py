"""
==========================================================
Historical Data Fetcher
==========================================================

Mission
-------
Actually USE the "Historical Data for 5 Years" and minute-
level historical data you already pay Dhan for monthly.

Before this (2026-07-22): the only historical call anywhere
in the bot was core/historical_data.py's get_orb(), which
only ever asks Dhan for TODAY's data, to preload the opening
range. The 5-year daily/minute history was being paid for
and never touched -- confirmed by grepping the whole codebase
for any other historical call and finding none.

This module is step 1 only: fetch real historical bars (daily
or minute-level, per Dhan's v2 API, which documents up to 5
years for both -- the installed SDK's own docstring is stale
on this, see .agents/skills/dhanhq/references/market-data.md)
and cache them locally so repeated backtesting work doesn't
re-hit the API every time.

This module deliberately does NOT:
    - touch the live engine or any live trading path
    - place or manage orders
    - decide anything

It only fetches and caches bars. The actual ORB-strategy
backtest (replaying these bars through the real ORB/risk/
dynamic-trade-manager logic to compare 1:1 vs 1:2 vs the
true-trailing-runner mode) is deliberately scoped as a
separate, dedicated piece of work -- not squeezed in here
right as markets open.

Author : H&M ORB AUTO TRADER
==========================================================
"""

import os
import time
import json
from datetime import date, datetime, timedelta

from dotenv import load_dotenv
from dhanhq import DhanContext, dhanhq


CACHE_DIR = "data/historical_cache"


class HistoricalFetcher:

    # Same throttle pattern already proven live in
    # core/historical_data.py's preload_orb() -- ~2.85
    # req/sec. Dhan's documented hard limit is on the LIVE
    # quote endpoint (1 req/sec); this historical/intraday
    # endpoint is a separate one, but there's no published
    # rate limit for it in the reference docs, so reusing
    # the same conservative, already-working throttle is
    # the safe default rather than guessing a faster one.
    REQUEST_DELAY_SECONDS = 0.35

    def __init__(self, cache_dir=CACHE_DIR):
        load_dotenv()

        context = DhanContext(
            os.getenv("DHAN_CLIENT_ID"),
            os.getenv("DHAN_ACCESS_TOKEN"),
        )
        self.dhan = dhanhq(context)

        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

        self._last_request_time = 0.0

    # --------------------------------------------------

    def _throttle(self):
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.REQUEST_DELAY_SECONDS:
            time.sleep(self.REQUEST_DELAY_SECONDS - elapsed)
        self._last_request_time = time.time()

    # --------------------------------------------------

    def _cache_path(self, kind, security_id, from_date, to_date, interval=None):
        # Fix (2026-07-22): from_date/to_date can carry "HH:MM:SS"
        # (the minute-history path passes full timestamps) --
        # Windows/NTFS rejects ":" in filenames outright, which
        # silently failed EVERY cache write on Windows (Errno 22)
        # and forced a full re-fetch on every single run. Strip
        # anything that isn't safe across Windows/Linux/Mac.
        def _sanitize(s):
            return (
                str(s).replace(":", "").replace(" ", "_")
            )

        suffix = f"_{interval}m" if interval else ""
        fname = (
            f"{kind}_{security_id}_"
            f"{_sanitize(from_date)}_{_sanitize(to_date)}"
            f"{suffix}.json"
        )
        return os.path.join(self.cache_dir, fname)

    def _read_cache(self, path):
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _write_cache(self, path, data):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"[HIST_FETCH] cache write failed ({path}): {e}")

    # --------------------------------------------------
    # Daily bars (up to 5 years, per v2 API docs)
    # --------------------------------------------------

    def get_daily_history(
        self,
        security_id,
        years=5,
        exchange_segment="NSE_EQ",
        instrument_type="EQUITY",
        use_cache=True,
    ):
        """
        Daily OHLCV bars for one symbol, up to `years` back
        from today. Returns a dict of parallel lists
        (open/high/low/close/volume/timestamp) or None on
        failure -- never raises.
        """
        to_date = date.today()
        from_date = to_date - timedelta(days=int(years * 365.25))

        from_str = from_date.strftime("%Y-%m-%d")
        to_str = to_date.strftime("%Y-%m-%d")

        cache_path = self._cache_path(
            "daily", security_id, from_str, to_str
        )

        if use_cache:
            cached = self._read_cache(cache_path)
            if cached is not None:
                return cached

        self._throttle()

        try:
            response = self.dhan.historical_daily_data(
                security_id=str(security_id),
                exchange_segment=exchange_segment,
                instrument_type=instrument_type,
                from_date=from_str,
                to_date=to_str,
                expiry_code=0,
                oi=False,
            )
        except Exception as e:
            print(
                f"[HIST_FETCH] daily history request failed for "
                f"{security_id}: {e}"
            )
            return None

        if response.get("status") != "success":
            print(
                f"[HIST_FETCH] daily history FAILED for "
                f"{security_id}: {response.get('remarks', 'N/A')}"
            )
            return None

        data = response.get("data", {})
        if not data.get("open"):
            return None

        self._write_cache(cache_path, data)
        return data

    # --------------------------------------------------
    # Minute bars (v2 API docs: up to 5 years for active
    # instruments -- NOT "today only", despite the installed
    # SDK's stale docstring; see reference/market-data.md)
    # --------------------------------------------------

    def get_minute_history(
        self,
        security_id,
        from_date,
        to_date,
        interval=15,
        exchange_segment="NSE_EQ",
        instrument_type="EQUITY",
        use_cache=True,
        chunk_days=60,
    ):
        """
        Minute-level OHLCV bars for one symbol over an
        arbitrary historical date range (datetime or
        "YYYY-MM-DD HH:MM:SS" strings).

        chunk_days: requests are split into chunks of this
        many calendar days each. This is a defensive default,
        NOT a documented Dhan limit -- the reference docs
        don't state a per-call cap for this endpoint (unlike
        expired_options_data, which is explicitly capped at
        30 days/call). Splitting anyway avoids one oversized
        request timing out or silently truncating on a multi-
        year pull, at the cost of more, smaller, throttled
        calls.

        Returns a single merged dict of parallel lists, or
        None if every chunk failed.
        """
        if isinstance(from_date, str):
            from_dt = datetime.strptime(
                from_date[:10], "%Y-%m-%d"
            )
        else:
            from_dt = from_date

        if isinstance(to_date, str):
            to_dt = datetime.strptime(to_date[:10], "%Y-%m-%d")
        else:
            to_dt = to_date

        merged = {
            "open": [], "high": [], "low": [],
            "close": [], "volume": [], "timestamp": [],
        }
        any_success = False

        chunk_start = from_dt
        while chunk_start <= to_dt:
            chunk_end = min(
                chunk_start + timedelta(days=chunk_days), to_dt
            )

            from_str = chunk_start.strftime("%Y-%m-%d 09:15:00")
            to_str = chunk_end.strftime("%Y-%m-%d 15:30:00")

            cache_path = self._cache_path(
                "minute", security_id, from_str, to_str, interval
            )

            chunk_data = (
                self._read_cache(cache_path) if use_cache else None
            )

            if chunk_data is None:
                self._throttle()
                try:
                    response = self.dhan.intraday_minute_data(
                        security_id=str(security_id),
                        exchange_segment=exchange_segment,
                        instrument_type=instrument_type,
                        from_date=from_str,
                        to_date=to_str,
                        interval=interval,
                    )
                except Exception as e:
                    print(
                        f"[HIST_FETCH] minute chunk failed for "
                        f"{security_id} ({from_str}..{to_str}): {e}"
                    )
                    chunk_start = chunk_end + timedelta(days=1)
                    continue

                if response.get("status") != "success":
                    print(
                        f"[HIST_FETCH] minute chunk FAILED for "
                        f"{security_id}: "
                        f"{response.get('remarks', 'N/A')}"
                    )
                    chunk_start = chunk_end + timedelta(days=1)
                    continue

                chunk_data = response.get("data", {})
                if chunk_data.get("open"):
                    self._write_cache(cache_path, chunk_data)

            if chunk_data and chunk_data.get("open"):
                any_success = True
                for key in merged:
                    merged[key].extend(chunk_data.get(key, []))

            chunk_start = chunk_end + timedelta(days=1)

        return merged if any_success else None
