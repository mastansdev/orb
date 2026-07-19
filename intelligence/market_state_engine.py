"""
==========================================================
Market State Engine
==========================================================

Live market regime from the bot's own tick data:

    TRENDING_UP / TRENDING_DOWN / BEARISH /
    CHOPPY / FLAT / WARMUP

Inputs: per-stock day change from the Price Engine
(breadth = % advancing, average change).

Consumers:
    • Risk Governor  → scales daily limits
    • Shock Responder → breadth-collapse detection
    • /market command

This engine NEVER trades.

Author : H&M ORB AUTO TRADER
==========================================================
"""

from intelligence.price_engine import price_engine


class MarketStateEngine:

    MIN_SAMPLE = 50

    def __init__(self):
        self.last_state = {"regime": "WARMUP"}

    # --------------------------------------------------

    def compute(self):
        advances = 0
        declines = 0
        total_change = 0.0
        sample = 0

        for stock in price_engine.prices.values():
            if (
                stock["previous_close"] is None
                or stock["ltp"] is None
            ):
                continue

            change = stock["change"]
            sample += 1
            total_change += change

            if change > 0.15:
                advances += 1
            elif change < -0.15:
                declines += 1

        if sample < self.MIN_SAMPLE:
            self.last_state = {
                "regime": "WARMUP",
                "sample": sample,
                "breadth_pct": None,
                "avg_change": None,
            }
            return self.last_state

        breadth_pct = round(advances / sample * 100, 1)
        avg_change = round(total_change / sample, 2)

        # ---------------------------------
        # Regime classification
        # ---------------------------------
        if breadth_pct <= 25 and avg_change <= -1.0:
            regime = "BEARISH"
        elif breadth_pct >= 65 and avg_change >= 0.5:
            regime = "TRENDING_UP"
        elif breadth_pct <= 35 and avg_change <= -0.5:
            regime = "TRENDING_DOWN"
        elif abs(avg_change) < 0.25:
            regime = "FLAT"
        else:
            regime = "CHOPPY"

        self.last_state = {
            "regime": regime,
            "sample": sample,
            "advances": advances,
            "declines": declines,
            "breadth_pct": breadth_pct,
            "avg_change": avg_change,
        }

        return self.last_state

    # --------------------------------------------------

    def report(self):
        s = self.last_state

        if s.get("regime") == "WARMUP":
            return (
                "MARKET STATE\n\nWarming up "
                f"({s.get('sample', 0)} stocks priced)."
            )

        return (
            "MARKET STATE\n\n"
            f"Regime    : {s['regime']}\n"
            f"Breadth   : {s['breadth_pct']}% advancing "
            f"({s['advances']}▲ / {s['declines']}▼)\n"
            f"Avg Move  : {s['avg_change']:+.2f}%\n"
            f"Sample    : {s['sample']} stocks"
        )


market_state_engine = MarketStateEngine()
