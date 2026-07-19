import os
import json
from datetime import datetime


class EventLogger:

    def __init__(self, log_folder="logs/events"):

        self.log_folder = log_folder
        os.makedirs(self.log_folder, exist_ok=True)

    # ---------------------------------------------------------

    def _get_file(self):

        return os.path.join(
            self.log_folder,
            f"{datetime.now().strftime('%Y%m%d')}.jsonl"
        )

    # ---------------------------------------------------------

    def log(
        self,
        level,
        module,
        event,
        message="",
        symbol="",
        trade_id="",
        data=None
    ):

        record = {

            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],

            "level": level,

            "module": module,

            "event": event,

            "symbol": symbol,

            "trade_id": trade_id,

            "message": message,

            "data": data if data else {}
        }

        with open(
            self._get_file(),
            "a",
            encoding="utf-8"
        ) as file:

            file.write(json.dumps(record) + "\n")

    # ---------------------------------------------------------

    def system(self, event, message="", data=None):

        self.log(
            "SYSTEM",
            "SYSTEM",
            event,
            message,
            data=data
        )

    # ---------------------------------------------------------

    def strategy(
        self,
        event,
        symbol="",
        trade_id="",
        message="",
        data=None
    ):

        self.log(
            "STRATEGY",
            "STRATEGY",
            event,
            message,
            symbol,
            trade_id,
            data
        )

    # ---------------------------------------------------------

    def trade(
        self,
        event,
        symbol="",
        trade_id="",
        message="",
        data=None
    ):

        self.log(
            "TRADE",
            "TRADE",
            event,
            message,
            symbol,
            trade_id,
            data
        )

    # ---------------------------------------------------------

    def execution(
        self,
        event,
        symbol="",
        trade_id="",
        message="",
        data=None
    ):

        self.log(
            "EXECUTION",
            "EXECUTION",
            event,
            message,
            symbol,
            trade_id,
            data
        )

    # ---------------------------------------------------------

    def risk(
        self,
        event,
        symbol="",
        trade_id="",
        message="",
        data=None
    ):

        self.log(
            "RISK",
            "RISK",
            event,
            message,
            symbol,
            trade_id,
            data
        )

    # ---------------------------------------------------------

    def warning(
        self,
        event,
        message="",
        data=None
    ):

        self.log(
            "WARNING",
            "WARNING",
            event,
            message,
            data=data
        )

    # ---------------------------------------------------------

    def error(
        self,
        event,
        message="",
        data=None
    ):

        self.log(
            "ERROR",
            "ERROR",
            event,
            message,
            data=data
        )


event_logger = EventLogger()