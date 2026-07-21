from config import RISK_REWARD


class RiskManager:

    def create_trade(self, entry_price, stop_loss):

        assert RISK_REWARD >= 1, "RISK_REWARD must be at least 1"

        risk = entry_price - stop_loss

        if risk <= 0:
            return None

        # Step 1: Updated dictionary with new trade lifecycle fields
        return {
            "entry": entry_price,
            "stop_loss": stop_loss,
            "trail_sl": stop_loss,
            "risk": risk,
            "target": entry_price + (risk * RISK_REWARD),
            # Existing
            "trail_active": False,
            "active": True,
            "exit_price": None,
            # ------------------------------
            # Trade Lifecycle (NEW)
            # ------------------------------
            "stage": "RISK",
            "highest_price": entry_price,
            "target_reached": False,
            "breakeven_done": False,
        }

    # --------------------------------------------------

    def update(self, trade, ltp, ltt):

        if not trade["active"]:
            return "CLOSED"

        # Step 2: Highest Price Tracking
        # ---------------------------------
        if ltp > trade["highest_price"]:
            trade["highest_price"] = ltp

        # Force Exit
        if ltt >= "15:15:00":
            trade["active"] = False
            trade["exit_price"] = ltp
            return "TIME_EXIT"

        # Stop Loss / Breakeven
        if ltp <= trade["trail_sl"]:
            trade["active"] = False
            trade["exit_price"] = ltp
            return "STOPLOSS"

        # --------------------------------------------------
        # Move Stop Loss to Breakeven at 1R
        #
        # NOTE: this must run BEFORE the target check.
        # With RISK_REWARD = 1.0 the old ordering made
        # this block unreachable (target always fired
        # first at exactly 1R).
        # --------------------------------------------------

        if not trade["breakeven_done"] and ltp >= trade["entry"] + trade["risk"]:

            trade["trail_active"] = True
            trade["trail_sl"] = trade["entry"]
            trade["breakeven_done"] = True
            trade["stage"] = "PROTECTED"

        # --------------------------------------------------
        # Target -- INFORMATIONAL ONLY, no longer force-closes
        # the position (2026-07-21, user's explicit choice:
        # "true trailing runner, no fixed cap").
        #
        # Old behaviour: reaching RISK_REWARD x risk closed the
        # ENTIRE position right here, before dynamic_trade_
        # manager.py ever got a turn. Since PARTIAL_BOOK_AT_R
        # (config.py) also sits at 1R -- the same level as the
        # old RISK_REWARD=1.0 target -- this check always won
        # the race, so partial-booking and the progressive
        # trailing stop never actually ran on a winning trade
        # in production, despite all that logic existing.
        #
        # New behaviour: just record that price touched the
        # nominal target (kept for dashboard/reporting context)
        # and keep returning ACTIVE. From here,
        # dynamic_trade_manager.advise() takes over: books half
        # the position at PARTIAL_BOOK_AT_R, then trails the
        # remainder with a ratcheting stop that only tightens,
        # never widens -- no fixed ceiling. The trade now only
        # ends via STOPLOSS/trail, the 15:15 hard time exit, or
        # a catalyst/thesis-decay exit -- never by "hit a
        # number, close it."
        # --------------------------------------------------
        if not trade["target_reached"] and ltp >= trade["target"]:
            trade["target_reached"] = True

        return "ACTIVE"