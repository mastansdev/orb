import csv
from datetime import datetime

from core.engine import Engine


class MarketReplay:

    def __init__(self):

        self.engine = Engine()

    # --------------------------------------------------

    def replay(self, csv_file):

        print("=" * 70)
        print("MARKET REPLAY")
        print("=" * 70)

        total_ticks = 0

        with open(csv_file, newline="") as file:

            reader = csv.DictReader(file)

            for row in reader:

                security_id = str(row["security_id"])
                symbol = row["symbol"]
                ltp = float(row["ltp"])
                ltt = row["time"]

                self.engine.process_tick(
                    security_id=security_id,
                    symbol=symbol,
                    ltp=ltp,
                    ltt=ltt
                )

                total_ticks += 1

        print()
        print("=" * 70)
        print("REPLAY COMPLETED")
        print("=" * 70)
        print(f"Ticks Processed : {total_ticks}")
        print("=" * 70)


# --------------------------------------------------

if __name__ == "__main__":

    replay = MarketReplay()

    replay.replay(
        "data/replay.csv"
    )