from datetime import datetime
import time
import psutil


class BotMonitor:

    def __init__(self, capital_manager):

        self.capital_manager = capital_manager
        self.position_manager = None
        self.tick_cache = None

        self.start_time = time.time()

        # Runtime Status
        self.status = "STOPPED"
        self.connection = "CONNECTED"

        # Market Info
        self.universe = 0
        self.orb_completed = 0

        # Trading Info
        self.last_tick = "None"
        self.last_trade = "None"
        

        # Queue Monitoring
        self.queue_size = 0
        self.max_queue_size = 0
        self.processed_ticks = 0

        # Counters
        self.stats = {
            "ticks": 0,
            "signals": 0,
            "buy": 0,
            "sell": 0,
            "active_trades": 0,
            "target": 0,
            "stoploss": 0,
            "time_exit": 0,
            "errors": 0,
            "insufficient_capital": 0,
        }

        # Print every 5 minutes
        self.last_status_print = time.time()

    # -------------------------------------------------

    def set_status(self, status):

        self.status = status

    # -------------------------------------------------

    def set_connection(self, connection):

        self.connection = connection

    # -------------------------------------------------

    def set_universe(self, count):

        self.universe = count

    # -------------------------------------------------

    def set_orb_completed(self, count):

        self.orb_completed = count

    # -------------------------------------------------

    def update_last_tick(self, ltt):

        self.last_tick = ltt

    # -------------------------------------------------

    def set_last_trade(self, trade):

        self.last_trade = trade

    # -------------------------------------------------

    def set_runtime_objects(
        self,
        position_manager,
        tick_cache
    ):

        self.position_manager = position_manager
        self.tick_cache = tick_cache

    # -------------------------------------------------

    def update_queue(self, size):

        self.queue_size = size

        if size > self.max_queue_size:
            self.max_queue_size = size

    # -------------------------------------------------

    def increment_processed_ticks(self):

        self.processed_ticks += 1

    # -------------------------------------------------

    def increment(self, key):

        if key not in self.stats:
            self.stats[key] = 0

        self.stats[key] += 1

    # -------------------------------------------------

    def decrement(self, key):

        if key not in self.stats:
            self.stats[key] = 0

        if self.stats[key] > 0:
            self.stats[key] -= 1

    # -------------------------------------------------

    def print_open_positions(self, position_manager, tick_cache):

        if not position_manager.positions:
            return

        print()
        print("=" * 80)
        print("                        OPEN POSITIONS")
        print("=" * 80)

        print(
            f"{'Symbol':15}"
            f"{'Qty':>8}"
            f"{'Entry':>12}"
            f"{'LTP':>12}"
            f"{'MTM':>15}"
        )

        print("-" * 80)

        for security_id, position in position_manager.positions.items():

            tick = tick_cache.get(security_id)

            if tick is None:
                continue

            entry = position["entry_price"]
            qty = position["qty"]
            ltp = tick["ltp"]
            mtm = (ltp - entry) * qty

            if "symbol" not in position:
                print("\n========== BAD POSITION ==========")
                print(f"Security ID : {security_id}")
                print(position)
                print("==================================")
                continue
                         
   

            print(
                f"{position.get('symbol', 'UNKNOWN'):15}"
                f"{qty:>8}"
                f"{entry:>12.2f}"
                f"{ltp:>12.2f}"
                f"{mtm:>15.2f}"
            )

        print("=" * 80)

    # -------------------------------------------------

    def print_status(self):

        now = time.time()

        if now - self.last_status_print < 300:
            return

        self.last_status_print = now

        uptime = int(now - self.start_time)

        hrs = uptime // 3600
        mins = (uptime % 3600) // 60
        secs = uptime % 60

        process = psutil.Process()

        memory = process.memory_info().rss / (1024 * 1024)

        cpu = process.cpu_percent(interval=None)

        print("\n")
        print("=" * 65)
        print("                ORB AUTO TRADER STATUS")
        print("=" * 65)

        print(f"Time              : {datetime.now().strftime('%H:%M:%S')}")
        print(f"Uptime            : {hrs:02}:{mins:02}:{secs:02}")

        print()

        print(f"Status            : {self.status}")
        print(f"Connection        : {self.connection}")

        print()

        print(f"Universe          : {self.universe}")
        print(f"ORB Completed     : {self.orb_completed}")

        print()

        print(f"Ticks             : {self.stats['ticks']}")
        print(f"Engine Ticks      : {self.processed_ticks}")
        print(f"Signals           : {self.stats['signals']}")

        print()

        print(f"BUY               : {self.stats['buy']}")
        print(f"SELL              : {self.stats['sell']}")
        print(f"Open Positions    : {self.stats['active_trades']}")
        closed_positions = self.stats["sell"]
        print(f"Closed Positions  : {closed_positions}")

        print()

        print(f"Realized P&L      : ₹{self.capital_manager.pnl():,.2f}")
        print(f"Floating MTM      : ₹{self.capital_manager.floating_mtm():,.2f}")
        print(f"Net P&L           : ₹{self.capital_manager.net_pnl():,.2f}")

        print()

        capital = self.capital_manager.capital()
        available = self.capital_manager.available()
        blocked = self.capital_manager.blocked()

        capital_used = (
            (blocked / capital) * 100
            if capital > 0 else 0
        )

        print(f"Capital           : ₹{capital:,.2f}")
        print(f"Available         : ₹{available:,.2f}")
        print(f"Blocked           : ₹{blocked:,.2f}")
        print(f"Capital Used      : {capital_used:.2f}%")

        print()

        print(f"Queue Size        : {self.queue_size}")
        print(f"Max Queue Size    : {self.max_queue_size}")

        print(f"Memory            : {memory:.1f} MB")
        print(f"CPU               : {cpu:.1f}%")

        print()

        print(f"Last Tick         : {self.last_tick}")
        print(f"Last Trade        : {self.last_trade}")

        print()

        print(f"Errors            : {self.stats['errors']}")
        print(f"Capital Skips     : {self.stats['insufficient_capital']}")

        print("=" * 65)
        print()

        if (
            self.position_manager is not None
            and self.tick_cache is not None
        ):
            self.print_open_positions(
                self.position_manager,
                self.tick_cache
            )