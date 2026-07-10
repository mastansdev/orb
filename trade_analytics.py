import csv
import os


class TradeAnalytics:

    def __init__(self, file_path="trade_log.csv"):

        self.file_path = file_path

    # -------------------------------------------------

    def print_report(self):

        if not os.path.exists(self.file_path):

            print("\nNo trade log found.\n")
            return

        trades = []

        with open(self.file_path, "r", newline="") as file:

            reader = csv.DictReader(file)

            for row in reader:

                try:
                    row["PnL"] = float(row["PnL"])
                    trades.append(row)
                except:
                    continue

        if len(trades) == 0:

            print("\nNo completed trades.\n")
            return

        total = len(trades)

        winners = [t for t in trades if t["PnL"] > 0]
        losers = [t for t in trades if t["PnL"] < 0]

        gross_profit = sum(t["PnL"] for t in winners)
        gross_loss = sum(t["PnL"] for t in losers)

        net = gross_profit + gross_loss

        target = sum(1 for t in trades if t["Reason"] == "TARGET")
        stoploss = sum(1 for t in trades if t["Reason"] == "STOPLOSS")
        time_exit = sum(1 for t in trades if t["Reason"] == "TIME_EXIT")

        win_rate = (
            len(winners) / total * 100
            if total else 0
        )

        avg_win = (
            gross_profit / len(winners)
            if winners else 0
        )

        avg_loss = (
            gross_loss / len(losers)
            if losers else 0
        )

        best = max((t["PnL"] for t in trades), default=0)
        worst = min((t["PnL"] for t in trades), default=0)

        print()
        print("=" * 65)
        print("               TRADE ANALYTICS REPORT")
        print("=" * 65)

        print(f"Total Trades      : {total}")
        print(f"Winners           : {len(winners)}")
        print(f"Losers            : {len(losers)}")
        print(f"Win Rate          : {win_rate:.2f}%")

        print()

        print(f"Gross Profit      : ₹{gross_profit:.2f}")
        print(f"Gross Loss        : ₹{gross_loss:.2f}")
        print(f"Net PnL           : ₹{net:.2f}")

        print()

        print(f"Average Winner    : ₹{avg_win:.2f}")
        print(f"Average Loser     : ₹{avg_loss:.2f}")

        print()

        print(f"Best Trade        : ₹{best:.2f}")
        print(f"Worst Trade       : ₹{worst:.2f}")

        print()

        print(f"Target            : {target}")
        print(f"StopLoss          : {stoploss}")
        print(f"Time Exit         : {time_exit}")

        print("=" * 65)
        print()