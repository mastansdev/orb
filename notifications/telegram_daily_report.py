import os
import csv
from dotenv import load_dotenv

from notifications.telegram_notifier import TelegramNotifier

load_dotenv()


class TelegramDailyReport:

    def __init__(self):

        self.telegram = TelegramNotifier(
            os.getenv("TELEGRAM_BOT_TOKEN"),
            os.getenv("TELEGRAM_CHAT_ID")
        )

    # --------------------------------------------

    def send_report(self, file_path="trade_log.csv"):

        if not os.path.exists(file_path):
            print("Trade log not found.")
            return

        trades = []

        with open(file_path, "r", newline="") as file:

            reader = csv.DictReader(file)

            for row in reader:

                try:
                    row["PnL"] = float(row["PnL"])
                    trades.append(row)
                except:
                    continue

        if len(trades) == 0:

            self.telegram.send(
                "📊 DAILY TRADING REPORT\n\n"
                "No trades executed today."
            )

            return

        total = len(trades)

        winners = [t for t in trades if t["PnL"] > 0]
        losers = [t for t in trades if t["PnL"] < 0]

        gross_profit = sum(t["PnL"] for t in winners)
        gross_loss = sum(t["PnL"] for t in losers)

        net = gross_profit + gross_loss

        target = sum(
            1 for t in trades
            if t["Reason"] == "TARGET"
        )

        stoploss = sum(
            1 for t in trades
            if t["Reason"] == "STOPLOSS"
        )

        time_exit = sum(
            1 for t in trades
            if t["Reason"] == "TIME_EXIT"
        )

        win_rate = (
            len(winners) / total * 100
            if total else 0
        )

        message = (
            "📊 DAILY TRADING REPORT\n\n"

            f"Total Trades : {total}\n"
            f"Winners : {len(winners)}\n"
            f"Losers : {len(losers)}\n"
            f"Win Rate : {win_rate:.2f}%\n\n"

            f"Gross Profit : ₹{gross_profit:.2f}\n"
            f"Gross Loss : ₹{gross_loss:.2f}\n"
            f"Net PnL : ₹{net:.2f}\n\n"

            f"Target : {target}\n"
            f"StopLoss : {stoploss}\n"
            f"Time Exit : {time_exit}"
        )

        self.telegram.send(message)