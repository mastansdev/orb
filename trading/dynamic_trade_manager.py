"""
==========================================================
Dynamic Trade Manager
==========================================================

Mission
-------
Positions are not "set and forget." Institutional
management = continuously re-deciding the right
exposure as evidence arrives.

Decisions produced (advice, never execution):

    HOLD          — nothing to do
    PARTIAL_BOOK  — book a fraction at R-multiple
    TIGHTEN       — ratchet the trailing stop
    EXIT          — thesis dead (negative catalyst on
                    the held name) — exit now

The Engine executes the advice; the Risk Manager's
stops remain the hard failsafe underneath.

Rules (config-driven)
---------------------
1. PARTIAL_BOOK once at PARTIAL_BOOK_AT_R
   (locks profit, lets the rest run — right-tail
   capture with a protected core)
2. TIGHTEN after TRAIL_AFTER_R: trail at
   highest_price − TRAIL_DISTANCE_R × risk
3. EXIT if a fresh NEGATIVE structured event or
   negative F&O catalyst appears on the held symbol
   (news-driven de-risking: flatten first,
   understand later)

This module NEVER:
    • places orders
    • overrides the Risk Governor
    • widens stops

Author : H&M ORB AUTO TRADER
==========================================================
"""

import time

from config import (
    DYNAMIC_MANAGEMENT_ENABLED,
    PARTIAL_BOOK_AT_R,
    PARTIAL_BOOK_FRACTION,
    TRAIL_AFTER_R,
    TRAIL_DISTANCE_R,
)


class DynamicTradeManager:

    NEGATIVE_DIRECTIONS = (
        "WEAKENING", "CONTRADICTED", "NEGATIVE", "BEARISH"
    )

    # How tight the trail starts, right at PROFIT_LOCK_AT_R, before
    # progressively loosening toward TRAIL_DISTANCE_R by the time
    # the trade reaches TRAIL_AFTER_R. Consider moving to config.py
    # if this needs tuning independently later.
    MIN_TRAIL_DISTANCE_R = 0.3

    # ---------------------------------
    # VELOCITY GUARD (2026-07-20)
    #
    # User's trading philosophy: "if any open position is observed
    # retracing and falling too speed, book that position
    # (irrespective of pnl)... not first-see-first-buy." The
    # progressive trail above reacts to how FAR price has fallen
    # from its peak -- this reacts to how FAST it's falling, even
    # if it hasn't given back much yet. A stock can be well inside
    # its trail distance but still be crashing violently in the
    # last couple of minutes; the trail alone wouldn't catch that
    # until the damage accumulates.
    #
    # Mechanism: track a short rolling window of recent prices per
    # trade. If price has dropped by VELOCITY_DROP_R (in R-multiples
    # of the trade's own risk) from its OWN short-term peak within
    # that window, exit immediately -- regardless of current PnL,
    # regardless of where the R-multiple-based trail would have
    # fired. This is deliberately independent of and faster-firing
    # than the trail.
    #
    # Tuning tradeoff, stated plainly: too tight and this will cut
    # genuine winners short on normal 1-2 minute noise/profit-taking
    # pullbacks that would have continued running; too loose and it
    # stops being meaningfully faster than the existing trail. These
    # starting values are a reasoned first attempt, not a backtested
    # optimum -- watch how often this fires in practice and adjust.
    # ---------------------------------
    VELOCITY_WINDOW_SECONDS = 120   # look back this far for the local peak
    VELOCITY_DROP_R = 0.5           # exit if price falls this many R from that local peak

    def __init__(
        self,
        event_intelligence=None,
        fno_engine=None
    ):
        self.event_intelligence = event_intelligence
        self.fno_engine = fno_engine

        self.partials_booked = 0
        self.tightens = 0
        self.catalyst_exits = 0
        self.velocity_exits = 0

    # --------------------------------------------------

    def advise(self, symbol, trade, ltp):
        """
        Evaluate one open position.

        Returns dict:
            {action, qty (for PARTIAL_BOOK),
             new_trail (for TIGHTEN), reason}
        """
        if not DYNAMIC_MANAGEMENT_ENABLED:
            return {"action": "HOLD", "reason": "disabled"}

        entry = trade.get("entry", 0)
        risk = trade.get("risk", 0)
        qty = trade.get("qty", 0)

        if entry <= 0 or risk <= 0 or qty <= 0:
            return {"action": "HOLD", "reason": "invalid"}

        r_multiple = (ltp - entry) / risk

        # ---------------------------------
        # 1. Negative catalyst on held name
        #    → EXIT (highest priority)
        # ---------------------------------
        negative_reason = self._negative_catalyst(symbol)

        if negative_reason:
            self.catalyst_exits += 1
            return {
                "action": "EXIT",
                "reason": (
                    f"Negative catalyst: {negative_reason}"
                ),
            }

        # ---------------------------------
        # 1c. VELOCITY GUARD — sharp, fast reversal
        #     → EXIT regardless of current PnL
        # ---------------------------------
        velocity_reason = self._velocity_exit(
            trade, ltp, risk
        )

        if velocity_reason:
            self.velocity_exits += 1
            return {
                "action": "EXIT",
                "reason": velocity_reason,
            }

        # ---------------------------------
        # 1b. PROFIT LOCK — once a trade is a real
        #     winner, its stop can never fall below the
        #     locked floor. A winner will NOT become a
        #     loser. ("Every winner returns something.")
        # ---------------------------------
        from config import (
            PROFIT_LOCK_AT_R,
            PROFIT_LOCK_FLOOR_R,
        )

        if (
            not trade.get("profit_locked", False)
            and r_multiple >= PROFIT_LOCK_AT_R
        ):
            lock_price = round(
                entry + PROFIT_LOCK_FLOOR_R * risk, 2
            )
            current_trail = trade.get(
                "trail_sl", trade.get("stop_loss", 0)
            )
            # Side-effect floor: raise the stop so this
            # winner cannot become a loser, then CONTINUE
            # to partial-book / trail as normal.
            if lock_price > current_trail:
                trade["trail_sl"] = lock_price
                trade["trail_active"] = True
            trade["profit_locked"] = True
            self.tightens += 1

        # ---------------------------------
        # 2. Partial profit booking
        # ---------------------------------
        if (
            not trade.get("partial_done", False)
            and r_multiple >= PARTIAL_BOOK_AT_R
            and qty >= 2
        ):
            book_qty = max(
                1, int(qty * PARTIAL_BOOK_FRACTION)
            )

            # Never book the entire position partially
            if book_qty >= qty:
                book_qty = qty - 1

            self.partials_booked += 1

            return {
                "action": "PARTIAL_BOOK",
                "qty": book_qty,
                "reason": (
                    f"+{r_multiple:.1f}R reached — "
                    f"booking {book_qty}/{qty}"
                ),
            }

        # ---------------------------------
        # 3. PROGRESSIVE TRAIL
        #
        # Fix for the profit-giveback bug found live on V2RETAIL
        # (2026-07-20): the OLD logic had a dead zone between
        # PROFIT_LOCK_AT_R (0.6R -- a one-time STATIC floor) and
        # TRAIL_AFTER_R (1.5R -- where active ratcheting used to
        # start). A trade peaking inside that zone got NO adaptive
        # protection at all -- just the static floor, set far below
        # its peak. V2RETAIL peaked at ~1.04R (squarely in the gap)
        # and gave back 85.6% of its peak profit (₹7,543 → ₹1,087)
        # before the static floor finally caught it.
        #
        # Fix: start trailing at the SAME point profit-lock fires
        # (PROFIT_LOCK_AT_R), using a tight distance that
        # PROGRESSIVELY LOOSENS as the move extends toward
        # TRAIL_AFTER_R, reaching today's existing TRAIL_DISTANCE_R
        # exactly at TRAIL_AFTER_R and staying there beyond it.
        #
        # This means trades that run big (>= TRAIL_AFTER_R) behave
        # IDENTICALLY to before -- no regression for proven big
        # movers, which the existing test suite already validates
        # ("trail ratchets", "trail level correct", "trail never
        # widens"). Only trades that peak in the former dead zone
        # get real protection now.
        # ---------------------------------
        highest = trade.get("highest_price", ltp)

        # IMPORTANT: use the PEAK r-multiple (based on highest_price,
        # which only ever increases) to size the trail distance, not
        # the CURRENT r-multiple (based on ltp, which drops as price
        # reverses). Using current r-multiple here would make the
        # trail distance shrink WHILE price is falling -- unstable,
        # unintended behavior. Peak r-multiple freezes the moment a
        # trade tops out, so the trail distance (and therefore the
        # trail price) also freezes at a single, stable value once
        # the reversal begins -- exactly what "how far did this
        # trade prove itself" should mean.
        peak_r_multiple = (highest - entry) / risk

        if peak_r_multiple >= PROFIT_LOCK_AT_R:

            if peak_r_multiple >= TRAIL_AFTER_R:
                trail_distance_r = TRAIL_DISTANCE_R
            else:
                span = TRAIL_AFTER_R - PROFIT_LOCK_AT_R
                progress = (
                    (peak_r_multiple - PROFIT_LOCK_AT_R) / span
                    if span > 0 else 1.0
                )
                trail_distance_r = (
                    self.MIN_TRAIL_DISTANCE_R
                    + progress * (
                        TRAIL_DISTANCE_R
                        - self.MIN_TRAIL_DISTANCE_R
                    )
                )

            candidate_trail = round(
                highest - (trail_distance_r * risk), 2
            )

            current_trail = trade.get(
                "trail_sl", trade.get("stop_loss", 0)
            )

            # Ratchet only — never widen (same guarantee as before)
            if candidate_trail > current_trail:
                self.tightens += 1

                return {
                    "action": "TIGHTEN",
                    "new_trail": candidate_trail,
                    "reason": (
                        f"peak +{peak_r_multiple:.2f}R — trail "
                        f"(dist {trail_distance_r:.2f}R) → "
                        f"₹{candidate_trail:.2f}"
                    ),
                }

        return {"action": "HOLD", "reason": ""}

    # --------------------------------------------------

    def _negative_catalyst(self, symbol):
        """
        Fresh negative structured event or negative
        F&O catalyst on the held symbol.
        """
        # F&O watchlist direction
        if self.fno_engine is not None:
            try:
                entry = self.fno_engine.watchlist.get(
                    symbol
                )
                if entry and str(
                    entry.get("direction", "")
                ).upper() in self.NEGATIVE_DIRECTIONS:
                    return entry.get(
                        "headline", "F&O catalyst turned negative"
                    )[:80]
            except Exception:
                pass

        # Recent structured events
        if self.event_intelligence is not None:
            try:
                events = (
                    self.event_intelligence
                        .repository
                        .symbol_structured_events(symbol, 3)
                )

                for event in events:
                    if not self.event_intelligence._is_fresh(
                        event.get("created_at", "")
                    ):
                        continue

                    direction = str(
                        event.get("direction", "")
                    ).upper()

                    importance = float(
                        event.get("importance", 0) or 0
                    )

                    if (
                        direction in self.NEGATIVE_DIRECTIONS
                        and importance >= 40
                    ):
                        return event.get(
                            "headline", "negative event"
                        )[:80]
            except Exception:
                pass

        return None

    # --------------------------------------------------

    def _velocity_exit(self, trade, ltp, risk):
        """
        Track a short rolling window of recent prices for THIS
        trade, and exit if price has dropped by VELOCITY_DROP_R
        (in R-multiples) from its own SHORT-TERM peak within
        VELOCITY_WINDOW_SECONDS -- independent of the trade's
        all-time peak or current overall PnL. Returns a reason
        string if triggered, else None.
        """
        now = time.time()

        history = trade.setdefault("velocity_history", [])
        history.append((now, ltp))

        # Prune anything outside the lookback window.
        cutoff = now - self.VELOCITY_WINDOW_SECONDS
        history[:] = [
            (t, p) for t, p in history if t >= cutoff
        ]

        if len(history) < 2:
            # Not enough samples yet to judge speed.
            return None

        local_peak = max(p for _, p in history)
        drop_r = (local_peak - ltp) / risk

        if drop_r >= self.VELOCITY_DROP_R:
            return (
                f"Velocity guard: fell {drop_r:.2f}R from its "
                f"own {self.VELOCITY_WINDOW_SECONDS}s peak "
                f"(₹{local_peak:.2f} → ₹{ltp:.2f}) — sharp "
                f"reversal, exiting regardless of PnL"
            )

        return None

    # --------------------------------------------------

    def stats(self):
        return {
            "partials_booked": self.partials_booked,
            "tightens": self.tightens,
            "catalyst_exits": self.catalyst_exits,
            "velocity_exits": self.velocity_exits,
        }