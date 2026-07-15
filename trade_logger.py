import csv
import os
from datetime import datetime

from config import TRADE_LOG_FILE


class TradeLogger:

    def __init__(self):

        self.file_name = TRADE_LOG_FILE

        if not os.path.exists(self.file_name):

            with open(self.file_name, "w", newline="", encoding="utf-8") as file:

                writer = csv.writer(file)

                writer.writerow([
                    "Entry Date",
                    "Entry Time",
                    "Exit Date",
                    "Exit Time",
                    "Holding Seconds",
                    "Symbol",
                    "Qty",
                    "Entry",
                    "Exit",
                    "PnL",
                    "Reason"
                ])

    # --------------------------------------------------

    def log_trade(
        self,
        entry_date,
        entry_time,
        exit_date,
        exit_time,
        symbol,
        entry,
        exit_price,
        qty,
        pnl,
        reason
    ):

        with open(self.file_name, "a", newline="", encoding="utf-8") as file:

            writer = csv.writer(file)

            entry_dt = datetime.strptime(
                f"{entry_date} {entry_time}",
                "%Y-%m-%d %H:%M:%S"
            )
            exit_dt = datetime.strptime(
                f"{exit_date} {exit_time}",
                "%Y-%m-%d %H:%M:%S"
            )
            holding_seconds = int(
                (exit_dt - entry_dt).total_seconds()
            )

            writer.writerow([
                entry_date,
                entry_time,
                exit_date,
                exit_time,
                holding_seconds,
                symbol,
                int(qty),
                round(entry, 2),
                round(exit_price, 2),
                round(pnl, 2),
                reason
            ])