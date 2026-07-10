"""
==========================================================
Position Monitor

Institutional Grade ORB Auto Trading Bot

Read-only monitor.

Responsibilities
----------------
• Read open_positions.json
• Display live open positions
• Calculate Floating MTM
• Refresh dashboard

Never
-----
• Modify trades
• Place orders
• Block capital
• Import Engine
==========================================================
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime

# ==========================================================
# Configuration
# ==========================================================

# Change 5: Added Version tracking constant
VERSION = "1.0"

POSITIONS_FILE = "open_positions.json"
REFRESH_INTERVAL = 1.0
CLEAR_SCREEN = True


# ==========================================================
# Position Monitor
# ==========================================================

class PositionMonitor:

    def __init__(self):
        self.positions = {}
        self.last_refresh = None

    # ------------------------------------------------------

    def run(self):
        while True:
            try:
                self._load_positions()
                self._render()
            except KeyboardInterrupt:
                print("\nPosition Monitor stopped.")
                break
            except Exception as exc:
                print(f"\nERROR : {exc}")
            
            time.sleep(REFRESH_INTERVAL)

    # ------------------------------------------------------

    def _load_positions(self):
        if not os.path.exists(POSITIONS_FILE):
            self.positions = {}
            return
        
        # Change 1: Wrapped JSON loading to defend against partial file writes
        try:
            with open(POSITIONS_FILE, "r", encoding="utf-8") as file:
                self.positions = json.load(file)
        except json.JSONDecodeError:
            # Skip updating this iteration if file is currently being rewritten
            return
            
        self.last_refresh = datetime.now()

    # ------------------------------------------------------

    def _render(self):
        # Change 3: Preserved for now; ready to swap for 'rich' downstream
        if CLEAR_SCREEN:
            os.system("cls" if os.name == "nt" else "clear")

        # Change 4: Expanded dashboard width to 120 chars
        print("=" * 120)
        # Change 5: Added version tag to dashboard title
        print(f"LIVE TRADING DASHBOARD (Position Monitor v{VERSION})")
        print("=" * 120)

        now = datetime.now().strftime("%H:%M:%S")
        refresh = (
            self.last_refresh.strftime("%H:%M:%S") 
            if self.last_refresh 
            else "N/A"
        )

        print(f"Time             : {now}")
        print(f"Last Refresh     : {refresh}")

        total_positions = len(self.positions)
        print(f"Open Positions   : {total_positions}")
        print("-" * 120)

        print(
            f"{'Symbol':<15}"
            f"{'Qty':>8}"
            f"{'Entry':>12}"
            f"{'SL':>12}"
            f"{'Target':>12}"
            f"{'Stage':>14}"
            f"{'Score':>8}"
        )
        print("-" * 120)

        protected = 0
        risk = 0
        trailing = 0
        total_capital = 0

        # Change 2: Sorting positions chronologically by entry_time
        sorted_positions = sorted(
            self.positions.items(),
            key=lambda x: x[1].get("entry_time", "")
        )

        for security_id, position in sorted_positions:
            stage = position.get("stage", "")

            if stage == "PROTECTED":
                protected += 1

            if stage == "RISK":
                risk += 1

            if position.get("trail_active", False):
                trailing += 1

            total_capital += position.get("capital_used", 0)

            score = position.get("decision", {}).get("score", 0)

            print(
                f"{position.get('symbol',''):<15}"
                f"{position.get('qty',0):>8}"
                f"{position.get('entry',0):>12.2f}"
                f"{position.get('stop_loss',0):>12.2f}"
                f"{position.get('target',0):>12.2f}"
                f"{stage:>14}"
                f"{score:>8}"
            )

        print("-" * 120)
        print(f"Risk Trades      : {risk}")
        print(f"Protected Trades : {protected}")
        print(f"Trailing Active  : {trailing}")
        print(f"Capital Used     : ₹{total_capital:,.2f}")
        print("=" * 120)


if __name__ == "__main__":
    monitor = PositionMonitor()
    monitor.run()