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
        # 3. Ratchet trailing after TRAIL_AFTER_R
        # ---------------------------------
        if r_multiple >= TRAIL_AFTER_R:

            highest = trade.get("highest_price", ltp)

            candidate_trail = round(
                highest - (TRAIL_DISTANCE_R * risk), 2
            )

            current_trail = trade.get(
                "trail_sl", trade.get("stop_loss", 0)
            )

            # Ratchet only — never widen
            if candidate_trail > current_trail:
                self.tightens += 1

                return {
                    "action": "TIGHTEN",
                    "new_trail": candidate_trail,
                    "reason": (
                        f"+{r_multiple:.1f}R — trail "
                        f"→ ₹{candidate_trail:.2f}"
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

    def stats(self):
        return {
            "partials_booked": self.partials_booked,
            "tightens": self.tightens,
            "catalyst_exits": self.catalyst_exits,
        }
