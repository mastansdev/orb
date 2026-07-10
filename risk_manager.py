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

        # Step 4: Replaced Target block to track target_reached and update stage
        if ltp >= trade["target"]:
            trade["target_reached"] = True
            trade["stage"] = "WINNER"
            trade["active"] = False
            trade["exit_price"] = ltp
            return "TARGET"

        # --------------------------------------------------
        # Move Stop Loss to Breakeven at 1R
        # --------------------------------------------------

        # Step 3: Replaced breakeven block to use the new flags and update stage
        if not trade["breakeven_done"] and ltp >= trade["entry"] + trade["risk"]:

            trade["trail_active"] = True
            trade["trail_sl"] = trade["entry"]
            trade["breakeven_done"] = True
            trade["stage"] = "PROTECTED"

        return "ACTIVE"