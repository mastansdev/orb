from collections import Counter
from datetime import datetime
from pathlib import Path
import csv


class TradeForensicsV2:
    """
    Institutional Trade Forensics

    Responsibilities
    ----------------
    Analyze completed trades and produce an
    institutional-quality trading report.

    Never
    -----
    - Place trades
    - Modify trades
    - Connect to Dhan
    - Change portfolio
    """

    def __init__(self, trade_log_file):

        self.trade_log_file = Path(trade_log_file)

        self.trades = []

    # --------------------------------------------------

    def load(self):

        self.trades.clear()

        with open(
            self.trade_log_file,
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(
                file,
                delimiter="\t"
            )

            for row in reader:
                self.trades.append(row)

    # --------------------------------------------------

    def summary(self):

        exits = Counter()

        total_pnl = 0.0

        winners = 0

        losers = 0

        for trade in self.trades:

            exit_type = trade["Exit Reason"]

            pnl = float(trade["PnL"])

            exits[exit_type] += 1

            total_pnl += pnl

            if pnl >= 0:
                winners += 1
            else:
                losers += 1

        print()

        print("=" * 70)
        print("SESSION SUMMARY")
        print("=" * 70)

        print(f"Trades        : {len(self.trades)}")
        print(f"Winners       : {winners}")
        print(f"Losers        : {losers}")

        if self.trades:

            print(
                f"Win Rate      : "
                f"{(winners/len(self.trades))*100:.2f}%"
            )

        print()

        print("Exit Distribution")

        for k, v in exits.items():

            print(f"{k:15} : {v}")

        print()

        print(f"Net PnL       : ₹{total_pnl:,.2f}")

        print("=" * 70)

    # --------------------------------------------------

    def run(self):

        self.load()

        self.summary()


if __name__ == "__main__":

    analyzer = TradeForensicsV2(

        "trade_log.csv"

    )

    analyzer.run()