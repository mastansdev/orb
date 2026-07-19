"""
==========================================================
Risk Governor
==========================================================

Mission
-------
Independent risk authority with VETO power over the
strategy. The Constitution says:

    Evidence contributes; Conviction decides;
    RISK AUTHORIZES; Execution acts.

This module is that authorization step.

Responsibilities
----------------
1. Enforce the daily loss lockout (DAILY_MAX_LOSS)
2. Enforce the daily profit lock (DAILY_MAX_PROFIT)
3. Enforce consecutive-loss pause
4. Enforce portfolio heat cap (total open risk)
5. Enforce sector concentration cap
6. Maintain kill-switch state with reasons
7. Alert the operator when any lockout fires

This module NEVER:
    • scores trades
    • places or exits orders directly
    • reads market intelligence

It only answers one question:
    "Is it SAFE to take more risk right now?"

Once a lockout fires it stays locked for the rest of
the session. There is no automatic re-enable and no
override method by design.

Author : H&M ORB AUTO TRADER
==========================================================
"""

from datetime import datetime

from config import (
    DAILY_MAX_LOSS,
    DAILY_MAX_PROFIT,
    DAILY_LOSS_INCLUDES_FLOATING,
    RISK_GOVERNOR_ENABLED,
    KILL_SWITCH_EXIT_ALL,
    MAX_CONSECUTIVE_LOSSES,
    MAX_POSITIONS_PER_SECTOR,
    MAX_PORTFOLIO_HEAT,
    CAPITAL,
    RISK_PER_TRADE,
    MAX_CAPITAL_PER_TRADE,
    MAX_OPEN_POSITIONS,
)


class RiskGovernor:

    def __init__(
        self,
        capital_manager,
        trade_controller,
        telegram=None
    ):
        self.capital_manager = capital_manager
        self.trade_controller = trade_controller
        self.telegram = telegram

        # ---------------------------------
        # Kill Switch State
        # ---------------------------------
        self.locked = False
        self.lock_reason = ""
        self.lock_time = None

        # ---------------------------------
        # Session Counters
        # ---------------------------------
        self.consecutive_losses = 0
        self.trades_closed = 0
        self.entries_blocked = 0

        # One-time alert guards
        self._loss_alert_sent = False
        self._profit_alert_sent = False

    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------

    def _notify(self, message):
        print(f"\n[RISK GOVERNOR] {message}\n")

        if self.telegram is not None:
            try:
                self.telegram.send(
                    f"🛑 RISK GOVERNOR\n\n{message}"
                )
            except Exception:
                # A Telegram failure must never break risk logic
                pass

    # --------------------------------------------------

    def _day_pnl(self):
        """
        Daily P&L as the governor sees it.
        """
        realized = self.capital_manager.pnl()

        if DAILY_LOSS_INCLUDES_FLOATING:
            return realized + self.capital_manager.floating_mtm()

        return realized

    # --------------------------------------------------

    def _lock(self, reason):
        """
        Fire the kill switch. Irreversible for the session.
        """
        if self.locked:
            return

        self.locked = True
        self.lock_reason = reason
        self.lock_time = datetime.now()

        # Block all new trading activity
        self.trade_controller.disable_entries()
        self.trade_controller.disable_trading()

        message = (
            f"KILL SWITCH FIRED\n\n"
            f"Reason : {reason}\n"
            f"Time   : {self.lock_time.strftime('%H:%M:%S')}\n\n"
            f"New entries are DISABLED for the rest of the day."
        )

        if KILL_SWITCH_EXIT_ALL:
            self.trade_controller.request_exit_all()
            message += "\nAll open positions will be exited."

        self._notify(message)

    # --------------------------------------------------
    # Portfolio heat / concentration
    # --------------------------------------------------

    def portfolio_heat(self, trades):
        """
        Sum of open risk across positions:
        (entry - stop_loss) * qty for each open trade.
        """
        heat = 0.0

        for trade in trades.values():
            entry = trade.get("entry", 0)
            stop = trade.get("stop_loss", 0)
            qty = trade.get("qty", 0)
            risk = max(0.0, (entry - stop)) * qty
            heat += risk

        return round(heat, 2)

    # --------------------------------------------------

    def _sector_count(self, trades, sector):
        if not sector:
            return 0

        return sum(
            1
            for trade in trades.values()
            if trade.get("sector", "") == sector
        )

    # --------------------------------------------------
    # PUBLIC : Entry Authorization
    # --------------------------------------------------

    def entry_allowed(
        self,
        trades,
        new_risk=0.0,
        sector=""
    ):
        """
        Called BEFORE every new entry.

        Returns (allowed: bool, reason: str)
        """

        if not RISK_GOVERNOR_ENABLED:
            return True, "Risk Governor disabled"

        # ---------------------------------
        # 1. Kill switch already fired
        # ---------------------------------
        if self.locked:
            self.entries_blocked += 1
            return False, f"LOCKED: {self.lock_reason}"

        # ---------------------------------
        # 2. Daily loss lockout
        # ---------------------------------
        day_pnl = self._day_pnl()

        if day_pnl <= -abs(DAILY_MAX_LOSS):
            self._lock(
                f"Daily loss limit hit "
                f"(₹{day_pnl:.0f} ≤ -₹{DAILY_MAX_LOSS})"
            )
            self.entries_blocked += 1
            return False, "Daily loss limit"

        # ---------------------------------
        # 3. Daily profit lock (soft: entries only)
        # ---------------------------------
        if day_pnl >= abs(DAILY_MAX_PROFIT):
            if not self._profit_alert_sent:
                self._profit_alert_sent = True
                self.trade_controller.disable_entries()
                self._notify(
                    f"Daily profit target reached "
                    f"(₹{day_pnl:.0f}). New entries paused. "
                    f"Open positions continue to be managed."
                )
            self.entries_blocked += 1
            return False, "Daily profit target reached"

        # ---------------------------------
        # 4. Consecutive loss pause
        # ---------------------------------
        if self.consecutive_losses >= MAX_CONSECUTIVE_LOSSES:
            self._lock(
                f"{self.consecutive_losses} consecutive losses "
                f"— regime likely hostile"
            )
            self.entries_blocked += 1
            return False, "Consecutive loss pause"

        # ---------------------------------
        # 5. Portfolio heat cap
        # ---------------------------------
        heat = self.portfolio_heat(trades)

        if heat + new_risk > MAX_PORTFOLIO_HEAT:
            self.entries_blocked += 1
            return False, (
                f"Portfolio heat cap "
                f"(₹{heat:.0f} + ₹{new_risk:.0f} > "
                f"₹{MAX_PORTFOLIO_HEAT})"
            )

        # ---------------------------------
        # 6. Sector concentration cap
        # ---------------------------------
        if sector:
            count = self._sector_count(trades, sector)

            if count >= MAX_POSITIONS_PER_SECTOR:
                self.entries_blocked += 1
                return False, (
                    f"Sector cap: {count} open positions "
                    f"in {sector}"
                )

        return True, "Risk authorized"

    # --------------------------------------------------
    # PUBLIC : Trade Result Feedback
    # --------------------------------------------------

    def on_trade_closed(self, pnl):
        """
        Called AFTER every trade closes.
        Updates loss streak and re-checks the daily
        lockout so it can fire between entries too.
        """
        self.trades_closed += 1

        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        if not RISK_GOVERNOR_ENABLED:
            return

        day_pnl = self._day_pnl()

        if not self.locked and day_pnl <= -abs(DAILY_MAX_LOSS):
            self._lock(
                f"Daily loss limit hit after exit "
                f"(₹{day_pnl:.0f} ≤ -₹{DAILY_MAX_LOSS})"
            )

    # --------------------------------------------------
    # PUBLIC : Config Coherence Audit
    # --------------------------------------------------

    @staticmethod
    def coherence_audit():
        """
        Detect internally-inconsistent risk settings
        BEFORE they surprise the operator live.

        Returns (warnings: list[str], facts: dict)
        """
        warnings = []

        intended_risk = CAPITAL * RISK_PER_TRADE

        # Realistic per-trade risk is capped by position
        # value: MAX_CAPITAL_PER_TRADE × a typical
        # intraday stop distance (~2-3% of price).
        typical_stop_pct = 0.025
        realistic_risk = (
            MAX_CAPITAL_PER_TRADE * typical_stop_pct
        )

        effective_risk = min(intended_risk, realistic_risk)

        losers_to_lockout = (
            DAILY_MAX_LOSS / effective_risk
            if effective_risk > 0 else 0
        )

        facts = {
            "intended_risk_per_trade": round(
                intended_risk, 0
            ),
            "realistic_risk_per_trade": round(
                realistic_risk, 0
            ),
            "daily_max_loss": DAILY_MAX_LOSS,
            "losers_to_lockout": round(
                losers_to_lockout, 1
            ),
            "max_portfolio_heat": MAX_PORTFOLIO_HEAT,
        }

        # 1. Intended risk exceeds the daily limit
        if intended_risk > DAILY_MAX_LOSS:
            warnings.append(
                f"RISK_PER_TRADE implies "
                f"₹{intended_risk:,.0f} risk/trade but "
                f"DAILY_MAX_LOSS is ₹{DAILY_MAX_LOSS:,.0f} "
                f"— one intended-size loss exceeds the "
                f"daily limit "
                f"{intended_risk / DAILY_MAX_LOSS:.0f}×. "
                f"Position-value cap is silently doing "
                f"your sizing."
            )

        # 2. Very fast lockout
        if 0 < losers_to_lockout < 3:
            warnings.append(
                f"Daily lockout after only "
                f"~{losers_to_lockout:.1f} typical losers "
                f"(₹{effective_risk:,.0f} each vs "
                f"₹{DAILY_MAX_LOSS:,.0f} limit). "
                f"Intentional? If not, raise "
                f"DAILY_MAX_LOSS or cut size."
            )

        # 3. Heat cap vs daily loss
        if MAX_PORTFOLIO_HEAT > DAILY_MAX_LOSS * 10:
            warnings.append(
                f"MAX_PORTFOLIO_HEAT "
                f"(₹{MAX_PORTFOLIO_HEAT:,.0f}) allows "
                f"{MAX_PORTFOLIO_HEAT / DAILY_MAX_LOSS:.0f}× "
                f"the daily loss limit in simultaneous "
                f"open risk — a single bad sweep can blow "
                f"through the daily limit before exits fill."
            )

        # 4. Heat cap vs position count
        per_position_heat = (
            MAX_PORTFOLIO_HEAT / MAX_OPEN_POSITIONS
            if MAX_OPEN_POSITIONS else 0
        )
        if per_position_heat < effective_risk * 0.5:
            warnings.append(
                f"Heat cap ÷ MAX_OPEN_POSITIONS = "
                f"₹{per_position_heat:,.0f}/position — "
                f"less than half a typical trade's risk "
                f"(₹{effective_risk:,.0f}); the book will "
                f"hit the heat cap long before "
                f"{MAX_OPEN_POSITIONS} positions."
            )

        return warnings, facts

    # --------------------------------------------------

    def print_coherence_audit(self):
        warnings, facts = self.coherence_audit()

        print("\n" + "=" * 60)
        print("RISK CONFIG COHERENCE AUDIT")
        print("=" * 60)
        print(
            f"Intended risk/trade  : "
            f"₹{facts['intended_risk_per_trade']:,.0f}"
        )
        print(
            f"Realistic risk/trade : "
            f"₹{facts['realistic_risk_per_trade']:,.0f} "
            f"(position-value capped)"
        )
        print(
            f"Daily loss limit     : "
            f"₹{facts['daily_max_loss']:,.0f} "
            f"(~{facts['losers_to_lockout']} losers "
            f"to lockout)"
        )
        print(
            f"Portfolio heat cap   : "
            f"₹{facts['max_portfolio_heat']:,.0f}"
        )

        if warnings:
            print()
            for i, warning in enumerate(warnings, 1):
                print(f"⚠️  {i}. {warning}")
        else:
            print("\n✓ Settings are internally coherent.")

        print("=" * 60 + "\n")

        return warnings

    # --------------------------------------------------
    # PUBLIC : Status
    # --------------------------------------------------

    def status(self):
        return {
            "enabled": RISK_GOVERNOR_ENABLED,
            "locked": self.locked,
            "lock_reason": self.lock_reason,
            "day_pnl": round(self._day_pnl(), 2),
            "daily_max_loss": DAILY_MAX_LOSS,
            "consecutive_losses": self.consecutive_losses,
            "max_consecutive_losses": MAX_CONSECUTIVE_LOSSES,
            "max_portfolio_heat": MAX_PORTFOLIO_HEAT,
            "max_positions_per_sector": MAX_POSITIONS_PER_SECTOR,
            "trades_closed": self.trades_closed,
            "entries_blocked": self.entries_blocked,
        }
