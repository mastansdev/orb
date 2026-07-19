"""
==========================================================
Edge Analyzer
==========================================================

Mission
-------
Answer the ONLY question that matters before anything
else is built:

    DOES THIS SYSTEM HAVE AN EDGE, NET OF COSTS?

Reads the trade log (v2 schema) and computes:

    • Trades, win rate, avg win / avg loss
    • Gross expectancy per trade
    • Estimated all-in charges per trade
      (brokerage, STT, exchange, SEBI, stamp, GST)
    • NET expectancy per trade  ← the verdict
    • Profit factor
    • Breakdown by hour of entry
    • Breakdown by sector
    • Breakdown by conviction band
      (does higher conviction actually win more?)

Honesty rules
-------------
• Below MIN_TRADES the verdict is "INSUFFICIENT DATA",
  never a conclusion.
• Charges are estimated with the same rates as
  ChargesCalculator.

This module NEVER:
    • trades
    • modifies any file

Author : H&M ORB AUTO TRADER
==========================================================
"""

import csv
import os

from config import TRADE_LOG_FILE


class EdgeAnalyzer:

    MIN_TRADES = 30

    # Same cost model as ChargesCalculator
    BROKERAGE_PER_ORDER = 20.00
    STT_RATE = 0.00025            # sell side
    EXCHANGE_RATE = 0.000030699   # both sides
    SEBI_RATE = 0.000001          # both sides
    STAMP_RATE = 0.00003          # buy side
    GST_RATE = 0.18

    def __init__(self, log_file=None):
        self.log_file = log_file or TRADE_LOG_FILE

    # --------------------------------------------------

    def _load(self):
        if not os.path.exists(self.log_file):
            return []

        trades = []

        try:
            with open(
                self.log_file, newline="", encoding="utf-8"
            ) as f:
                for row in csv.DictReader(f):
                    # Exclude test artifacts
                    if "SMOKETEST" in (
                        row.get("Sector", "") or ""
                    ):
                        continue

                    try:
                        trades.append({
                            "date": row.get("Date", ""),
                            "entry_time": row.get(
                                "EntryTime", ""
                            ),
                            "symbol": row.get("Symbol", ""),
                            "sector": row.get("Sector", "")
                            or "UNKNOWN",
                            "qty": int(
                                float(row.get("Qty", 0))
                            ),
                            "entry": float(
                                row.get("EntryPrice", 0)
                            ),
                            "exit": float(
                                row.get("ExitPrice", 0)
                            ),
                            "pnl": float(row.get("PnL", 0)),
                            "exit_reason": row.get(
                                "ExitReason", ""
                            ),
                            "conviction": float(
                                row.get("Conviction", 0) or 0
                            ),
                        })
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            print(f"[EDGE] Log read failed: {e}")

        return trades

    # --------------------------------------------------

    def _charges(self, trade):
        """
        Estimated all-in cost for one round trip.
        """
        buy_turnover = trade["entry"] * trade["qty"]
        sell_turnover = trade["exit"] * trade["qty"]
        total = buy_turnover + sell_turnover

        brokerage = 2 * self.BROKERAGE_PER_ORDER
        stt = sell_turnover * self.STT_RATE
        exchange = total * self.EXCHANGE_RATE
        sebi = total * self.SEBI_RATE
        stamp = buy_turnover * self.STAMP_RATE
        gst = (brokerage + exchange + sebi) * self.GST_RATE

        return brokerage + stt + exchange + sebi + stamp + gst

    # --------------------------------------------------

    def analyze(self):
        trades = self._load()

        result = {
            "trades": len(trades),
            "verdict": None,
        }

        if not trades:
            result["verdict"] = "NO DATA"
            return result

        wins = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] <= 0]

        gross_pnl = sum(t["pnl"] for t in trades)
        total_charges = sum(
            self._charges(t) for t in trades
        )
        net_pnl = gross_pnl - total_charges

        gross_win = sum(t["pnl"] for t in wins)
        gross_loss = abs(sum(t["pnl"] for t in losses))

        result.update({
            "win_rate": round(
                len(wins) / len(trades) * 100, 1
            ),
            "avg_win": round(
                gross_win / len(wins), 2
            ) if wins else 0,
            "avg_loss": round(
                gross_loss / len(losses), 2
            ) if losses else 0,
            "gross_pnl": round(gross_pnl, 2),
            "total_charges": round(total_charges, 2),
            "net_pnl": round(net_pnl, 2),
            "gross_expectancy": round(
                gross_pnl / len(trades), 2
            ),
            "charges_per_trade": round(
                total_charges / len(trades), 2
            ),
            "net_expectancy": round(
                net_pnl / len(trades), 2
            ),
            "profit_factor": round(
                gross_win / gross_loss, 2
            ) if gross_loss > 0 else None,
        })

        # Verdict
        if len(trades) < self.MIN_TRADES:
            result["verdict"] = (
                f"INSUFFICIENT DATA "
                f"({len(trades)}/{self.MIN_TRADES} trades) "
                f"— keep paper trading"
            )
        elif result["net_expectancy"] > 0:
            result["verdict"] = (
                f"POSITIVE net expectancy "
                f"(₹{result['net_expectancy']}/trade) — "
                f"edge present so far; verify across regimes"
            )
        else:
            result["verdict"] = (
                f"NEGATIVE net expectancy "
                f"(₹{result['net_expectancy']}/trade) — "
                f"NO EDGE at current costs; do not go live"
            )

        # Breakdowns
        result["by_hour"] = self._bucket(
            trades,
            lambda t: (
                t["entry_time"][:2] + ":00"
                if t["entry_time"] else "?"
            ),
        )
        result["by_sector"] = self._bucket(
            trades, lambda t: t["sector"]
        )
        result["by_conviction"] = self._bucket(
            trades, self._conviction_band
        )
        result["by_exit"] = self._bucket(
            trades, lambda t: t["exit_reason"] or "?"
        )

        return result

    # --------------------------------------------------

    @staticmethod
    def _conviction_band(trade):
        c = trade["conviction"]
        if c >= 85:
            return "85+"
        if c >= 70:
            return "70-84"
        if c >= 55:
            return "55-69"
        if c >= 40:
            return "40-54"
        return "<40"

    # --------------------------------------------------

    def _bucket(self, trades, key_fn):
        buckets = {}

        for t in trades:
            key = key_fn(t)
            b = buckets.setdefault(
                key, {"trades": 0, "wins": 0, "pnl": 0.0}
            )
            b["trades"] += 1
            if t["pnl"] > 0:
                b["wins"] += 1
            b["pnl"] += t["pnl"]

        out = []
        for key, b in buckets.items():
            out.append({
                "bucket": key,
                "trades": b["trades"],
                "win_rate": round(
                    b["wins"] / b["trades"] * 100, 1
                ),
                "pnl": round(b["pnl"], 2),
            })

        out.sort(key=lambda x: -x["pnl"])
        return out

    # --------------------------------------------------

    def report(self):
        r = self.analyze()

        if r["verdict"] == "NO DATA":
            return "EDGE ANALYSIS\n\nNo trades logged yet."

        lines = [
            "EDGE ANALYSIS (net of charges)",
            "",
            f"Trades          : {r['trades']}",
            f"Win Rate        : {r['win_rate']}%",
            f"Avg Win / Loss  : ₹{r['avg_win']} / ₹{r['avg_loss']}",
            f"Profit Factor   : {r['profit_factor']}",
            "",
            f"Gross PnL       : ₹{r['gross_pnl']:,.0f}",
            f"Est. Charges    : ₹{r['total_charges']:,.0f}",
            f"NET PnL         : ₹{r['net_pnl']:,.0f}",
            "",
            f"Gross / trade   : ₹{r['gross_expectancy']}",
            f"Charges / trade : ₹{r['charges_per_trade']}",
            f"NET / trade     : ₹{r['net_expectancy']}",
            "",
            f"VERDICT: {r['verdict']}",
        ]

        def add_breakdown(title, rows, limit=5):
            lines.append("")
            lines.append(f"{title}:")
            for row in rows[:limit]:
                lines.append(
                    f"• {row['bucket']}: "
                    f"{row['trades']}t, "
                    f"{row['win_rate']}%, "
                    f"₹{row['pnl']:,.0f}"
                )

        add_breakdown("By Conviction", r["by_conviction"])
        add_breakdown("By Hour", r["by_hour"])
        add_breakdown("By Sector", r["by_sector"])
        add_breakdown("By Exit", r["by_exit"])

        return "\n".join(lines)


# ------------------------------------------------------

if __name__ == "__main__":
    print(EdgeAnalyzer().report())
