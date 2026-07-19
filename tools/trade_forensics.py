import os
import sys
import csv
from datetime import datetime

# --------------------------------------------------
# Add project root to Python path
# --------------------------------------------------

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --------------------------------------------------

from config import TRADE_LOG_FILE


class TradeForensics:

    def __init__(self):
        self.file_name = TRADE_LOG_FILE
        self.trades = []
        self.trade_date = datetime.now().strftime("%Y-%m-%d")

    # --------------------------------------------------

    def load_trades(self, trade_date=None):
        self.trades.clear()

        if trade_date is None:
            trade_date = self.trade_date

        self.trade_date = trade_date

        if not os.path.exists(self.file_name):
            print(f"\nTrade log not found : {self.file_name}")
            return

        with open(
            self.file_name,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:
            reader = csv.DictReader(file)

            for row in reader:
                if row["Date"] != trade_date:
                    continue

                # 1. Map entry and exit prices using the new header naming
                row["EntryPrice"] = float(row["EntryPrice"])
                row["ExitPrice"] = float(row["ExitPrice"])
                row["Qty"] = int(row["Qty"])
                row["PnL"] = float(row["PnL"])

                self.trades.append(row)

        # 1. Sort using EntryTime instead of generic Time
        self.trades.sort(key=lambda x: x["EntryTime"])

    # --------------------------------------------------

    def print_session_validation(self):
        print()
        print("=" * 70)
        print("SESSION VALIDATION")
        print("=" * 70)

        if not self.trades:
            print("Status          : NO TRADES")
            return

        # 2. Extract first and last trade timings using EntryTime
        first_trade = self.trades[0]["EntryTime"]
        last_trade = self.trades[-1]["EntryTime"]

        print(f"First Trade     : {first_trade}")
        print(f"Last Trade      : {last_trade}")

        hh, mm, _ = map(int, first_trade.split(":"))

        if hh > 9 or (hh == 9 and mm > 45):
            print("Status          : WARNING")
            print("Observation     : Trading started much later than expected.")
            print("Recommendation  : Ignore time-based strategy analysis.")
        else:
            print("Status          : VALID")
            print("Recommendation  : Session suitable for analysis.")

    # --------------------------------------------------

    def print_report(self):
        print()
        print("=" * 70)
        print("                 ORB AUTO TRADER - TRADE FORENSICS")
        print("=" * 70)
        print(f"Trading Date    : {self.trade_date}")
        print("=" * 70)

        if not self.trades:
            print("No trades found.")
            print("=" * 70)
            return

        total = len(self.trades)

        winners = [t for t in self.trades if t["PnL"] > 0]
        losers = [t for t in self.trades if t["PnL"] < 0]

        gross_profit = sum(t["PnL"] for t in winners)
        gross_loss = sum(t["PnL"] for t in losers)

        net = gross_profit + gross_loss

        average_profit = (
            gross_profit / len(winners)
            if winners else 0
        )

        average_loss = (
            abs(gross_loss) / len(losers)
            if losers else 0
        )

        profit_factor = (
            gross_profit / abs(gross_loss)
            if gross_loss != 0 else 0
        )

        expectancy = (
            net / total
            if total else 0
        )

        win_rate = len(winners) / total * 100

        largest_winner = (
            max(winners, key=lambda x: x["PnL"])
            if winners else None
        )
        largest_loser = (
            min(losers, key=lambda x: x["PnL"])
            if losers else None
        )

        print(f"Trades          : {total}")
        print(f"Winners         : {len(winners)}")
        print(f"Losers          : {len(losers)}")
        print(f"Win Rate        : {win_rate:.2f}%")

        print()

        print(f"Gross Profit    : {gross_profit:.2f}")
        print(f"Gross Loss      : {gross_loss:.2f}")
        print(f"Net PnL         : {net:.2f}")

        print()

        print(f"Average Winner  : {average_profit:.2f}")
        print(f"Average Loser   : {average_loss:.2f}")
        print(f"Profit Factor   : {profit_factor:.2f}")
        print(f"Expectancy      : {expectancy:.2f}")

        print()

        # --- REPLACED SECTION ---
        if largest_winner:
            print(
                f"Largest Winner  : {largest_winner['Symbol']} ({largest_winner['PnL']:.2f})"
            )
        else:
            print("Largest Winner  : N/A")

        if largest_loser:
            print(
                f"Largest Loser   : {largest_loser['Symbol']} ({largest_loser['PnL']:.2f})"
            )
        else:
            print("Largest Loser   : N/A")
        # ------------------------

        self.print_session_validation()

        exit_analysis = {}

        # 3. Pull from ExitReason instead of Reason
        for trade in self.trades:
            reason = trade["ExitReason"]
            exit_analysis[reason] = (
                exit_analysis.get(reason, 0) + 1
            )

        print()
        print("=" * 70)
        print("EXIT ANALYSIS")
        print("=" * 70)

        for reason, count in sorted(exit_analysis.items()):
            print(f"{reason:<20}{count}")

        print()
        print("=" * 70)
        print("TOP 10 WINNERS")
        print("=" * 70)

        for trade in sorted(
            winners,
            key=lambda x: x["PnL"],
            reverse=True
        )[:10]:
            print(
                f"{trade['Symbol']:<20}"
                f"{trade['PnL']:>10.2f}"
            )

        print()
        print("=" * 70)
        print("TOP 10 LOSERS")
        print("=" * 70)

        for trade in sorted(
            losers,
            key=lambda x: x["PnL"]
        )[:10]:
            print(
                f"{trade['Symbol']:<20}"
                f"{trade['PnL']:>10.2f}"
            )

        print()
        print("=" * 70)
        print("ENTRY TIME ANALYSIS")
        print("=" * 70)

        slots = {
            "09:30-09:45": [],
            "09:45-10:00": [],
            "10:00-10:30": [],
            "10:30-11:00": [],
            "11:00-12:00": [],
            "12:00-13:00": [],
            "13:00-14:00": [],
            "14:00-15:15": []
        }

        # 4. Use EntryTime to slot trades into their corresponding hours
        for trade in self.trades:
            hour, minute, _ = map(int, trade["EntryTime"].split(":"))

            if hour == 9 and minute < 45:
                slots["09:30-09:45"].append(trade)
            elif hour == 9:
                slots["09:45-10:00"].append(trade)
            elif hour == 10 and minute < 30:
                slots["10:00-10:30"].append(trade)
            elif hour == 10:
                slots["10:30-11:00"].append(trade)
            elif hour == 11:
                slots["11:00-12:00"].append(trade)
            elif hour == 12:
                slots["12:00-13:00"].append(trade)
            elif hour == 13:
                slots["13:00-14:00"].append(trade)
            else:
                slots["14:00-15:15"].append(trade)

        for slot, trades in slots.items():
            pnl = sum(t["PnL"] for t in trades)
            print(
                f"{slot:<15}"
                f"Trades:{len(trades):>4}"
                f"   PnL:{pnl:>10.2f}"
            )

        print()
        print("=" * 70)


if __name__ == "__main__":
    report = TradeForensics()
    report.load_trades()
    report.print_report()