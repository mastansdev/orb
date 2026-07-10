from datetime import datetime


class DaySummary:

    def print_summary(self, monitor):

        print()
        print("=" * 65)
        print("                  END OF DAY SUMMARY")
        print("=" * 65)

        print(f"Date              : {datetime.now().strftime('%d-%m-%Y')}")
        print()

        print(f"Universe          : {monitor.universe}")
        print(f"ORB Completed     : {monitor.orb_completed}")

        print()

        print(f"Ticks             : {monitor.stats['ticks']}")
        print(f"Signals           : {monitor.stats['signals']}")

        print()

        print(f"BUY               : {monitor.stats['buy']}")
        print(f"SELL              : {monitor.stats['sell']}")
        print(f"Open Trades       : {monitor.stats['active_trades']}")

        print()

        print(f"Target            : {monitor.stats['target']}")
        print(f"StopLoss          : {monitor.stats['stoploss']}")
        print(f"Time Exit         : {monitor.stats['time_exit']}")

        print()

        print(f"Today's PnL       : ₹{monitor.pnl:.2f}")

        print()

        print(f"Errors            : {monitor.stats['errors']}")

        print("=" * 65)
        print()