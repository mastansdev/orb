import time
import requests


class TelegramCommandCenter:

    def __init__(self, engine, bot_token, chat_id):
        self.engine = engine
        self.bot_token = bot_token
        self.chat_id = str(chat_id)
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

        self.last_update_id = 0
        self.telegram_failures = 0

        # ---------------------------------
        # Command Registry
        # ---------------------------------
        self.commands = {
            "/status": self.cmd_status,
            "/capital": self.cmd_capital,
            "/mtm": self.cmd_mtm,
            "/positions": self.cmd_positions,
            "/health": self.cmd_health,   
            "/tickaudit": self.cmd_tick_audit,

            "/pause": self.cmd_pause,
            "/resume": self.cmd_resume,
            "/tradingoff": self.cmd_trading_off,
            "/tradingon": self.cmd_trading_on,

            "/exitall": self.cmd_exit_all,
        }

    # ---------------------------------

    def poll(self):
        try:
            response = requests.get(
                f"{self.base_url}/getUpdates",
                params={
                    "offset": self.last_update_id + 1,
                    "timeout": 20,
                },
                timeout=(5, 30),
            )

            data = response.json()

            if not data.get("ok"):
                return

            self.telegram_failures = 0

            for update in data["result"]:
                self.last_update_id = update["update_id"]
                message = update.get("message")

                if message is None:
                    continue

                if str(message["chat"]["id"]) != self.chat_id:
                    continue

                text = message.get("text", "")
                self.handle_command(text.strip())

        except Exception as e:
            self.telegram_failures += 1

            if self.telegram_failures >= 3:
                print("\n========== TELEGRAM COMMAND ERROR ==========")
                print(f"Consecutive Failures : {self.telegram_failures}")
                print(e)
                print("============================================\n")

            time.sleep(2)

    # ---------------------------------

    def run(self):
        while True:
            self.poll()
            time.sleep(0.5)

    # ---------------------------------

    def handle_command(self, command):
        if not command:
            return

        parts = command.split()
        base_command = parts[0].lower()
        args = parts[1:]

        handler = self.commands.get(base_command)
        if handler:
            handler(args)
        else:
            self.help()

    # ---------------------------------

    def cmd_status(self, args):
        status = self.engine.status()
        self.engine.telegram.send(
            "📊 BOT STATUS\n\n"
            f"Status      : {status['status']}\n"
            f"Connection  : {status['connection']}\n"
            f"Trades      : {status['active_trades']}\n"
            f"Ticks       : {status['processed_ticks']}\n"
            f"ORB         : {status['orb_completed']}"
        )

    # ---------------------------------

    def cmd_capital(self, args):
        capital = self.engine.capital()
        self.engine.telegram.send(
            "💰 CAPITAL\n\n"
            f"Starting    : ₹{capital['starting']:.2f}\n"
            f"Available   : ₹{capital['available']:.2f}\n"
            f"Blocked     : ₹{capital['blocked']:.2f}"
        )

    # ---------------------------------

    def cmd_mtm(self, args):
        mtm = self.engine.mtm()
        self.engine.telegram.send(
            "📈 MTM\n\n"
            f"Floating    : ₹{mtm['floating']:.2f}\n"
            f"Realized    : ₹{mtm['realized']:.2f}\n"
            f"Net         : ₹{mtm['net']:.2f}"
        )

    # ---------------------------------

    def cmd_positions(self, args):
        positions = self.engine.positions()

        if not positions:
            self.engine.telegram.send("📌 OPEN POSITIONS\n\nNo open positions.")
            return

        message = "📌 OPEN POSITIONS\n\n"
        total_pnl = 0.0

        for security_id, trade in positions.items():
            tick = self.engine.get_tick(security_id)

            if tick is None:
                message += f"{trade['symbol']}\nLTP   : Waiting...\n\n"
                continue

            ltp = tick["ltp"]
            pnl = (ltp - trade["entry"]) * trade["qty"]
            total_pnl += pnl

            message += (
                f"{trade['symbol']}\n"
                f"Entry : ₹{trade['entry']:.2f}\n"
                f"LTP   : ₹{ltp:.2f}\n"
                f"Qty   : {trade['qty']}\n"
                f"PnL   : ₹{pnl:.2f}\n\n"
            )

        message += (
            f"Total Positions : {len(positions)}\n"
            f"Total MTM : ₹{total_pnl:.2f}"
        )
        self.engine.telegram.send(message)

    # ---------------------------------

    def cmd_health(self, args):
        health = self.engine.health()
        self.engine.telegram.send(
            "🩺 BOT HEALTH\n\n"
            f"Status      : {health['status']}\n"
            f"Connection  : {health['connection']}\n"
            f"Ticks       : {health['processed_ticks']}\n"
            f"Trades      : {health['active_trades']}\n"
            f"ORB Ready   : {health['orb_completed']}"
        )

    # ---------------------------------

    def cmd_tick_audit(self, args):
        self.engine.telegram.send(
            "Tick Audit - Under Construction"
        )

    # ---------------------------------

    def cmd_pause(self, args):
        self.engine.pause()
        self.engine.telegram.send(
            "⏸️ NEW ENTRIES PAUSED\n\n"
            "Existing positions will continue to be managed."
        )

    # ---------------------------------

    def cmd_resume(self, args):
        self.engine.resume()
        self.engine.telegram.send(
            "▶️ NEW ENTRIES RESUMED"
        )

    # ---------------------------------

    def cmd_trading_off(self, args):
        self.engine.trading_off()
        self.engine.telegram.send(
            "🛑 TRADING DISABLED\n\n"
            "No new trades will be allowed."
        )

    # ---------------------------------

    def cmd_trading_on(self, args):
        self.engine.trading_on()
        self.engine.telegram.send(
            "✅ TRADING ENABLED"
        )

    # ---------------------------------
    
    def cmd_exit_all(self, args):
        result = self.engine.exit_all()

        self.engine.telegram.send(
            "🚨 EXIT ALL REQUESTED\n\n"
            "All open positions will be exited on the next processing cycle.\n\n"
            f"Status : {result['message']}"
        )

    # ---------------------------------

    def help(self):
        self.engine.telegram.send(
            "Available Commands\n\n"
            "/status\n"
            "/capital\n"
            "/mtm\n"
            "/positions\n"
            "/health\n"
            "/tickaudit\n\n"
            "/pause\n"
            "/resume\n\n"
            "/tradingoff\n"
            "/tradingon\n"
            "/exitall"
        )