"""
==========================================================
Pre-Market Snapshot
==========================================================

Captures each symbol's genuine pre-open discovered price and
volume, once per trading day, for use in prioritizing the
750-stock universe right at market open (biggest pre-open
gaps/volume first) instead of the bot searching all 750 names
with equal blind attention when the bell rings.

Why this is possible at all -- and why it needs a filter
----------------------------------------------------------
Confirmed empirically on 2026-07-21 by running
tests/Test_premarket_feed.py live (see the log it produced,
premarket_feed_test_20260721_085953.log): Dhan's feed sends
packets continuously from BEFORE 09:00, but the early ones
carry STALE data left over from the previous session -- Ticker
Data shows LTT="00:00:00" (a sentinel), and Quote Data shows
LTT values from yesterday afternoon (e.g. "15:59:09"). The
genuine pre-open discovered price only starts appearing once
LTT itself falls inside today's actual pre-open window --
confirmed in that log at 09:07:57, where LTT flips to a real
current timestamp and high/low/open all converge on the
discovered price (the classic sign of NSE's pre-open call
auction settling).

So "is this tick real pre-open data, not stale carryover" is
answered by: does LTT's time-of-day fall inside
[PREOPEN_START, MARKET_OPEN)? Stale carryover values are either
the "00:00:00" sentinel or an afternoon time from the prior
session -- in practice never coincidentally inside this narrow
band, so this is a real filter grounded in what was actually
observed, not a guess.

Caveat, stated plainly: the empirical run above only watched 5
liquid stocks (RELIANCE, TCS, HDFCBANK, INFY, SBIN). Whether
EVERY one of the 750 stocks gets a genuine pre-open tick in
that window (versus staying on stale data until 09:15, e.g. for
illiquid names with no pre-open orders) has not been verified --
that can only be confirmed by watching a real session with the
full universe subscribed, i.e. tomorrow morning.

This module NEVER trades and NEVER blocks anything -- it is
pure observation, feeding a ranked report the same way the
news/results watchlists do.

Author : H&M ORB AUTO TRADER
==========================================================
"""

from datetime import datetime


class PreMarketSnapshot:

    PREOPEN_START = "09:00:00"
    MARKET_OPEN = "09:15:00"

    def __init__(self):
        # symbol -> {"price","volume","ltt","captured_at"}
        self.snapshots = {}
        self._session_date = None

    # --------------------------------------------------

    def _reset_if_new_day(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self._session_date:
            self._session_date = today
            self.snapshots = {}

    # --------------------------------------------------

    def on_tick(self, symbol, ltp, ltt, volume=0):
        """
        Called on every tick (cheap no-op outside the pre-open
        window). Keeps overwriting a symbol's snapshot with the
        latest pre-open tick until 09:15, at which point the
        last value written is what stays -- the most refined
        pre-open price/volume for the day.
        """
        self._reset_if_new_day()

        ltt_str = str(ltt or "")
        if not (self.PREOPEN_START <= ltt_str < self.MARKET_OPEN):
            return

        if ltp is None:
            return

        symbol = str(symbol).upper().strip()
        if not symbol:
            return

        self.snapshots[symbol] = {
            "price": float(ltp),
            "volume": int(volume or 0),
            "ltt": ltt_str,
            "captured_at": datetime.now().isoformat(),
        }

    # --------------------------------------------------

    def get(self, symbol):
        self._reset_if_new_day()
        return self.snapshots.get(str(symbol).upper().strip())

    # --------------------------------------------------

    def gap_percent(self, symbol, previous_close):
        """
        % gap of the pre-open discovered price vs the previous
        close. Returns None if there's no snapshot or no usable
        previous close -- never fabricates a number.
        """
        snap = self.get(symbol)
        if snap is None or not previous_close:
            return None
        try:
            return round(
                (snap["price"] - previous_close)
                / previous_close * 100,
                2,
            )
        except (TypeError, ZeroDivisionError):
            return None

    # --------------------------------------------------

    def ranked_by_gap(self, price_engine=None, limit=25):
        """
        Every captured symbol, ranked by absolute gap % vs
        previous close. price_engine is optional (this module
        has no hard dependency on it) -- without it, gap_percent
        is just None for every row and ranking falls back to
        insertion order.
        """
        self._reset_if_new_day()

        rows = []
        for symbol, snap in self.snapshots.items():
            prev_close = None
            if price_engine is not None:
                try:
                    prev_close = price_engine.get_previous_close(
                        symbol
                    )
                except Exception:
                    prev_close = None

            gap = (
                self.gap_percent(symbol, prev_close)
                if prev_close else None
            )

            rows.append({
                "symbol": symbol,
                "price": snap["price"],
                "volume": snap["volume"],
                "previous_close": prev_close,
                "gap_percent": gap,
            })

        rows.sort(
            key=lambda r: (
                abs(r["gap_percent"])
                if r["gap_percent"] is not None else -1
            ),
            reverse=True,
        )
        return rows[:limit]

    # --------------------------------------------------

    def report(self, price_engine=None, limit=15):
        self._reset_if_new_day()

        if not self.snapshots:
            return (
                "PRE-MARKET SNAPSHOT\n\n"
                "No pre-open data captured yet today."
            )

        ranked = self.ranked_by_gap(
            price_engine=price_engine, limit=limit
        )

        lines = [
            f"PRE-MARKET SNAPSHOT "
            f"({len(self.snapshots)} stocks captured)",
            "",
        ]
        for r in ranked:
            gap_str = (
                f"{r['gap_percent']:+.2f}%"
                if r["gap_percent"] is not None else "—"
            )
            lines.append(
                f"{r['symbol']:<12} {gap_str:>8}  "
                f"₹{r['price']:.2f}  vol {r['volume']:,}"
            )

        return "\n".join(lines)
