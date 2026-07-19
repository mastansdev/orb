"""
==========================================================
Execution Quality (Fills Logger + TCA seed)
==========================================================

Mission
-------
Measure execution, don't assume it.

Every order (paper or live) writes one row to
fills_log.csv:

    timestamp, mode, side, symbol, qty,
    intended_price, fill_price, slippage_rupees,
    slippage_bps, order_id, status

This is the seed of Transaction Cost Analysis:
after a few weeks, slippage_bps tells you the TRUE
cost of breakout entries — the number every backtest
silently gets wrong.

This module NEVER:
    • places orders
    • changes PnL accounting

Author : H&M ORB AUTO TRADER
==========================================================
"""

import csv
import os
from datetime import datetime
from threading import RLock


class ExecutionQuality:

    FILE_NAME = "fills_log.csv"

    HEADER = [
        "Timestamp", "Mode", "Side", "Symbol", "Qty",
        "IntendedPrice", "FillPrice",
        "SlippageRupees", "SlippageBps",
        "OrderId", "Status",
    ]

    def __init__(self, file_name=None):
        self.file_name = file_name or self.FILE_NAME
        self._lock = RLock()

        if not os.path.exists(self.file_name):
            try:
                with open(
                    self.file_name, "w",
                    newline="", encoding="utf-8"
                ) as f:
                    csv.writer(f).writerow(self.HEADER)
            except Exception:
                pass

    # --------------------------------------------------

    def record(
        self,
        mode,
        side,
        symbol,
        qty,
        intended_price,
        fill_price,
        order_id="",
        status="",
    ):
        """
        fill_price may be None (unknown/unconfirmed) —
        recorded as blank, slippage blank.
        """
        slippage_rupees = ""
        slippage_bps = ""

        if (
            fill_price is not None
            and intended_price
            and intended_price > 0
        ):
            # Signed so adverse slippage is positive:
            # BUY filled higher = +, SELL filled lower = +
            direction = 1 if side == "BUY" else -1
            slip = (
                (fill_price - intended_price) * direction
            )
            slippage_rupees = round(slip * qty, 2)
            slippage_bps = round(
                slip / intended_price * 10000, 1
            )

        try:
            with self._lock:
                with open(
                    self.file_name, "a",
                    newline="", encoding="utf-8"
                ) as f:
                    csv.writer(f).writerow([
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        mode,
                        side,
                        symbol,
                        qty,
                        round(intended_price, 2)
                        if intended_price else "",
                        round(fill_price, 2)
                        if fill_price is not None else "",
                        slippage_rupees,
                        slippage_bps,
                        order_id,
                        status,
                    ])
        except Exception as e:
            print(f"[TCA] Fill log failed: {e}")

    # --------------------------------------------------

    def summary(self, limit=500):
        """
        Rolling slippage summary for /execution.
        """
        if not os.path.exists(self.file_name):
            return None

        rows = []

        try:
            with open(
                self.file_name, newline="",
                encoding="utf-8"
            ) as f:
                rows = list(csv.DictReader(f))[-limit:]
        except Exception:
            return None

        graded = [
            r for r in rows
            if r.get("SlippageBps") not in ("", None)
        ]

        if not graded:
            return {
                "fills": len(rows),
                "graded": 0,
            }

        bps_values = [
            float(r["SlippageBps"]) for r in graded
        ]
        rupee_values = [
            float(r["SlippageRupees"]) for r in graded
        ]

        return {
            "fills": len(rows),
            "graded": len(graded),
            "avg_slippage_bps": round(
                sum(bps_values) / len(bps_values), 1
            ),
            "worst_slippage_bps": round(
                max(bps_values), 1
            ),
            "total_slippage_rupees": round(
                sum(rupee_values), 2
            ),
        }
