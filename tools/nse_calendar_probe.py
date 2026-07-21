"""
NSE Board Meetings (Results Calendar) — Diagnostic Probe
=========================================================

Run this ON YOUR MACHINE (it needs internet + the nse
package -- pip install nse):

    py tools/nse_calendar_probe.py

Sibling to tools/bse_calendar_probe.py -- same idea, for the
second, independent calendar source added 2026-07-21
(NseResultsCalendarCollector). Prints the REAL structure of
what NSE returns, and unlike running the full bot, this exits
on its own timeline -- it isn't affected by market_data.py's
after-16:00 reconnect cutoff, so it's safe to run any time of
day to check connectivity.

This script only READS from NSE. It changes nothing.
"""

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


def main():
    print("=" * 64)
    print("  NSE BOARD MEETINGS (RESULTS CALENDAR) PROBE")
    print("=" * 64)

    try:
        from nse import NSE
    except ImportError:
        print("nse package not installed. Run: pip install nse")
        return

    try:
        nse = NSE(download_folder=".", server=False)
    except Exception as e:
        print(f"Could not start NSE client: {e}")
        return

    try:
        rows = nse.boardMeetings(
            index="equities",
            from_date=datetime.now(),
            to_date=datetime.now() + timedelta(days=14),
        )
    except Exception as e:
        print(f"boardMeetings() failed: {e}")
        try:
            nse.exit()
        except Exception:
            pass
        return

    print(f"\nTotal rows returned : {len(rows)}\n")

    if not rows:
        print("NSE returned ZERO rows. Either there are no")
        print("board meetings scheduled in this window, or")
        print("the endpoint changed. Paste this output anyway.")
        try:
            nse.exit()
        except Exception:
            pass
        return

    # 1. The KEYS (field names)
    first = rows[0]
    print("-" * 64)
    print("ROW KEYS (field names):")
    print("-" * 64)
    if isinstance(first, dict):
        for key in first.keys():
            print(f"  • {key}")
    else:
        print(f"  Rows are {type(first)}, not dicts:")
        print(f"  {first}")
        try:
            nse.exit()
        except Exception:
            pass
        return

    # 2. First 8 full rows — shows date format + purpose text
    print("\n" + "-" * 64)
    print("FIRST 8 RAW ROWS:")
    print("-" * 64)
    for i, row in enumerate(rows[:8], 1):
        print(f"\n[{i}]")
        for key, value in row.items():
            print(f"    {key} = {value!r}")

    # 3. How many rows actually look results-related, per the
    # same purpose+desc keyword filter NseResultsCalendarCollector
    # uses -- confirms the filter isn't discarding everything.
    RESULTS_PURPOSE_KEYWORDS = (
        "financial result", "quarterly result",
        "unaudited financial", "audited financial",
        "annual result",
    )
    results_like = 0
    for row in rows:
        purpose_text = (
            str(row.get("bm_purpose", "")) + " "
            + str(row.get("bm_desc", ""))
        ).lower()
        if any(kw in purpose_text for kw in RESULTS_PURPOSE_KEYWORDS):
            results_like += 1

    print("\n" + "-" * 64)
    print(
        f"Rows matching results-purpose filter: "
        f"{results_like} / {len(rows)}"
    )
    print("-" * 64)

    try:
        nse.exit()
    except Exception:
        pass

    print("\n" + "=" * 64)
    print("  COPY EVERYTHING ABOVE BACK INTO THE CHAT")
    print("=" * 64)


if __name__ == "__main__":
    main()
