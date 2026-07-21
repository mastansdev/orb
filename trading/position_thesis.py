"""
==========================================================
Position Thesis Engine  (the HOLD brain)
==========================================================

PROJECT_BRAIN.md, first principle:

    "Allocate capital where probability of continuation
     is highest, and WITHDRAW capital immediately when
     that probability deteriorates."

The bot's ENTRY brain is rich (9 evidence sources +
conviction + causal). Its HOLD brain was mechanical
(stop / target / trail / time). This engine is the
missing half: it continuously re-scores the THESIS of
every open position and issues a THESIS_EXIT the moment
the reason to own the stock has decayed — even in small
profit, even before the stop.

Why: a stock entered because "sector leading + RS leader
+ catalyst" whose sector then flips laggard and catalyst
fades is a dead trade. Waiting for a mechanical stop is
how winners round-trip into losers and drawdowns deepen.
Exit the dead thesis early as a scratch; redeploy the
capital to a live opportunity.

Decision returned:
    HOLD          — thesis intact
    THESIS_EXIT   — conviction decayed below the floor
                    (reason to own is gone)

The price stop remains the failsafe underneath. This is
advice; the Engine executes it.

Author : H&M ORB AUTO TRADER
==========================================================
"""

from datetime import datetime

from config import (
    THESIS_ENGINE_ENABLED,
    THESIS_DECAY_FRACTION,
    THESIS_GRACE_MINUTES,
)


class PositionThesisEngine:

    def __init__(
        self,
        trade_selection_engine,
        intelligence_engine,
        sector_engine=None,
    ):
        self.trade_selection_engine = trade_selection_engine
        self.intelligence_engine = intelligence_engine
        self.sector_engine = sector_engine

        self.thesis_exits = 0

    # --------------------------------------------------

    def advise(self, symbol, trade, ltp):
        """
        Re-evaluate one open position's thesis.
        Returns {action, reason, current, entry}.
        """
        if not THESIS_ENGINE_ENABLED:
            return {"action": "HOLD", "reason": ""}

        # Grace period: let the trade breathe past entry
        entry_time = trade.get("entry_time", "")
        if self._minutes_since(entry_time) < THESIS_GRACE_MINUTES:
            return {"action": "HOLD", "reason": "grace"}

        entry_conviction = float(
            trade.get("conviction", 0) or 0
        )

        # No conviction recorded at entry (e.g. legacy
        # trade) → nothing to compare; leave to stops.
        if entry_conviction <= 0:
            return {"action": "HOLD", "reason": "no baseline"}

        # Re-score the live thesis (read-only)
        try:
            intelligence = self.intelligence_engine.get(symbol)
            current = self.trade_selection_engine.score_symbol(
                symbol, intelligence
            )
        except Exception:
            return {"action": "HOLD", "reason": "score failed"}

        # Fix (2026-07-21): score_symbol() returns None (not
        # 0.0) when the rebuild itself crashed internally,
        # specifically so a code failure can't masquerade as
        # "conviction genuinely hit zero" and force a real
        # exit on a live position over a bug. Treat that the
        # same as the except above: hold, don't decide.
        if current is None:
            return {"action": "HOLD", "reason": "score failed"}

        floor = entry_conviction * THESIS_DECAY_FRACTION

        if current < floor:
            self.thesis_exits += 1
            return {
                "action": "THESIS_EXIT",
                "reason": (
                    f"thesis decayed: conviction "
                    f"{current:.0f} < {floor:.0f} "
                    f"(entry {entry_conviction:.0f}) — "
                    f"reason to own is gone"
                ),
                "current": round(current, 1),
                "entry": round(entry_conviction, 1),
            }

        return {
            "action": "HOLD",
            "reason": "",
            "current": round(current, 1),
            "entry": round(entry_conviction, 1),
        }

    # --------------------------------------------------

    @staticmethod
    def _minutes_since(entry_time):
        """
        Minutes elapsed since entry_time (a bare "HH:MM:SS"
        string with no date attached).

        BUG FIXED HERE: naively doing (now - entered) on a
        same-day reconstruction goes NEGATIVE whenever entry_time's
        clock value is later in the day than the current wall
        clock -- e.g. entry_time="09:20:00" evaluated at 07:40.
        A negative elapsed value is always < THESIS_GRACE_MINUTES,
        so the grace-period check above silently returns HOLD
        and the decay check below never runs at all, no matter
        how badly the thesis has actually decayed.

        In real trading this can't happen (a position's
        entry_time is always earlier the same session than any
        later check), but it can happen when a test or replay
        harness runs a fixed clock-time scenario before that
        time of day -- which is exactly what caused this test to
        fail when the suite ran at 07:40 with entry_time
        "09:20:00". Clamp any negative diff to a large positive
        number instead of letting it look like "still fresh".
        """
        if not entry_time:
            return 999
        try:
            now = datetime.now()
            hh, mm, ss = (entry_time.split(":") + ["0", "0"])[:3]
            entered = now.replace(
                hour=int(hh), minute=int(mm),
                second=int(ss), microsecond=0
            )
            elapsed = (now - entered).total_seconds() / 60
            if elapsed < 0:
                return 999
            return elapsed
        except Exception:
            return 999

    # --------------------------------------------------

    def stats(self):
        return {"thesis_exits": self.thesis_exits}