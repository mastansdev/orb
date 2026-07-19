"""
==========================================================
Market Shock Responder
==========================================================

The Trump-Iran lesson (+53k → -1.4L): when a market-wide
bearish shock hits, the correct sequence is:

    1. FLATTEN everything immediately
       (speed of de-risking beats accuracy of analysis)
    2. Identify the weakest / most-affected sector
    3. Position for downside: BUY ATM PE on the
       weakest names / index

Triggers
--------
    • Breadth collapse (market state: ≤20% advancing
      and avg ≤ -1.5%)
    • Risk Governor shock guards (peak giveback /
      fast drop) via callback
    • Operator: /shock CONFIRM

v1 honesty note
---------------
Steps 1-2 are fully automatic. Step 3 produces a
PRECISE recommendation (weakest sector, weakest names,
ATM strikes) via Telegram — auto-execution of option
orders needs the option feed subscription (planned),
because a position we cannot see ticks for cannot be
managed.

Fires at most once per session.

Author : H&M ORB AUTO TRADER
==========================================================
"""

from datetime import datetime

from config import (
    SHOCK_RESPONDER_ENABLED,
    SHOCK_BREADTH_PCT,
    SHOCK_AVG_CHANGE,
)
from intelligence.price_engine import price_engine


class ShockResponder:

    def __init__(
        self,
        trade_controller,
        sector_engine,
        company_intelligence,
        telegram=None,
    ):
        self.trade_controller = trade_controller
        self.sector_engine = sector_engine
        self.company_intelligence = company_intelligence
        self.telegram = telegram

        self.triggered = False
        self.trigger_reason = ""
        self.trigger_time = None

    # --------------------------------------------------

    def check_market(self, state):
        """
        Called by the Engine with the live market state.
        """
        if not SHOCK_RESPONDER_ENABLED or self.triggered:
            return False

        breadth = state.get("breadth_pct")
        avg = state.get("avg_change")

        if breadth is None or avg is None:
            return False

        if (
            breadth <= SHOCK_BREADTH_PCT
            and avg <= SHOCK_AVG_CHANGE
        ):
            self.trigger(
                f"MARKET BREADTH COLLAPSE: only "
                f"{breadth}% advancing, avg "
                f"{avg:+.2f}% — market-wide shock"
            )
            return True

        return False

    # --------------------------------------------------

    def trigger(self, reason):
        """
        Execute the shock playbook. Once per session.
        """
        if self.triggered:
            return

        self.triggered = True
        self.trigger_reason = reason
        self.trigger_time = datetime.now()

        # 1. FLATTEN — no analysis first
        self.trade_controller.disable_entries()
        self.trade_controller.request_exit_all()

        print(f"\n🚨 SHOCK RESPONDER: {reason}\n")

        # 2-3. Weakest sector + PE recommendations
        recommendation = self._build_recommendation()

        message = (
            f"🚨 MARKET SHOCK RESPONSE\n\n"
            f"Trigger : {reason}\n"
            f"Time    : "
            f"{self.trigger_time.strftime('%H:%M:%S')}\n\n"
            f"ACTIONS TAKEN:\n"
            f"1. All open positions → EXITING NOW\n"
            f"2. New long entries → DISABLED\n\n"
            f"{recommendation}"
        )

        if self.telegram is not None:
            try:
                self.telegram.send(message)
            except Exception:
                pass

    # --------------------------------------------------

    def _weakest_sector(self):
        """
        Weakest sector by live change across profiles.
        """
        sector_changes = {}

        try:
            for symbol, profile in (
                self.company_intelligence.profiles.items()
            ):
                sector = profile.get("sector", "")
                if not sector:
                    continue

                change = price_engine.get_change(symbol)
                if change is None:
                    continue

                sector_changes.setdefault(
                    sector, []
                ).append((symbol, change))

            worst_sector = None
            worst_avg = 999.0

            for sector, rows in sector_changes.items():
                if len(rows) < 3:
                    continue
                avg = sum(c for _, c in rows) / len(rows)
                if avg < worst_avg:
                    worst_avg = avg
                    worst_sector = sector

            if worst_sector is None:
                return None, None, []

            weakest_stocks = sorted(
                sector_changes[worst_sector],
                key=lambda x: x[1],
            )[:3]

            return worst_sector, worst_avg, weakest_stocks

        except Exception:
            return None, None, []

    # --------------------------------------------------

    @staticmethod
    def _atm_strike(price):
        if price >= 1000:
            step = 50
        elif price >= 300:
            step = 20
        elif price >= 100:
            step = 10
        else:
            step = 5
        return int(round(price / step) * step)

    # --------------------------------------------------

    def _build_recommendation(self):
        sector, avg, stocks = self._weakest_sector()

        if sector is None:
            return (
                "3. PE SETUP: market data insufficient "
                "for sector ranking — consider NIFTY "
                "ATM PE manually."
            )

        lines = [
            f"3. DOWNSIDE SETUP (weakest sector):",
            f"   Sector: {sector} ({avg:+.2f}% avg)",
            "",
            "   ATM PE candidates (F&O, weakest first):",
        ]

        added = 0
        for symbol, change in stocks:
            profile = (
                self.company_intelligence.get_profile(
                    symbol
                )
            )
            is_fno = str(
                profile.get("fno", "")
            ).strip().upper() in (
                "YES", "Y", "TRUE", "1", "FNO"
            )

            ltp = price_engine.get_ltp(symbol)
            if not ltp:
                continue

            strike = self._atm_strike(ltp)
            tag = "F&O" if is_fno else "no F&O"

            lines.append(
                f"   • {symbol} ({change:+.1f}%) "
                f"@ ₹{ltp:.0f} → BUY {strike} PE "
                f"[{tag}]"
            )
            added += 1

        if added == 0:
            lines.append("   (no priced candidates)")

        lines += [
            "",
            "   ⚠ Option orders are OPERATOR-EXECUTED",
            "   in this version (option feed",
            "   subscription pending for auto-manage).",
        ]

        return "\n".join(lines)

    # --------------------------------------------------

    def status(self):
        return {
            "enabled": SHOCK_RESPONDER_ENABLED,
            "triggered": self.triggered,
            "reason": self.trigger_reason,
            "time": (
                self.trigger_time.strftime("%H:%M:%S")
                if self.trigger_time else None
            ),
        }
