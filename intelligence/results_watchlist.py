"""
==========================================================
Results Watchlist  (active, day-based)
==========================================================

Turns the results calendar from passive caution into an
active daily opportunity funnel:

    WATCHING   — stock reports TODAY, result not yet out.
                 New entries BLOCKED (binary-event risk):
                 a result can gap the stock through a stop.

    ANNOUNCED  — the result has published (detected via a
                 fresh news/event on the name). Direction
                 is now known → the stock becomes a
                 TOP-PRIORITY catalyst for a post-result
                 trade (subject to the priced-in check).

So the bot protects capital BEFORE the number, and hunts
the move AFTER it — the correct way to trade earnings.

This module NEVER trades. It classifies attention.

Author : H&M ORB AUTO TRADER
==========================================================
"""

from datetime import datetime

from intelligence.evidence import Evidence


class ResultsWatchlist:

    def __init__(self, results_calendar, event_intelligence=None):
        self.results_calendar = results_calendar
        self.event_intelligence = event_intelligence

        # symbol → {"state","since","headline"}
        self.today = {}
        self._loaded_date = None

        self.rebuild()

    # --------------------------------------------------

    def rebuild(self):
        """Load today's result names as WATCHING."""
        today = datetime.now().strftime("%Y-%m-%d")
        self._loaded_date = today

        names = self.results_calendar.upcoming(0).get(
            today, []
        )

        self.today = {}
        for symbol in names:
            self.today[symbol.upper()] = {
                "state": "WATCHING",
                "since": datetime.now(),
                "headline": "",
            }

        if self.today:
            print(
                f"[WATCHLIST] Results today: "
                f"{len(self.today)} stocks WATCHING"
            )

        return len(self.today)

    # --------------------------------------------------

    def _refresh_if_new_day(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self._loaded_date:
            self.rebuild()

    # --------------------------------------------------

    def is_watching(self, symbol):
        """Reporting today, result NOT yet announced."""
        self._refresh_if_new_day()
        entry = self.today.get(symbol.upper())
        return bool(entry and entry["state"] == "WATCHING")

    # --------------------------------------------------

    def is_announced(self, symbol):
        """Result published today — live catalyst."""
        self._refresh_if_new_day()
        entry = self.today.get(symbol.upper())
        return bool(entry and entry["state"] == "ANNOUNCED")

    # --------------------------------------------------

    def on_event(self, event):
        """
        Called for every structured event. If a fresh
        event lands on a stock that reports today, the
        result is out → flip WATCHING → ANNOUNCED.
        """
        self._refresh_if_new_day()

        symbol = str(event.get("symbol", "")).upper()
        if not symbol:
            return

        entry = self.today.get(symbol)
        if entry is None or entry["state"] == "ANNOUNCED":
            return

        # Result / earnings-type events confirm the drop
        etype = str(event.get("event_type", "")).upper()
        catalyst = str(event.get("catalyst", "")).upper()

        looks_like_result = (
            "RESULT" in etype or "RESULT" in catalyst
            or "EARNING" in etype or "PROFIT" in etype
            or "REVENUE" in etype or "QUARTER" in etype
        )

        # Any material event on a results-day name is
        # treated as the announcement trigger.
        importance = float(event.get("importance", 0) or 0)

        if looks_like_result or importance >= 40:
            entry["state"] = "ANNOUNCED"
            entry["since"] = datetime.now()
            entry["headline"] = event.get("headline", "")[:100]
            print(
                f"[WATCHLIST] {symbol} RESULT ANNOUNCED → "
                f"live catalyst"
            )

    # --------------------------------------------------

    def build_evidence(self, symbol):
        """
        ANNOUNCED results-day stocks get a positive
        RESULTS_LIVE catalyst boost (post-result move).
        WATCHING stocks get nothing here — they are
        blocked upstream by the binary-event rule.
        """
        self._refresh_if_new_day()

        entry = self.today.get(symbol.upper())
        if entry is None or entry["state"] != "ANNOUNCED":
            return []

        return [
            Evidence(
                provider="RESULTS_LIVE",
                symbol=symbol,
                recommendation="BUY",
                score=70,
                confidence=75,
                reason=(
                    f"Post-result catalyst (announced "
                    f"today): {entry['headline'][:70]}"
                ),
                facts={
                    "event_type": "RESULTS_ANNOUNCED",
                    "state": "ANNOUNCED",
                },
            )
        ]

    # --------------------------------------------------

    def report(self):
        self._refresh_if_new_day()

        if not self.today:
            return (
                "RESULTS WATCHLIST (today)\n\n"
                "No stocks reporting today."
            )

        watching = [
            s for s, e in self.today.items()
            if e["state"] == "WATCHING"
        ]
        announced = [
            s for s, e in self.today.items()
            if e["state"] == "ANNOUNCED"
        ]

        lines = [
            "RESULTS WATCHLIST (today)",
            "",
            f"⏳ WATCHING (result awaited, entries "
            f"BLOCKED): {len(watching)}",
        ]
        if watching:
            lines.append("  " + ", ".join(sorted(watching)[:25]))

        lines.append("")
        lines.append(
            f"✅ ANNOUNCED (live catalyst, tradeable): "
            f"{len(announced)}"
        )
        if announced:
            lines.append("  " + ", ".join(sorted(announced)))
        else:
            lines.append("  (none yet — flips live as "
                         "results publish)")

        return "\n".join(lines)
