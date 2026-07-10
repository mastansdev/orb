from datetime import datetime
import os
from dotenv import load_dotenv
from historical_data import HistoricalData
from telegram_notifier import TelegramNotifier
from position_recovery import PositionRecovery
from open_position_manager import OpenPositionManager
from trade_selection_engine import TradeSelectionEngine
from config import ORB_BUFFER, ENTRY_BUFFER

from day_summary import DaySummary
from watchdog import Watchdog
from bot_monitor import BotMonitor
from tick_cache import TickCache
from orb_engine import ORBEngine
from strategy import Strategy
from position_manager import PositionManager
from paper_execution import PaperExecution
from risk_manager import RiskManager
from trade_logger import TradeLogger
from capital_manager import CapitalManager
from sector_engine import SectorEngine
from price_engine import price_engine
from industry_engine import IndustryEngine
from results_engine import ResultsEngine
from theme_engine import ThemeEngine
from relative_strength_engine import RelativeStrengthEngine
# CHANGE 1 — Import MarketMoodEngine
from market_mood_engine import MarketMoodEngine
# NEW ADDITION — Import CandleEngine
from candle_engine import candle_engine
from config import DECISION_TRACE

# Core infrastructure routing elements
from system_registry import SystemRegistry
from intelligence_engine import IntelligenceEngine
from portfolio_risk_manager import PortfolioRiskManager
# STEP 1A — Import DecisionAudit
from decision_audit import DecisionAudit

# Portfolio Control
from trade_controller import TradeController

# FIXED: Moved MarketRecorder import to the top of the file
from market_recorder import MarketRecorder

# STEP 1 — Import PortfolioLedger
from portfolio_ledger import PortfolioLedger

# --------------------------------------------------
# Market Intelligence
# --------------------------------------------------
from collectors.news_collector import NewsCollector
from news_classifier import NewsClassifier
from impact_engine import ImpactEngine
from market_catalyst import MarketCatalyst
from market_memory import MarketMemory
from market_environment import MarketEnvironment

from news_engine import NewsEngine

load_dotenv()


class Engine:
    
    # Structural constants for tracking and routing exit state metrics
    EXIT_TARGET = "TARGET"
    EXIT_STOPLOSS = "STOPLOSS"
    EXIT_TIME = "TIME_EXIT"
    EXIT_MANUAL = "MANUAL_EXIT"
    EXIT_SYSTEM = "SYSTEM_EXIT"

    def __init__(self):
        self.tick_cache = TickCache()
        self.orb_engine = ORBEngine()
        self.historical_data = HistoricalData()
        self.capital_manager = CapitalManager()
        self.trade_selection_engine = TradeSelectionEngine()
        self.sector_engine = SectorEngine()
        self.industry_engine = IndustryEngine()
        self.results_engine = ResultsEngine()
        self.relative_strength_engine = RelativeStrengthEngine()
        self.theme_engine = ThemeEngine()
        # CHANGE 2 — Instantiate MarketMoodEngine
        self.market_mood_engine = MarketMoodEngine()
        # NEW ADDITION — Instantiate CandleEngine
        self.candle_engine = candle_engine

        # --------------------------------------------------
        # Market Intelligence
        # --------------------------------------------------

        self.news_engine = NewsEngine(self)

        self.news_collector = NewsCollector()

        self.news_classifier = NewsClassifier()

        self.impact_engine = ImpactEngine()

        self.market_catalyst = MarketCatalyst()

        self.market_memory = MarketMemory()

        self.market_environment = MarketEnvironment()


        # --------------------------------------------------
        # Register News Sources
        # --------------------------------------------------

        self.news_engine.register_collector(
            self.news_collector
        )



        # Build structural registration layers first
        self.registry = SystemRegistry()
        self.intelligence_engine = IntelligenceEngine(self.registry)

        # Attach intelligence analytical runtimes to systemic engine path
        self.registry.register("price", price_engine)
        self.registry.register("sector", self.sector_engine)
        self.registry.register("industry", self.industry_engine)
        self.registry.register("results", self.results_engine)
        self.registry.register("relative_strength", self.relative_strength_engine)
        self.registry.register("theme", self.theme_engine)
        # CHANGE 3 — Register market_mood in the SystemRegistry
        self.registry.register(
            "market_mood",
            self.market_mood_engine
        )
        self.registry.register(
            "market_environment",
            self.market_environment
        )
        self.registry.register(
            "market_catalyst",
            self.market_catalyst
        )
        self.registry.register(
            "market_memory",
            self.market_memory
        )

        self.strategy = Strategy()
        self.position_manager = PositionManager(
            capital_manager=self.capital_manager
        )
        self.paper_execution = PaperExecution()
        self.risk_manager = RiskManager()
        self.portfolio_risk_manager = PortfolioRiskManager()
        # STEP 1B — Instantiate DecisionAudit
        self.decision_audit = DecisionAudit()
        
        # STEP 2 — Create PortfolioLedger Instance
        self.portfolio_ledger = PortfolioLedger()

        # STEP 3 — Initialize the Trading Day ledger using available capital
        self.portfolio_ledger.start_day(
            self.capital_manager.available()
        )
        
        # Portfolio Control
        self.trade_controller = TradeController()
        
        self.trade_logger = TradeLogger()
        self.position_recovery = PositionRecovery()
        self.open_position_manager = OpenPositionManager()
        self.monitor = BotMonitor(
            capital_manager=self.capital_manager
        )
        self.monitor.set_runtime_objects(
            self.position_manager,
            self.tick_cache
        )
        self.watchdog = Watchdog()
        self.day_summary = DaySummary()
        self.telegram = TelegramNotifier(
            os.getenv("TELEGRAM_BOT_TOKEN"),
            os.getenv("TELEGRAM_CHAT_ID")
        )
        self.summary_printed = False
        self.last_sector_print = ""

        # FIXED: Clean instantiation via the global top-level import
        self.market_recorder = MarketRecorder(
            interval_seconds=1
        )

        self.trades = self.position_recovery.load()
        
        # ---------------------------------
        # Position Recovery Loop
        # ---------------------------------
        for security_id, trade in self.trades.items():
            self.position_manager.recover_position(
                security_id=security_id,
                symbol=trade["symbol"],
                entry_price=trade["entry"],
                stop_loss=trade["stop_loss"],
                qty=trade["qty"]
            )

            self.open_position_manager.add(security_id, trade)

            # Synchronize internal portfolio metrics with recovered state memory
            self.portfolio_risk_manager.add_trade(trade["symbol"])

            blocked = trade["entry"] * trade["qty"]
            self.capital_manager.block(blocked)
            self.monitor.increment("active_trades")
            
            self.monitor.set_last_trade(f"RECOVERED {trade['symbol']}")
            self.orb_engine.set_entry_taken(security_id)

        if self.trades:
            print(f"Recovered {len(self.trades)} open position(s).")
            
        self.monitor.set_orb_completed(self.orb_engine.completed_count())
        self.monitor.set_status("RUNNING")
        self.monitor.set_connection("CONNECTED")

    def process_tick(self, security_id, symbol, ltp, ltt):
        # FIXED: Wrap entire tick pipeline in try...finally to enforce "One tick -> One snapshot"
        try:
            self.monitor.increment_processed_ticks()

            # ---------------------------------
            # Tick Cache
            # ---------------------------------
            self.tick_cache.update(security_id, ltp, ltt)

            # ---------------------------------
            # Price Engine
            # ---------------------------------
            price_engine.update(symbol=symbol, ltp=ltp, last_update=ltt)
            change = price_engine.get_change(symbol)

            # ---------------------------------
            # Candle Engine Update
            # ---------------------------------
            self.candle_engine.update(
                symbol=symbol,
                ltp=ltp,
                timestamp=ltt
            )

            # ---------------------------------
            # Sector & Industry Intelligence
            # ---------------------------------
            self.sector_engine.update(symbol, ltp, change)
            self.industry_engine.update(symbol, ltp, change)
            self.theme_engine.update(symbol, ltp, change)
            self.relative_strength_engine.update(symbol, ltp, change)
                
            # ---------------------------------
            # Live Floating MTM
            # ---------------------------------
            total_mtm = 0.0

            for sid, position in self.position_manager.positions.items():
                tick = self.tick_cache.get(sid)
                if tick is None:
                    continue

                current_price = tick["ltp"]
                total_mtm += (current_price - position["entry_price"]) * position["qty"]

            self.capital_manager.set_floating_mtm(total_mtm)

            self.monitor.increment("ticks")
            self.monitor.update_last_tick(ltt)
            self.watchdog.tick_received()

            # ---------------------------------
            # Live / Historical ORB Builder
            # ---------------------------------
            current_time = ltt

            # Always update ORB from live ticks
            self.orb_engine.update(security_id, ltp, ltt)
            orb = self.orb_engine.get_orb(security_id)

            # If bot started after 09:30 and ORB is unavailable,
            # load historical ORB as a fallback.
            if current_time >= "09:30:00" and orb is None:
                historical_orb = self.historical_data.get_cached_orb(security_id)

                if historical_orb:
                    self.orb_engine.load_historical_orb(
                        security_id,
                        historical_orb["high"],
                        historical_orb["low"]
                    )
                    orb = self.orb_engine.get_orb(security_id)

            # ---------------------------------
            # Instrumentation Block
            # ---------------------------------
            completed = self.orb_engine.completed_count()
            self.monitor.set_orb_completed(completed)

            if orb is None:
                return

            trade = self.trades.get(security_id)

            # ---------------------------------
            # ENTRY
            # ---------------------------------
            if trade is None:

                # Master trading switch
                if not self.trade_controller.is_trading_enabled():
                    return

                # New entry switch
                if not self.trade_controller.is_entries_enabled():
                    return

                signal = self.strategy.is_buy_signal(
                    ltp,
                    orb,
                    ltt
                )

                # STEP 2 — Modified logic rule and clean print configuration block
                if signal:
                    print("\n========== LIVE ORB CANDIDATE ==========")
                    print(f"Symbol      : {symbol}")
                    print(f"Time        : {ltt}")
                    print(f"LTP         : {ltp:.2f}")
                    print(f"ORB High    : {orb['high']:.2f}")
                    print(f"ORB Low     : {orb['low']:.2f}")
                    print(f"Signal      : {signal}")
                    print("========================================\n")

                if signal:
                    intelligence = self.intelligence_engine.get(symbol)
                    decision = self.trade_selection_engine.evaluate(
                        symbol, ltp, orb, intelligence
                    )

                    print("\n========== TRADE SELECTION ==========")
                    print(f"Symbol    : {symbol}")
                    print(f"Selected  : {decision['selected']}")
                    print(f"Score     : {decision['score']}")
                    print(f"Reasons   : {decision['reasons']}")
                    print("=====================================\n")

                    # Record every evaluated decision
                    if decision is not None:
                        self.decision_audit.record_decision(
                            security_id=security_id,
                            symbol=symbol,
                            decision=decision
                        )

                    if decision is None:
                        return

                    if not decision["selected"]:
                        return

                    # Validate allocation rules against portfolio layer bounds
                    portfolio_decision = self.portfolio_risk_manager.can_take_trade(
                        symbol=symbol,
                        intelligence=intelligence
                    )

                    # STEP 3 — Record Portfolio Decision
                    self.decision_audit.record_portfolio_decision(
                        security_id=security_id,
                        portfolio_decision=portfolio_decision
                    )

                    # Log systemic exclusions to metrics server for performance visibility
                    if not portfolio_decision["allowed"]:
                        self.monitor.increment("portfolio_rejected")
                        return

                if signal:
                    self.monitor.increment("signals")

                    if symbol in ("VTL", "NUVAMA"):
                        trigger_price = orb["high"] + ENTRY_BUFFER

                        print("\n========== BREAKOUT DEBUG ==========")
                        print(f"Symbol        : {symbol}")
                        print(f"Time          : {ltt}")
                        print(f"ORB High      : {orb['high']:.2f}")
                        print(f"Trigger Price : {trigger_price:.2f}")
                        print(f"Current LTP   : {ltp:.2f}")
                        print(f"Breakout %    : {((ltp - orb['high']) / orb['high']) * 100:.3f}%")
                        print("====================================\n")

                    stop_loss = orb["low"] - ORB_BUFFER

                    qty = self.position_manager.open_position(
                        security_id, symbol, ltp, stop_loss
                    )

                    if qty <= 0:
                        self.monitor.increment("insufficient_capital")
                        return

                    self.paper_execution.buy(security_id, symbol, ltp, qty)
                    print(f"BUY : {symbol} @ {ltp:.2f} Qty:{qty}")

                    self.telegram.send(
                        f"🟢 BUY EXECUTED\n\n"
                        f"Stock : {symbol}\n"
                        f"Entry : ₹{ltp:.2f}\n"
                        f"Quantity : {qty}\n"
                        f"Stop Loss : ₹{stop_loss:.2f}\n"
                        f"Time : {ltt}"
                    )

                    self.monitor.increment("buy")
                    self.monitor.increment("active_trades")
                    self.monitor.set_last_trade(f"BUY {symbol} @ {ltp}")

                    new_trade = self.risk_manager.create_trade(ltp, stop_loss)
                    if new_trade is None:
                        return

                    # ---------------------------------
                    # Trade Metadata Setters
                    # ---------------------------------
                    new_trade["qty"] = qty
                    new_trade["symbol"] = symbol
                    new_trade["entry_time"] = ltt
                    new_trade["entry_date"] = datetime.now().strftime("%Y-%m-%d")
                    new_trade["capital_used"] = round(qty * ltp, 2)
                    new_trade["orb"] = {
                        "high": orb["high"],
                        "low": orb["low"]
                    }
                    new_trade["decision"] = decision

                    # STEP 4 — Record Execution
                    self.decision_audit.record_execution(
                        security_id=security_id,
                        execution={
                            "symbol": symbol,
                            "entry_price": ltp,
                            "qty": qty,
                            "stop_loss": stop_loss,
                            "entry_time": ltt
                        }
                    )

                    # Commit allocation reference only when parameters pass validation
                    self.portfolio_risk_manager.add_trade(symbol)

                    # Execute explicit sandbox tracking state assertions under debugging flags
                    if __debug__:
                        assert symbol in self.portfolio_risk_manager.open_trades, (
                            f"Portfolio allocation state out of sync for {symbol}"
                        )

                    self.trades[security_id] = new_trade

                    # CHANGE 2 — Wire PortfolioLedger BUY
                    capital_used = qty * ltp
                    self.portfolio_ledger.record_buy(
                        capital_used=capital_used
                    )

                    self.open_position_manager.add(security_id, new_trade)
                    
                    self.orb_engine.set_entry_taken(security_id)
                    self.position_recovery.save(self.trades)

            # ---------------------------------
            # EXIT
            # ---------------------------------
            else:
                # CHANGE 1 — Complete /exitall evaluation bypass routing
                if self.trade_controller.is_exit_all_requested():
                    result = self.EXIT_MANUAL
                else:
                    result = self.risk_manager.update(
                        trade,
                        ltp,
                        ltt
                    )

                if result == self.EXIT_TARGET:
                    self.monitor.increment("target")
                elif result == self.EXIT_STOPLOSS:
                    self.monitor.increment("stoploss")
                elif result == self.EXIT_TIME:
                    self.monitor.increment("time_exit")

                # Route execution state drop when static exit signatures hit targets
                if result in [
                    self.EXIT_TARGET,
                    self.EXIT_STOPLOSS,
                    self.EXIT_TIME,
                    self.EXIT_MANUAL,
                    self.EXIT_SYSTEM,
                ]:

                    pnl = (ltp - trade["entry"]) * trade["qty"]

                    # Required Fix #1 — paper_execution.sell() executed BEFORE record_sell()
                    self.paper_execution.sell(
                        security_id,
                        symbol,
                        ltp,
                        trade["qty"]
                    )

                    # CHANGE 3 — Wire PortfolioLedger SELL
                    capital_released = trade["qty"] * ltp
                    self.portfolio_ledger.record_sell(
                        capital_released=capital_released,
                        gross_pnl=pnl
                    )

                    # Record completed execution result
                    self.decision_audit.record_result(
                        security_id=security_id,
                        result={
                            "exit_price": ltp,
                            "exit_time": ltt,
                            "exit_reason": result,
                            "pnl": round(pnl, 2)
                        }
                    )
                    
                    # Instantly clear structural risk indexes to free risk capacity
                    self.portfolio_risk_manager.remove_trade(symbol)
                    
                    print(f"SELL : {symbol} @ {ltp:.2f} PnL:{pnl:.2f}")

                    icon = "🔴"
                    title = "SELL EXECUTED"

                    if result == self.EXIT_TARGET:
                        icon = "🟢"
                        title = "TARGET HIT"
                    elif result == self.EXIT_TIME:
                        icon = "🟡"
                        title = "TIME EXIT"
                    elif result == self.EXIT_MANUAL:
                        icon = "🚨"
                        title = "MANUAL EXIT"
                    elif result == self.EXIT_SYSTEM:
                        icon = "⚠️"
                        title = "SYSTEM EXIT"

                    self.telegram.send(
                        f"{icon} {title}\n\n"
                        f"Stock      : {symbol}\n\n"
                        f"Entry      : ₹{trade['entry']:.2f}\n"
                        f"Exit       : ₹{ltp:.2f}\n\n"
                        f"Quantity   : {trade['qty']}\n\n"
                        f"Reason     : {result}\n"
                        f"PnL        : ₹{pnl:.2f}\n\n"
                        f"Time       : {ltt}"
                    )

                    self.monitor.increment("sell")
                    self.monitor.decrement("active_trades")
                    self.monitor.set_last_trade(f"SELL {symbol} @ {ltp}")
                    
                    self.trade_logger.log_trade(
                        datetime.now().strftime("%Y-%m-%d"),
                        ltt,
                        symbol,
                        trade["entry"],
                        ltp,
                        trade["qty"],
                        round(pnl, 2),
                        result
                    )

                    self.position_manager.close_position(security_id, pnl)
                    self.open_position_manager.remove(security_id)
                    del self.trades[security_id]
                    
                    # Required Fix #2 — Modified notification and tracking logic block
                    if self.trades:
                        self.position_recovery.save(self.trades)
                    else:
                        self.position_recovery.clear()

                    # Notify only when Exit-All operation has finished
                    if (
                        self.trade_controller.is_exit_all_requested()
                        and not self.trades
                    ):
                        self.trade_controller.clear_exit_all()

                        self.telegram.send(
                            "✅ EXIT ALL COMPLETED\n\n"
                            "All open positions have been successfully closed.\n\n"
                            "Remaining Positions : 0"
                        )

        finally:
            # FIXED: Exactly one recorder call executed at the end of every tick trajectory.
            self.market_recorder.record(**self.system_snapshot())
            self.monitor.print_status()
            self.watchdog.check()

    def get_tick(self, security_id):
        return self.tick_cache.get(security_id)

    def get_orb(self, security_id):
        return self.orb_engine.get_orb(security_id)

    def print_day_summary(self):
        self.day_summary.print_summary(self.monitor)

    def status(self):
        return {
            "status": self.monitor.status,
            "connection": self.monitor.connection,
            "active_trades": self.open_position_manager.count(),
            "processed_ticks": self.monitor.processed_ticks,
            "orb_completed": self.orb_engine.completed_count()
        }

    def positions(self):
        return self.open_position_manager.all()

    def capital(self):
        return {
            "starting": self.capital_manager.capital(),
            "available": self.capital_manager.available(),
            "blocked": self.capital_manager.blocked()
        }

    def mtm(self):
        return {
            "floating": self.capital_manager.floating_mtm(),
            "realized": self.capital_manager.pnl(),
            "net": self.capital_manager.net_pnl()
        }

    def sector(self):
        return self.sector_engine.get_rankings()

    def health(self):
        return {
            "processed_ticks": self.monitor.processed_ticks,
            "active_trades": self.open_position_manager.count(),
            "orb_completed": self.orb_engine.completed_count(),
            "status": self.monitor.status,
            "connection": self.monitor.connection
        }

    def system_snapshot(self):
        capital = self.capital()
        mtm = self.mtm()
        return {
            "floating_mtm": mtm["floating"],
            "realized_pnl": mtm["realized"],
            "net_pnl": mtm["net"],
            "open_positions": self.open_position_manager.count(),
            "capital_used": capital["starting"] - capital["available"],
            "available_capital": capital["available"]
        }

    def shutdown(self):
        self.market_recorder.close()

    def pause(self):
        self.trade_controller.disable_entries()
        return {
            "success": True,
            "message": "New entries paused."
        }

    def resume(self):
        self.trade_controller.enable_entries()
        return {
            "success": True,
            "message": "New entries resumed."
        }

    def trading_off(self):
        self.trade_controller.disable_trading()
        self.trade_controller.disable_entries()

        return {
            "success": True,
            "message": "Trading disabled."
        }

    def trading_on(self):
        self.trade_controller.enable_trading()
        self.trade_controller.enable_entries()

        return {
            "success": True,
            "message": "Trading enabled."
        }

    def exit_all(self):
        self.trade_controller.request_exit_all()

        return {
            "success": True,
            "message": "Exit All requested."
        }

    # CHANGE 4 — Add Ledger Status API
    def ledger(self):
        return self.portfolio_ledger.summary()

    # CHANGE 5 — Add TradeController Status API
    def trade_controller_status(self):
        return self.trade_controller.status()

    # --------------------------------------------------
    # Market Intelligence Pipeline
    # --------------------------------------------------
    def _process_market_news(self, news):
        try:
            # ---------------------------------
            # News Classification
            # ---------------------------------
            classified_news = self.news_classifier.classify(news)

            if classified_news is None:
                return

            # ---------------------------------
            # Impact Analysis
            # ---------------------------------
            impact = self.impact_engine.evaluate(classified_news)

            if impact is None:
                return

            # ---------------------------------
            # Catalyst Management
            # ---------------------------------
            self.market_catalyst.update(impact)

            # ---------------------------------
            # Memory
            # ---------------------------------
            self.market_memory.remember(impact)

            # ---------------------------------
            # Market Environment
            # ---------------------------------
            self.market_environment.update(impact)

        except Exception as e:
            print("\n========== MARKET INTELLIGENCE ERROR ==========")
            print(e)
            print("===============================================\n")