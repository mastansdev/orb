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
                    "Date",
                    "EntryTime",
                    "Symbol",
                    "Sector",
                    "Industry",
                    "Theme",
                    "Qty",
                    "EntryPrice",
                    "ExitTime",
                    "ExitPrice",
                    "PnL",
                    "HoldingSeconds",
                    "ExitReason",
                    "Conviction",
                    "TradeID"
                ])

    # --------------------------------------------------

    def log_trade(
        self,
        trade_date,
        entry_time,
        exit_time,
        symbol,
        sector,
        industry,
        theme,
        qty,
        entry_price,
        exit_price,
        pnl,
        exit_reason,
        conviction,
    ):
        with open(self.file_name, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            entry_dt = datetime.strptime(
                f"{trade_date} {entry_time}", 
                "%Y-%m-%d %H:%M:%S"
            )
            exit_dt = datetime.strptime(
                f"{trade_date} {exit_time}", 
                "%Y-%m-%d %H:%M:%S"
            )
            holding_seconds = int((exit_dt - entry_dt).total_seconds())

            writer.writerow([
                trade_date,
                entry_time,
                symbol,
                sector or "",
                industry or "",
                theme or "",
                int(qty),
                round(float(entry_price), 2),
                exit_time,
                round(float(exit_price), 2),
                round(float(pnl), 2),
                holding_seconds,
                exit_reason,
                conviction if conviction is not None else 0,
                f"{trade_date.replace('-', '')}_{symbol}_{entry_time.replace(':', '')}",
            ])