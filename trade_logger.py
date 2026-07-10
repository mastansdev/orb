import csv
import os

from config import TRADE_LOG_FILE


class TradeLogger:

    def __init__(self):

        self.file_name = TRADE_LOG_FILE

        if not os.path.exists(self.file_name):

            with open(self.file_name, "w", newline="", encoding="utf-8") as file:

                writer = csv.writer(file)

                writer.writerow([
                    "Date",
                    "Time",
                    "Symbol",
                    "Entry",
                    "Exit",
                    "Qty",
                    "PnL",
                    "Reason"
                ])

    # --------------------------------------------------

    def log_trade(
        self,
        date,
        time,
        symbol,
        entry,
        exit_price,
        qty,
        pnl,
        reason
    ):

        with open(self.file_name, "a", newline="", encoding="utf-8") as file:

            writer = csv.writer(file)

            writer.writerow([
                date,
                time,
                symbol,
                round(entry, 2),
                round(exit_price, 2),
                int(qty),
                round(pnl, 2),
                reason
            ])