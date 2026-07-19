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

            # Institutional intelligence
            "/risk": self.cmd_risk,
            "/memory": self.cmd_memory,
            "/company": self.cmd_company,
            "/pool": self.cmd_pool,
            "/sectors": self.cmd_sectors,

            # Institutional desk commands
            "/brief": self.cmd_brief,
            "/fno": self.cmd_fno,
            "/exposure": self.cmd_exposure,
            "/calibration": self.cmd_calibration,
            "/events": self.cmd_events,
            "/journal": self.cmd_journal,
            "/eod": self.cmd_eod,
            "/graph": self.cmd_graph,
            "/calendar": self.cmd_calendar,
            "/edge": self.cmd_edge,
            "/execution": self.cmd_execution,
            "/causal": self.cmd_causal,
            "/decay": self.cmd_decay,
            "/shockmodel": self.cmd_shockmodel,
            "/news": self.cmd_news,
            "/profile": self.cmd_profile,
            "/market": self.cmd_market,
            "/fetchresults": self.cmd_fetch_results,
            "/shock": self.cmd_shock,
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

    def cmd_risk(self, args):
        status = self.engine.risk_status()

        locked_line = "🔒 LOCKED" if status["locked"] else "🟢 ACTIVE"

        message = (
            "🛡️ RISK GOVERNOR\n\n"
            f"State        : {locked_line}\n"
        )

        if status["locked"]:
            message += f"Reason       : {status['lock_reason']}\n"

        message += (
            f"Day PnL      : ₹{status['day_pnl']:.2f}\n"
            f"Loss Limit   : ₹{status['daily_max_loss']}\n"
            f"Loss Streak  : {status['consecutive_losses']}"
            f"/{status['max_consecutive_losses']}\n"
            f"Heat         : ₹{status['portfolio_heat']:.0f}"
            f"/₹{status['max_portfolio_heat']}\n"
            f"Blocked      : {status['entries_blocked']} entries\n"
            f"Closed       : {status['trades_closed']} trades"
        )

        self.engine.telegram.send(message)

    # ---------------------------------

    def cmd_memory(self, args):
        if not args:
            self.engine.telegram.send(
                "Usage: /memory SYMBOL"
            )
            return

        symbol = args[0].upper()
        report = self.engine.memory_report(symbol)
        self.engine.telegram.send(f"🧠 {report}")

    # ---------------------------------

    def cmd_company(self, args):
        if not args:
            self.engine.telegram.send(
                "Usage: /company SYMBOL"
            )
            return

        symbol = args[0].upper()
        report = self.engine.company_report(symbol)
        self.engine.telegram.send(f"🏢 {report}")

    # ---------------------------------

    def cmd_pool(self, args):
        report = self.engine.opportunity_pool_report()
        self.engine.telegram.send(f"🎯 {report}")

    # ---------------------------------

    def cmd_sectors(self, args):
        count = self.engine.record_sector_memory()
        rankings = self.engine.sector() or []

        lines = ["📊 SECTOR RANKINGS", ""]

        for i, entry in enumerate(rankings[:10], start=1):
            if isinstance(entry, dict):
                name = entry.get("sector") or entry.get("name") or "?"
                score = (
                    entry.get("score")
                    or entry.get("participation")
                    or 0
                )
                lines.append(f"{i:02d}. {name} ({score})")
            else:
                lines.append(f"{i:02d}. {entry}")

        lines.append("")
        lines.append(f"Recorded {count} sectors to memory.")

        self.engine.telegram.send("\n".join(lines))

    # ---------------------------------

    def cmd_brief(self, args):
        self.engine.telegram.send(
            self.engine.morning_brief()
        )

    # ---------------------------------

    def cmd_fno(self, args):
        self.engine.telegram.send(
            f"🎯 {self.engine.fno_report()}"
        )

    # ---------------------------------

    def cmd_exposure(self, args):
        self.engine.telegram.send(
            f"📊 {self.engine.exposure_report()}"
        )

    # ---------------------------------

    def cmd_calibration(self, args):
        self.engine.telegram.send(
            f"🎓 {self.engine.calibration_report()}"
        )

    # ---------------------------------

    def cmd_events(self, args):
        symbol = args[0].upper() if args else None
        self.engine.telegram.send(
            f"📰 {self.engine.events_report(symbol)}"
        )

    # ---------------------------------

    def cmd_journal(self, args):
        self.engine.telegram.send(
            f"📓 {self.engine.journal_report()}"
        )

    # ---------------------------------

    def cmd_eod(self, args):
        self.engine.telegram.send(
            f"🌇 {self.engine.eod_report()}"
        )

    # ---------------------------------

    def cmd_edge(self, args):
        self.engine.telegram.send(
            f"📐 {self.engine.edge_report()}"
        )

    # ---------------------------------

    def cmd_execution(self, args):
        self.engine.telegram.send(
            f"🎯 {self.engine.execution_report()}"
        )

    # ---------------------------------

    def cmd_causal(self, args):
        symbol = args[0].upper() if args else None
        self.engine.telegram.send(
            f"🧩 {self.engine.causal_report(symbol)}"
        )

    # ---------------------------------

    def cmd_decay(self, args):
        event_type = args[0].upper() if args else None
        self.engine.telegram.send(
            f"📉 {self.engine.decay_report(event_type)}"
        )

    # ---------------------------------

    def cmd_shockmodel(self, args):
        self.engine.telegram.send(
            f"📉 {self.engine.decay_report()}"
        )

    # ---------------------------------

    def cmd_news(self, args):
        self.engine.telegram.send(
            f"📡 {self.engine.news_pipeline_report()}"
        )

    # ---------------------------------

    def cmd_profile(self, args):
        self.engine.telegram.send(
            f"💰 {self.engine.profile_report()}"
        )

    # ---------------------------------

    def cmd_market(self, args):
        self.engine.telegram.send(
            f"🌡️ {self.engine.market_report()}"
        )

    # ---------------------------------

    def cmd_fetch_results(self, args):
        self.engine.telegram.send(
            "📅 Fetching BSE results calendar…"
        )
        added = self.engine.fetch_results_calendar()
        self.engine.telegram.send(
            f"📅 Results calendar updated: "
            f"{added} entries added.\n\n"
            f"{self.engine.calendar_report()}"
        )

    # ---------------------------------

    def cmd_shock(self, args):
        # Operator red button — requires CONFIRM
        if not args or args[0].upper() != "CONFIRM":
            self.engine.telegram.send(
                "🚨 SHOCK RESPONSE requires "
                "confirmation.\n\n"
                "Send:  /shock CONFIRM\n\n"
                "This will EXIT ALL positions, disable "
                "entries, and send weakest-sector PE "
                "recommendations."
            )
            return

        status = self.engine.trigger_shock(
            "OPERATOR TRIGGERED via /shock"
        )
        self.engine.telegram.send(
            f"🚨 Shock response executed at "
            f"{status['time']}."
        )

    # ---------------------------------

    def cmd_graph(self, args):
        if not args:
            self.engine.telegram.send(
                "Usage: /graph SYMBOL"
            )
            return

        self.engine.telegram.send(
            f"🕸️ {self.engine.graph_report(args[0].upper())}"
        )

    # ---------------------------------

    def cmd_calendar(self, args):
        # /calendar               → week-ahead view
        # /calendar REFRESH       → purge + strict refetch
        # /calendar SYMBOL DATE   → add entry
        if args and args[0].upper() == "REFRESH":
            self.engine.telegram.send(
                "📅 Purging future entries and "
                "re-fetching BSE calendar (strict "
                "matching)…"
            )
            removed, added = (
                self.engine.refresh_results_calendar()
            )
            self.engine.telegram.send(
                f"📅 Calendar rebuilt: {removed} old "
                f"entries purged, {added} strict "
                f"matches added.\n\n"
                f"{self.engine.calendar_report()}"
            )
            return

        if len(args) >= 2:
            added = self.engine.calendar_add(
                args[0], args[1]
            )
            if added:
                self.engine.telegram.send(
                    f"📅 Added: {args[0].upper()} "
                    f"on {args[1]}"
                )
            else:
                self.engine.telegram.send(
                    "Usage: /calendar SYMBOL YYYY-MM-DD"
                )
            return

        self.engine.telegram.send(
            f"📅 {self.engine.calendar_report()}"
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
            "/risk — risk governor state\n"
            "/memory SYMBOL — pattern memory\n"
            "/company SYMBOL — company dossier\n"
            "/pool — opportunity pool\n"
            "/sectors — sector rankings\n\n"
            "/brief — institutional morning brief\n"
            "/fno — F&O catalyst watchlist\n"
            "/exposure — portfolio concentration\n"
            "/calibration — conviction vs outcomes\n"
            "/events [SYMBOL] — event memory\n"
            "/journal — today's decisions\n"
            "/eod — end of day report\n"
            "/graph SYMBOL — knowledge graph\n"
            "/calendar [REFRESH | SYMBOL DATE] — results week\n"
            "/edge — edge analysis (net of charges)\n"
            "/execution — slippage / fill quality\n"
            "/causal [SYMBOL] — cause-effect chains\n"
            "/news — Railway→Brain pipeline health\n"
            "/profile — capital / leverage / margin\n"
            "/market — regime + adaptive limits\n"
            "/fetchresults — refresh BSE results calendar\n"
            "/shock CONFIRM — emergency flatten + PE setup\n\n"
            "/pause\n"
            "/resume\n\n"
            "/tradingoff\n"
            "/tradingon\n"
            "/exitall"
        )