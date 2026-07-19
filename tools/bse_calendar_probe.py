"""
BSE Results Calendar — Diagnostic Probe
=======================================

Run this ON YOUR MACHINE (it needs internet + the bse
package, both of which the bot already uses):

    py tools/bse_calendar_probe.py

It prints the REAL structure of what BSE returns, so the
calendar collector can be fixed against truth instead of
guesses. Copy the ENTIRE output back into the chat.

This script only READS from BSE. It changes nothing.
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
    print("  BSE RESULTS CALENDAR PROBE")
    print("=" * 64)

    try:
        from bse import BSE
    except ImportError:
        print("bse package not installed. Run: pip install bse")
        return

    try:
        bse = BSE(download_folder=".")
    except Exception as e:
        print(f"Could not start BSE client: {e}")
        return

    try:
        rows = bse.resultCalendar(
            from_date=datetime.now(),
            to_date=datetime.now() + timedelta(days=14),
        )
    except Exception as e:
        print(f"resultCalendar() failed: {e}")
        try:
            bse.exit()
        except Exception:
            pass
        return

    print(f"\nTotal rows returned : {len(rows)}\n")

    if not rows:
        print("BSE returned ZERO rows. Either the market")
        print("is between result seasons, or the endpoint")
        print("changed. Paste this whole output anyway.")
        try:
            bse.exit()
        except Exception:
            pass
        return

    # 1. The KEYS (field names) — this is what I need most
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
            bse.exit()
        except Exception:
            pass
        return

    # 2. First 8 full rows — shows date format + name format
    print("\n" + "-" * 64)
    print("FIRST 8 RAW ROWS:")
    print("-" * 64)
    for i, row in enumerate(rows[:8], 1):
        print(f"\n[{i}]")
        for key, value in row.items():
            print(f"    {key} = {value!r}")

    # 3. Distinct dates seen (are they spread across days?)
    print("\n" + "-" * 64)
    print("DISTINCT VALUES per key (first 15 rows):")
    print("-" * 64)
    for key in first.keys():
        values = []
        for row in rows[:15]:
            v = str(row.get(key, ""))[:30]
            if v and v not in values:
                values.append(v)
        print(f"  {key}: {values[:10]}")

    try:
        bse.exit()
    except Exception:
        pass

    print("\n" + "=" * 64)
    print("  COPY EVERYTHING ABOVE BACK INTO THE CHAT")
    print("=" * 64)


if __name__ == "__main__":
    main()
