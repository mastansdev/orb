from datetime import datetime
import os
from dotenv import load_dotenv
from historical_data import HistoricalData
from telegram_notifier import TelegramNotifier
from position_recovery import PositionRecovery
from open_position_manager import OpenPositionManager
from trade_selection_engine import TradeSelectionEngine
import traceback
from config import ORB_BUFFER
from portfolio_risk_manager import PortfolioOpportunity
from trade_policy_manager import TradePolicyManager

from day_summary import DaySummary
from watchdog import Watchdog
from bot_monitor import BotMonitor
from tick_cache import TickCache
from orb_engine import ORBEngine
from strategy import Strategy
from position_manager import PositionManager
from execution import Execution
from broker_sync import BrokerSync
from risk_manager import RiskManager
from trade_logger import TradeLogger
from capital_manager import CapitalManager
from sector_engine import SectorEngine
from price_engine import price_engine
from industry_engine import IndustryEngine
from results_engine import ResultsEngine
from theme_engine import ThemeEngine
from relative_strength_engine import RelativeStrengthEngine
from market_mood_engine import MarketMoodEngine
from candle_engine import candle_engine
from config import DECISION_TRACE

# Core infrastructure routing elements
from system_registry import SystemRegistry
from intelligence_engine import IntelligenceEngine
from portfolio_risk_manager import PortfolioRiskManager
from allocation_trigger_engine import AllocationTriggerEngine
from capital_allocation_engine import CapitalAllocationEngine
from opportunity_ranker import OpportunityRanker
from portfolio_intelligence_engine import PortfolioIntelligenceEngine

from decision_audit import DecisionAudit

# Portfolio Control
from trade_controller import TradeController
from market_recorder import MarketRecorder
from portfolio_ledger import PortfolioLedger

# Market Intelligence Collectors & Models
from collectors.news_rss_collector import NewsRSSCollector
from collectors.bse_corporate_collector import BSECorporateCollector
from news_classifier import NewsClassifier
from impact_engine import ImpactEngine
from market_catalyst import MarketCatalyst
from market_memory import MarketMemory
from market_environment import MarketEnvironment
from news_engine import NewsEngine

# Institutional Risk & Memory Intelligence
from risk_governor import RiskGovernor
from pattern_engine import PatternEngine
from company_intelligence import CompanyIntelligence
from event_intelligence import EventIntelligence
from fno_opportunity_engine import FnOOpportunityEngine
from knowledge_graph import KnowledgeGraph
from results_calendar import ResultsCalendar
from dynamic_trade_manager import DynamicTradeManager
from causal_reasoning_engine import CausalReasoningEngine

from intelligence_context import IntelligenceContext

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

        # --------------------------------------------------
        # Institutional Capital Allocation Layer
        # --------------------------------------------------

        self.opportunity_ranker = OpportunityRanker()
        self.portfolio_intelligence_engine = PortfolioIntelligenceEngine()

        # --------------------------------------------------
        # Institutional Capital Allocation Layer
        # --------------------------------------------------

        self.opportunity_ranker = OpportunityRanker()
        self.portfolio_intelligence_engine = PortfolioIntelligenceEngine()
        self.capital_allocation_engine = CapitalAllocationEngine()
        self.allocation_trigger_engine = AllocationTriggerEngine()


        self.sector_engine = SectorEngine()
        self.industry_engine = IndustryEngine()
        self.results_engine = ResultsEngine()
        self.relative_strength_engine = RelativeStrengthEngine()
        self.theme_engine = ThemeEngine()
        self.market_mood_engine = MarketMoodEngine()
        self.candle_engine = candle_engine

        # --------------------------------------------------
        # Market Intelligence Setup
        # --------------------------------------------------

        # Shared Market Intelligence State
        self.market_catalyst = MarketCatalyst()
        self.market_memory = MarketMemory()
        self.market_environment = MarketEnvironment()

        # ---------------------------------
        # Intelligence Context
        # ---------------------------------

        self.intelligence_context = IntelligenceContext()
        self.intelligence_context.market_catalyst = self.market_catalyst
        self.intelligence_context.market_memory = self.market_memory
        self.intelligence_context.market_environment = self.market_environment

        # ---------------------------------
        # News Intelligence Pipeline
        # ---------------------------------

        self.news_engine = NewsEngine(self.intelligence_context)
        self.news_collector = NewsRSSCollector()
        self.bse_corporate_collector = BSECorporateCollector()

        # Register News Sources
        self.news_engine.register_collector(self.news_collector)
        self.news_engine.register_collector(
            self.bse_corporate_collector
        )

        # Regulatory carriers (SEBI / RBI / PIB)
        try:
            from collectors.regulatory_collector import (
                RegulatoryCollector,
            )
            self.news_engine.register_collector(
                RegulatoryCollector()
            )
        except Exception as e:
            print(f"[NEWS] Regulatory collector unavailable: {e}")

        
        # Legacy components retained temporarily during migration.
        # They will be removed after the NewsEngine migration
        # is fully completed and verified.
        self.news_classifier = NewsClassifier()
        self.impact_engine = ImpactEngine()
        
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
        self.registry.register("market_mood", self.market_mood_engine)
        self.registry.register("market_environment", self.market_environment)
        self.registry.register("market_catalyst", self.market_catalyst)
        self.registry.register("market_memory", self.market_memory)

        self.strategy = Strategy()
        self.position_manager = PositionManager(capital_manager=self.capital_manager)
        self.execution = Execution()
        self.broker_sync = BrokerSync()
        self.risk_manager = RiskManager()
        self.portfolio_risk_manager = PortfolioRiskManager()
        self.allocation_trigger_engine = AllocationTriggerEngine()
        self.capital_allocation_engine = CapitalAllocationEngine()
        # ---------------------------------
        # Institutional Allocation Clock
        # ---------------------------------
        
        self.last_allocation_cycle = None


        self.trade_policy_manager = TradePolicyManager()
        self.decision_audit = DecisionAudit()
        self.portfolio_ledger = PortfolioLedger()

        # Initialize the Trading Day ledger using available capital
        self.portfolio_ledger.start_day(self.capital_manager.available())
        
        # Portfolio Control
        self.trade_controller = TradeController()
        self.trade_logger = TradeLogger()
        self.position_recovery = PositionRecovery()
        self.open_position_manager = OpenPositionManager()
        
        self.monitor = BotMonitor(capital_manager=self.capital_manager)
        self.monitor.set_runtime_objects(self.position_manager, self.tick_cache)
        
        self.watchdog = Watchdog()
        self.day_summary = DaySummary()
        self.telegram = TelegramNotifier(
            os.getenv("TELEGRAM_BOT_TOKEN"),
            os.getenv("TELEGRAM_CHAT_ID")
        )

        # --------------------------------------------------
        # Risk Governor — independent risk authority.
        # Evidence contributes; Conviction decides;
        # RISK AUTHORIZES; Execution acts.
        # --------------------------------------------------
        self.risk_governor = RiskGovernor(
            capital_manager=self.capital_manager,
            trade_controller=self.trade_controller,
            telegram=self.telegram
        )

        # Config coherence audit at every startup —
        # incoherent limits are found on the bench,
        # not live.
        self.risk_governor.print_coherence_audit()

        # --------------------------------------------------
        # Memory-Driven Intelligence
        # --------------------------------------------------
        self.company_intelligence = CompanyIntelligence()
        self.pattern_engine = PatternEngine(self.market_memory)

        # Event Intelligence : stories → structured,
        # permanent, per-stock events
        self.event_intelligence = EventIntelligence(
            repository=self.market_memory.repository,
            company_intelligence=self.company_intelligence
        )

        # F&O Opportunity Intelligence : live catalyst
        # watchlist over the F&O universe
        self.fno_opportunity_engine = FnOOpportunityEngine(
            company_intelligence=self.company_intelligence,
            repository=self.market_memory.repository
        )

        # Knowledge Graph : weighted relationships +
        # sympathy propagation
        self.knowledge_graph = KnowledgeGraph(
            company_intelligence=self.company_intelligence,
            repository=self.market_memory.repository
        )

        # Results Calendar : no new risk into binary events
        self.results_calendar = ResultsCalendar(
            repository=self.market_memory.repository
        )

        # Calendar Harvester : auto-populate the
        # calendar from board-meeting intimations
        from calendar_harvester import CalendarHarvester
        self.calendar_harvester = CalendarHarvester(
            self.results_calendar
        )

        # Dynamic Trade Manager : partial booking,
        # ratchet trailing, catalyst exits
        self.dynamic_trade_manager = DynamicTradeManager(
            event_intelligence=self.event_intelligence,
            fno_engine=self.fno_opportunity_engine
        )

        # Causal Reasoning Engine : institutional
        # cause-and-effect knowledge (1st/2nd/3rd order)
        self.causal_engine = CausalReasoningEngine(
            company_intelligence=self.company_intelligence,
            repository=self.market_memory.repository
        )

        self.trade_selection_engine.attach_intelligence(
            pattern_engine=self.pattern_engine,
            company_intelligence=self.company_intelligence,
            event_intelligence=self.event_intelligence,
            fno_engine=self.fno_opportunity_engine,
            knowledge_graph=self.knowledge_graph,
            results_calendar=self.results_calendar,
            calendar_harvester=self.calendar_harvester,
            causal_engine=self.causal_engine
        )
        self.summary_printed = False
        self.last_sector_print = ""
        # Rolling tick-error tracking (for Phase 0 exception handling)
        self._tick_error_timestamps = []
        self.market_recorder = MarketRecorder(interval_seconds=1)

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
            recovered_opportunity = PortfolioOpportunity(
                symbol=trade["symbol"]
            )


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
        try:
            self.monitor.increment_processed_ticks()

            # ---------------------------------
            # Tick Cache Update
            # ---------------------------------
            self.tick_cache.update(security_id, ltp, ltt)

            # ---------------------------------
            # Price Engine Update
            # ---------------------------------
            price_engine.update(symbol=symbol, ltp=ltp, last_update=ltt)
            change = price_engine.get_change(symbol)

            # ---------------------------------
            # Candle Engine Update
            # ---------------------------------
            self.candle_engine.update(symbol=symbol, ltp=ltp, timestamp=ltt)

            # ---------------------------------
            # Sector & Industry Intelligence
            # ---------------------------------
            self.sector_engine.update(symbol, ltp, change)
            self.industry_engine.update(symbol, ltp, change)
            self.theme_engine.update(symbol, ltp, change)
            self.relative_strength_engine.update(symbol, ltp, change)
                
            # ---------------------------------
            # Live Floating MTM Calculation
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
            self.orb_engine.update(security_id, ltp, ltt)
            orb = self.orb_engine.get_orb(security_id)

            # Fallback to historical ORB data if running late
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
            # Instrumentation Metrics Update
            # ---------------------------------
            completed = self.orb_engine.completed_count()
            self.monitor.set_orb_completed(completed)

            if orb is None:
                return

            trade = self.trades.get(security_id)

            # --------------------------------------------------
            # Broker Synchronization
            # --------------------------------------------------
            if self.execution.mode == "LIVE":

                if trade is not None:

                    if not self.broker_sync.has_position(security_id):

                        print(f"⚠ Manual Exit Detected : {symbol}")

                        # Remove internal tracking states
                        self.position_manager.remove_position(security_id)
                        self.open_position_manager.remove(security_id)

                        # Free risk allocation capacity
                        self.portfolio_risk_manager.remove_trade(symbol)

                        # Update portfolio ledger state before dropping the dict handle
                        capital_released = trade["qty"] * ltp
                        self.portfolio_ledger.record_sell(
                            capital_released=capital_released,
                            gross_pnl=0
                        )

                        # Clear recovery state maps safely
                        del self.trades[security_id]
                        if self.trades:
                            self.position_recovery.save(self.trades)
                        else:
                            self.position_recovery.clear()

                        # Update visual dashboard states
                        self.monitor.decrement("active_trades")
                        self.monitor.set_last_trade(f"MANUAL EXIT {symbol}")

                        # Dispatch notifications
                        self.telegram.send(
                            f"⚠️ MANUAL EXIT DETECTED\n\n"
                            f"Stock : {symbol}\n\n"
                            f"The position was closed outside the bot.\n"
                            f"Internal state synchronized successfully."
                        )
                        return
                    # else: broker still shows this position open —
                    # fall through to the normal entry/exit pipeline below
                



            # ---------------------------------
            # POSITION ENTRY PIPELINE
            # ---------------------------------
            if trade is None:
                if not self.trade_controller.is_trading_enabled():
                    return
                if not self.trade_controller.is_entries_enabled():
                    return

                # Risk Governor kill-switch fast path:
                # when locked, skip all evaluation work.
                if self.risk_governor.locked:
                    return

                last_closed_candle = self.candle_engine.get_latest(symbol)
                signal = self.strategy.is_buy_signal(orb, ltt, last_closed_candle)

                if signal:
                    print("\n========== LIVE ORB CANDIDATE ==========")
                    print(f"Symbol      : {symbol}")
                    print(f"Time        : {ltt}")
                    print(f"LTP         : {ltp:.2f}")
                    print(f"ORB High    : {orb['high']:.2f}")
                    print(f"ORB Low     : {orb['low']:.2f}")
                    print(f"Signal      : {signal}")
                    print("========================================\n")

                    intelligence = self.intelligence_engine.get(symbol)
                    decision = self.trade_selection_engine.evaluate(
                        symbol, ltp, orb, intelligence
                    )

                    # --- Issue 1 Fix: Defensive None-Guard Exception Handling ---
                    if decision is None:
                        print(f"⚠️ CRITICAL: TradeSelectionEngine returned None for {symbol}.")
                        decision = {
                            "selected": False,
                            "score": 0,
                            "reasons": ["Brain returned no decision or raised an internal exception"],
                            "brain_decision": None
                        }

                    # Safely extract brain decision object framework
                    brain = decision.get("brain_decision") if isinstance(decision, dict) else None

                    # --- Issue 2 Fix: Brain-centric logging with clean Enum Unwrapping ---
                    if brain:
                        action_obj = getattr(brain, "action", None)
                        action_val = action_obj.value if hasattr(action_obj, "value") else action_obj
                        
                        print("\n========== BRAIN DECISION ==========")
                        print(f"Symbol      : {symbol}")
                        print(f"Action      : {action_val if action_val is not None else 'N/A'}")
                        print(f"Confidence  : {getattr(brain, 'confidence', 'N/A')}")
                        print(f"Score       : {getattr(brain, 'score', 'N/A')}")
                        print(f"Reasons     : {getattr(brain, 'reasons', 'N/A')}")
                        print(f"Warnings    : {getattr(brain, 'warnings', 'N/A')}")
                        print("===================================\n")
                    else:
                        print("\n========== TRADE SELECTION ==========")
                        print(f"Symbol    : {symbol}")
                        print(f"Selected  : {decision.get('selected', False)}")
                        print(f"Score     : {decision.get('score', 0)}")
                        print(f"Reasons   : {decision.get('reasons', ['No details provided'])}")
                        print("=====================================\n")

                    if decision is not None:
                        self.decision_audit.record_decision(
                            security_id=security_id,
                            symbol=symbol,
                            decision=decision
                        )

                    # --- Proactive rejection debug framework with Enum Unwrapping ---
                    if not decision.get("selected", False):
                        if brain:
                            action_obj = getattr(brain, "action", None)
                            action_val = action_obj.value if hasattr(action_obj, "value") else action_obj
                            
                            print(f"❌ BRAIN REJECTED : {symbol}")
                            print(f"Action  : {action_val if action_val is not None else 'N/A'}")
                            print(f"Reasons : {getattr(brain, 'reasons', 'N/A')}\n")
                        else:
                            print(f"❌ ENGINE SKIPPED : {symbol} - Reason: {decision.get('reasons', ['Fallback criteria not met'])}")
                        return

                    # Validate macro structural layout risk constraints

                    if brain is None:
                        print(f"❌ No Brain decision available for {symbol}")
                        return
                    
                    portfolio_decision = self.portfolio_risk_manager.can_take_trade(
                        opportunity=brain.opportunity 
                        )

                    self.decision_audit.record_portfolio_decision(
                        security_id=security_id,
                        portfolio_decision=portfolio_decision
                    )

                    if not portfolio_decision.allowed:
                        self.monitor.increment("portfolio_rejected")
                        return

                    self.monitor.increment("signals")

                    stop_loss = orb["low"] - ORB_BUFFER

                    qty = self.position_manager.open_position(
                        security_id, symbol, ltp, stop_loss
                    )

                    # PositionManager could not calculate a valid quantity
                    if qty <= 0:
                         self.monitor.increment("insufficient_capital")
                         return
                    
                    trade_value = qty * ltp

                    policy = self.trade_policy_manager.validate(
                        quantity=qty,
                        trade_value=trade_value
                    )

                    if not policy.approved:

                        print(f"TRADE POLICY REJECTED : {policy.reason}")

                        return

                    # --------------------------------------------------
                    # RISK AUTHORIZATION (final gate before execution)
                    #
                    # Daily loss lockout, consecutive-loss pause,
                    # portfolio heat cap, sector concentration cap.
                    # --------------------------------------------------

                    opportunity_sector = ""
                    try:
                        opportunity_sector = getattr(
                            getattr(brain.opportunity, "intelligence", None),
                            "dominant_sector",
                            ""
                        ) or ""
                    except Exception:
                        pass

                    new_risk = max(0.0, (ltp - stop_loss)) * qty

                    risk_allowed, risk_reason = (
                        self.risk_governor.entry_allowed(
                            trades=self.trades,
                            new_risk=new_risk,
                            sector=opportunity_sector
                        )
                    )

                    if not risk_allowed:
                        print(f"🛑 RISK VETO : {symbol} — {risk_reason}")
                        self.monitor.increment("portfolio_rejected")

                        self.decision_audit.record_portfolio_decision(
                            security_id=security_id,
                            portfolio_decision={
                                "action": "RISK_VETO",
                                "allowed": False,
                                "reason": risk_reason
                            }
                        )
                        return

                    execution_result = self.execution.buy(security_id, symbol, ltp, qty)
                    if not execution_result["success"]:
                        return

                    confirmed = self.position_manager.confirm_position(
                         security_id,
                         symbol,
                         ltp,
                         stop_loss,
                         qty
                    )

                    print(f"DEBUG CONFIRM -> {confirmed}")
                    
                    if not confirmed:
                         print("DEBUG -> Position confirmation failed")
                         return
                    
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

                    new_trade["qty"] = qty
                    new_trade["symbol"] = symbol
                    new_trade["entry_time"] = ltt
                    new_trade["entry_date"] = datetime.now().strftime("%Y-%m-%d")
                    new_trade["capital_used"] = round(qty * ltp, 2)
                    new_trade["orb"] = {"high": orb["high"], "low": orb["low"]}
                    new_trade["decision"] = decision

                    # --------------------------------------------------
                    # Institutional Trade Context
                    # --------------------------------------------------

                    # Bug fix: sector/industry/theme live on the
                    # opportunity's INTELLIGENCE snapshot, and
                    # conviction lives on the opportunity itself.
                    # The old getattr calls always returned "".

                    opportunity_intelligence = getattr(
                        brain.opportunity,
                        "intelligence",
                        None
                    )

                    new_trade["sector"] = getattr(
                        opportunity_intelligence,
                        "dominant_sector",
                        ""
                    ) or ""

                    new_trade["industry"] = getattr(
                        opportunity_intelligence,
                        "dominant_industry",
                        ""
                    ) or ""

                    new_trade["theme"] = getattr(
                        opportunity_intelligence,
                        "dominant_theme",
                        ""
                    ) or ""

                    new_trade["conviction"] = getattr(
                        brain.opportunity,
                        "conviction",
                        0
                    )

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

                    self.portfolio_risk_manager.add_trade(brain.opportunity)

                    if __debug__:
                        assert symbol in self.portfolio_risk_manager.open_trades, (
                            f"Portfolio allocation state out of sync for {symbol}"
                        )

                    self.trades[security_id] = new_trade

                    # Commit ledger adjustments for capital calculation tracking
                    capital_used = qty * ltp
                    self.portfolio_ledger.record_buy(capital_used=capital_used)

                    self.open_position_manager.add(security_id, new_trade)
                    self.orb_engine.set_entry_taken(security_id)
                    self.position_recovery.save(self.trades)

            # ---------------------------------
            # POSITION EXIT PIPELINE
            # ---------------------------------
            else:
                if self.trade_controller.is_exit_all_requested():
                    result = self.EXIT_MANUAL
                else:
                    result = self.risk_manager.update(trade, ltp, ltt)

                # --------------------------------------------------
                # Dynamic Trade Management
                # (partial booking / trail ratchet / catalyst exit)
                # --------------------------------------------------
                if result == "ACTIVE":
                    try:
                        advice = self.dynamic_trade_manager.advise(
                            symbol, trade, ltp
                        )

                        if advice["action"] == "EXIT":
                            print(
                                f"⚡ CATALYST EXIT : {symbol} — "
                                f"{advice['reason']}"
                            )
                            result = self.EXIT_SYSTEM

                        elif advice["action"] == "TIGHTEN":
                            trade["trail_sl"] = advice["new_trail"]
                            trade["trail_active"] = True
                            print(
                                f"🔒 TRAIL RATCHET : {symbol} — "
                                f"{advice['reason']}"
                            )

                        elif advice["action"] == "PARTIAL_BOOK":
                            book_qty = advice["qty"]

                            partial_result = self.execution.sell(
                                security_id, symbol, ltp, book_qty
                            )

                            if partial_result["success"]:
                                partial_pnl = (
                                    (ltp - trade["entry"]) * book_qty
                                )

                                self.position_manager.reduce_position(
                                    security_id, book_qty, ltp
                                )

                                self.portfolio_ledger.record_sell(
                                    capital_released=book_qty * ltp,
                                    gross_pnl=partial_pnl
                                )

                                trade["qty"] -= book_qty
                                trade["partial_done"] = True
                                trade["stage"] = "PARTIAL_BOOKED"

                                self.position_recovery.save(
                                    self.trades
                                )

                                print(
                                    f"💰 PARTIAL BOOK : {symbol} "
                                    f"{book_qty} @ {ltp:.2f} "
                                    f"(₹{partial_pnl:.0f})"
                                )

                                self.telegram.send(
                                    f"💰 PARTIAL PROFIT BOOKED\n\n"
                                    f"Stock    : {symbol}\n"
                                    f"Booked   : {book_qty} @ "
                                    f"₹{ltp:.2f}\n"
                                    f"PnL      : ₹{partial_pnl:.2f}\n"
                                    f"Running  : {trade['qty']} left\n"
                                    f"Reason   : {advice['reason']}"
                                )

                    except Exception as dyn_error:
                        # Dynamic management must never
                        # break the hard exit path
                        print(f"[DYNAMIC] {dyn_error}")

                if result == self.EXIT_TARGET:
                    self.monitor.increment("target")
                elif result == self.EXIT_STOPLOSS:
                    self.monitor.increment("stoploss")
                elif result == self.EXIT_TIME:
                    self.monitor.increment("time_exit")

                if result in [
                    self.EXIT_TARGET,
                    self.EXIT_STOPLOSS,
                    self.EXIT_TIME,
                    self.EXIT_MANUAL,
                    self.EXIT_SYSTEM,
                ]:
                    pnl = (ltp - trade["entry"]) * trade["qty"]

                    execution_result = self.execution.sell(
                        security_id, symbol, ltp, trade["qty"]
                    )
                    if not execution_result["success"]:
                        return

                    capital_released = trade["qty"] * ltp
                    self.portfolio_ledger.record_sell(
                        capital_released=capital_released,
                        gross_pnl=pnl
                    )

                    self.decision_audit.record_result(
                        security_id=security_id,
                        result={
                            "exit_price": ltp,
                            "exit_time": ltt,
                            "exit_reason": result,
                            "pnl": round(pnl, 2)
                        }
                    )
                    
                    self.portfolio_risk_manager.remove_trade(symbol)
                    print(f"SELL : {symbol} @ {ltp:.2f} PnL:{pnl:.2f}")

                    icon, title = "🔴", "SELL EXECUTED"
                    if result == self.EXIT_TARGET:
                        icon, title = "🟢", "TARGET HIT"
                    elif result == self.EXIT_TIME:
                        icon, title = "🟡", "TIME EXIT"
                    elif result == self.EXIT_MANUAL:
                        icon, title = "🚨", "MANUAL EXIT"
                    elif result == self.EXIT_SYSTEM:
                        icon, title = "⚠️", "SYSTEM EXIT"

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
                        trade_date=trade["entry_date"],
                        entry_time=trade["entry_time"],
                        exit_time=ltt,
                        symbol=symbol,

                        sector=trade.get("sector", ""),
                        industry=trade.get("industry", ""),
                        theme=trade.get("theme", ""),
                        qty=trade["qty"],

                        entry_price=trade["entry"],
                        exit_price=ltp,
                        
                        pnl=round(pnl, 2),

                        exit_reason=result,

                        conviction=trade.get("conviction", 0),
                    )

                    # --------------------------------------------------
                    # Institutional Memory : record the outcome
                    # --------------------------------------------------

                    try:
                        # Risk Governor learns the result
                        # (loss streaks, daily lockout re-check)
                        self.risk_governor.on_trade_closed(pnl)

                        trade_sector = trade.get("sector", "")

                        # ORB outcome memory (repeated-failure
                        # pattern detection feeds on this)
                        if result == self.EXIT_TARGET:
                            orb_outcome = "SUCCESS"
                        elif result == self.EXIT_STOPLOSS:
                            orb_outcome = "FAILED"
                        else:
                            orb_outcome = result

                        self.market_memory.record_orb_outcome(
                            symbol=symbol,
                            sector=trade_sector,
                            outcome=orb_outcome,
                            pnl=round(pnl, 2)
                        )

                        # Trade outcome memory
                        self.market_memory.record_trade_outcome({
                            "trade_date": trade.get("entry_date", ""),
                            "symbol": symbol,
                            "sector": trade_sector,
                            "industry": trade.get("industry", ""),
                            "theme": trade.get("theme", ""),
                            "entry_time": trade.get("entry_time", ""),
                            "exit_time": ltt,
                            "exit_reason": result,
                            "conviction": trade.get("conviction", 0),
                            "pnl": round(pnl, 2),
                        })

                        # Permanent company history
                        self.company_intelligence.record_trade(
                            symbol=symbol,
                            exit_reason=result,
                            pnl=pnl
                        )

                    except Exception as memory_error:
                        # Memory failures must never block exits
                        print(f"[MEMORY] Recording failed: {memory_error}")

                    self.position_manager.close_position(security_id, pnl)
                    self.open_position_manager.remove(security_id)
                    del self.trades[security_id]
                    
                    if self.trades:
                        self.position_recovery.save(self.trades)
                    else:
                        self.position_recovery.clear()

                    if self.trade_controller.is_exit_all_requested() and not self.trades:
                        self.trade_controller.clear_exit_all()
                        self.telegram.send(
                            "✅ EXIT ALL COMPLETED\n\n"
                            "All open positions have been successfully closed.\n\n"
                            "Remaining Positions : 0"
                        )

        except Exception as e:
            print(f"\n❌ TICK PROCESSING ERROR — {symbol} @ {ltt}")
            print(f"Error: {e}")
            traceback.print_exc()

            now = datetime.now()
            self._tick_error_timestamps.append(now)
            # Keep only errors from the last 60 seconds
            self._tick_error_timestamps = [
                t for t in self._tick_error_timestamps
                if (now - t).total_seconds() <= 60
            ]

            # Alert only if errors are clustering (5+ in the last minute),
            # not on every isolated bad tick — avoids alert spam on normal
            # noisy/malformed ticks while still catching real systemic issues
            if len(self._tick_error_timestamps) >= 5:
                try:
                    self.telegram.send(
                        f"⚠️ REPEATED TICK ERRORS\n\n"
                        f"5+ errors in the last minute — possible systemic issue.\n"
                        f"Latest: {symbol} — {str(e)[:150]}"
                    )
                except Exception:
                    # Never let a Telegram failure cause a further crash
                    pass

        finally:
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
    
    def run_capital_allocation_cycle(self):
        """
        Institutional Capital Allocation Pipeline
        """

        # --------------------------------------------------
        #  1. Read Opportunity Pool
        # --------------------------------------------------

        opportunities = (
            self.trade_selection_engine
                    .opportunity_pool
                    .ranked()
        )
        
        if not opportunities:
            return
        
        
        print("\n" + "=" * 70)
        print("         CAPITAL ALLOCATION CYCLE")
        print("=" * 70)
        
        
        print(f"Qualified Opportunities : {len(opportunities)}")

        # --------------------------------------------------
        # Temporary Debug Output
        # --------------------------------------------------

        for i, opportunity in enumerate(opportunities[:10], start=1):
            
            
            symbol = getattr(opportunity, "symbol", "UNKNOWN")
            conviction = getattr(opportunity, "conviction", 0)

            print(
                f"{i:02d}. "
                f"{symbol:<15} "
                f"Conviction : {conviction}"
            )

            print("=" * 70)


    def shutdown(self):
        # Persist today's sector leadership before closing
        self.record_sector_memory()
        self.market_recorder.close()

    def pause(self):
        self.trade_controller.disable_entries()
        return {"success": True, "message": "New entries paused."}

    def resume(self):
        self.trade_controller.enable_entries()
        return {"success": True, "message": "New entries resumed."}

    def trading_off(self):
        self.trade_controller.disable_trading()
        self.trade_controller.disable_entries()
        return {"success": True, "message": "Trading disabled."}

    def trading_on(self):
        self.trade_controller.enable_trading()
        self.trade_controller.enable_entries()
        return {"success": True, "message": "Trading enabled."}

    def exit_all(self):
        self.trade_controller.request_exit_all()
        return {"success": True, "message": "Exit All requested."}

    def ledger(self):
        return self.portfolio_ledger.summary()

    def trade_controller_status(self):
        return self.trade_controller.status()

    # --------------------------------------------------
    # Institutional Intelligence Accessors
    # (used by the Telegram Command Center)
    # --------------------------------------------------

    def risk_status(self):
        status = self.risk_governor.status()
        status["portfolio_heat"] = (
            self.risk_governor.portfolio_heat(self.trades)
        )
        return status

    def memory_report(self, symbol):
        sector = ""
        try:
            profile = self.company_intelligence.get_profile(symbol)
            sector = profile.get("sector", "")
        except Exception:
            pass

        return self.pattern_engine.report(symbol, sector)

    def company_report(self, symbol):
        return self.company_intelligence.report(symbol)

    def opportunity_pool_report(self, limit=10):
        opportunities = (
            self.trade_selection_engine
                .opportunity_pool
                .ranked()
        )

        if not opportunities:
            return "OPPORTUNITY POOL\n\nEmpty."

        lines = ["OPPORTUNITY POOL", ""]

        for i, opportunity in enumerate(
            opportunities[:limit], start=1
        ):
            symbol = getattr(opportunity, "symbol", "?")
            conviction = getattr(opportunity, "conviction", 0)
            lines.append(
                f"{i:02d}. {symbol:<12} "
                f"Conviction {conviction:.1f}"
            )

        return "\n".join(lines)

    def exposure_report(self):
        """
        Portfolio-aware intelligence: what is the book
        actually exposed to right now?
        """
        if not self.trades:
            return "PORTFOLIO EXPOSURE\n\nNo open positions."

        sectors = {}
        themes = {}
        total_value = 0.0
        total_risk = 0.0

        for trade in self.trades.values():
            value = trade.get("entry", 0) * trade.get("qty", 0)
            risk = max(
                0.0,
                trade.get("entry", 0) - trade.get("stop_loss", 0)
            ) * trade.get("qty", 0)

            total_value += value
            total_risk += risk

            sector = trade.get("sector", "") or "UNKNOWN"
            theme = trade.get("theme", "") or "UNKNOWN"

            sectors[sector] = sectors.get(sector, 0) + value
            themes[theme] = themes.get(theme, 0) + value

        lines = [
            "PORTFOLIO EXPOSURE",
            "",
            f"Positions   : {len(self.trades)}",
            f"Deployed    : ₹{total_value:,.0f}",
            f"Open Risk   : ₹{total_risk:,.0f}",
            "",
            "By Sector:",
        ]

        for sector, value in sorted(
            sectors.items(), key=lambda x: -x[1]
        ):
            pct = value / total_value * 100 if total_value else 0
            flag = " ⚠️" if pct > 50 else ""
            lines.append(
                f"• {sector}: ₹{value:,.0f} ({pct:.0f}%){flag}"
            )

        lines.append("")
        lines.append("By Theme:")

        for theme, value in sorted(
            themes.items(), key=lambda x: -x[1]
        )[:5]:
            pct = value / total_value * 100 if total_value else 0
            lines.append(
                f"• {theme}: ₹{value:,.0f} ({pct:.0f}%)"
            )

        return "\n".join(lines)

    # --------------------------------------------------

    def calibration_report(self):
        """
        Learning layer: does conviction MEAN anything?
        Conviction band vs. realized win rate.
        """
        try:
            report = (
                self.market_memory
                    .repository
                    .calibration_report()
            )
        except Exception:
            return "CALIBRATION\n\nMemory unavailable."

        lines = [
            "CONVICTION CALIBRATION",
            "(band → trades, win rate, PnL)",
            "",
        ]

        any_data = False

        for band in report:
            if band["trades"] == 0:
                continue
            any_data = True
            lines.append(
                f"• {band['band']:>6} : "
                f"{band['trades']} trades, "
                f"{band['win_rate']}% wins, "
                f"₹{band['total_pnl']:,.0f}"
            )

        if not any_data:
            lines.append(
                "No graded trades yet — calibration "
                "builds as trades close."
            )
        else:
            lines += [
                "",
                "Higher bands should win more often.",
                "If they don't, conviction is miscalibrated.",
            ]

        return "\n".join(lines)

    # --------------------------------------------------

    def events_report(self, symbol=None):
        return self.event_intelligence.report(symbol)

    # --------------------------------------------------

    def fno_report(self):
        return self.fno_opportunity_engine.report()

    # --------------------------------------------------

    def graph_report(self, symbol):
        return self.knowledge_graph.report(symbol)

    # --------------------------------------------------

    def calendar_report(self):
        return self.results_calendar.report()

    # --------------------------------------------------

    def calendar_add(self, symbol, date):
        return self.results_calendar.add(symbol, date)

    # --------------------------------------------------

    def causal_report(self, symbol=None):
        return self.causal_engine.report(symbol)

    # --------------------------------------------------

    def edge_report(self):
        from edge_analyzer import EdgeAnalyzer
        return EdgeAnalyzer().report()

    # --------------------------------------------------

    def execution_report(self):
        from execution_quality import ExecutionQuality
        summary = ExecutionQuality().summary()

        if not summary:
            return "EXECUTION QUALITY\n\nNo fills logged."

        lines = [
            "EXECUTION QUALITY",
            "",
            f"Fills logged : {summary['fills']}",
            f"Graded       : {summary['graded']}",
        ]

        if summary.get("graded"):
            lines += [
                f"Avg slippage : "
                f"{summary['avg_slippage_bps']} bps",
                f"Worst        : "
                f"{summary['worst_slippage_bps']} bps",
                f"Total cost   : "
                f"₹{summary['total_slippage_rupees']}",
            ]

        return "\n".join(lines)

    # --------------------------------------------------

    def journal_report(self):
        """
        Today's decision journal from the audit log.
        """
        audit = self.decision_audit.all()

        if not audit:
            return "DECISION JOURNAL\n\nNo decisions today."

        executed = 0
        rejected = 0
        risk_vetoed = 0

        lines_detail = []

        for record in audit.values():
            symbol = record.get("symbol", "?")
            decision = record.get("decision") or {}
            selected = (
                decision.get("selected", False)
                if isinstance(decision, dict) else False
            )
            portfolio = record.get("portfolio")
            execution = record.get("execution")
            result = record.get("result")

            if execution:
                executed += 1
                status = "EXECUTED"
                if result:
                    status += (
                        f" → {result.get('exit_reason', 'OPEN')}"
                        f" ₹{result.get('pnl', 0)}"
                    )
            elif (
                isinstance(portfolio, dict)
                and portfolio.get("action") == "RISK_VETO"
            ):
                risk_vetoed += 1
                status = "RISK VETO"
            elif selected:
                status = "SELECTED (not executed)"
            else:
                rejected += 1
                status = "REJECTED"

            lines_detail.append(f"• {symbol}: {status}")

        lines = [
            "DECISION JOURNAL (today)",
            "",
            f"Evaluated  : {len(audit)}",
            f"Executed   : {executed}",
            f"Rejected   : {rejected}",
            f"Risk Vetos : {risk_vetoed}",
            "",
        ] + lines_detail[:15]

        return "\n".join(lines)

    # --------------------------------------------------

    def eod_report(self):
        """
        End-of-day institutional summary.
        """
        capital = self.capital()
        mtm = self.mtm()
        ledger = self.ledger() or {}
        risk = self.risk_status()

        lines = [
            "END OF DAY REPORT",
            "",
            f"Net PnL      : ₹{mtm['net']:,.2f}",
            f"Realized     : ₹{mtm['realized']:,.2f}",
            f"Floating     : ₹{mtm['floating']:,.2f}",
            "",
            f"Capital Used : ₹{capital['starting'] - capital['available']:,.0f}",
            f"Available    : ₹{capital['available']:,.0f}",
            "",
            f"Trades Closed  : {risk['trades_closed']}",
            f"Entries Blocked: {risk['entries_blocked']}",
            f"Loss Streak    : {risk['consecutive_losses']}",
            f"Kill Switch    : "
            f"{'FIRED — ' + risk['lock_reason'] if risk['locked'] else 'not fired'}",
        ]

        # Persist sector leadership for streak memory
        recorded = self.record_sector_memory()
        lines.append("")
        lines.append(
            f"Sector memory updated ({recorded} sectors)."
        )

        # Event outcome write-back: grade today's
        # structured events with realized day moves —
        # this is what makes event memory predictive.
        graded = self.event_intelligence.write_outcomes(
            price_engine.get_change
        )
        lines.append(
            f"Event outcomes graded: {graded}."
        )

        return "\n".join(lines)

    # --------------------------------------------------

    def morning_brief(self):
        """
        Institutional pre-market brief:
        risk state, active catalysts, sector streaks,
        F&O watchlist, opportunity pool.
        """
        lines = ["🌅 INSTITUTIONAL BRIEF", ""]

        # Risk state
        risk = self.risk_status()
        lines.append(
            f"Risk : "
            f"{'🔒 LOCKED — ' + risk['lock_reason'] if risk['locked'] else '🟢 clear'}"
            f" | Day PnL ₹{risk['day_pnl']:,.0f}"
        )

        # Active market catalysts (memory)
        try:
            active = self.market_memory.active_rules()
            if active:
                lines.append("")
                lines.append(
                    f"Active Catalysts ({len(active)}):"
                )
                for rule in active[:5]:
                    lines.append(f"• {rule}")
        except Exception:
            pass

        # Sector streaks
        try:
            streaks = (
                self.market_memory
                    .repository
                    .top_sector_streaks()
            )
            if streaks:
                lines.append("")
                lines.append("Sector Leadership Streaks:")
                for s in streaks[:5]:
                    lines.append(
                        f"• {s['sector']} — "
                        f"{s['streak']} day(s) in top 3"
                    )
        except Exception:
            pass

        # F&O watchlist
        watchlist = self.fno_opportunity_engine.get_watchlist()
        if watchlist:
            lines.append("")
            lines.append(
                f"F&O Catalyst Watchlist ({len(watchlist)}):"
            )
            for entry in watchlist[:5]:
                lines.append(
                    f"• {entry['symbol']} — "
                    f"{entry.get('event_type', '?')} "
                    f"(imp {entry['importance']:.0f})"
                )
        else:
            lines.append("")
            lines.append("F&O Watchlist : empty")

        return "\n".join(lines)

    # --------------------------------------------------

    def record_sector_memory(self):
        """
        Persist today's sector leadership ranking into
        institutional memory (leadership streak tracking).
        """
        try:
            rankings = self.sector_engine.get_rankings() or []

            for i, entry in enumerate(rankings, start=1):
                if isinstance(entry, dict):
                    sector = (
                        entry.get("sector")
                        or entry.get("name")
                        or ""
                    )
                    score = (
                        entry.get("score")
                        or entry.get("participation")
                        or 0
                    )
                else:
                    sector = str(entry)
                    score = 0

                if sector:
                    self.market_memory.record_sector_day(
                        sector=sector,
                        rank=i,
                        score=score
                    )

            return len(rankings)

        except Exception as e:
            print(f"[MEMORY] Sector memory failed: {e}")
            return 0

    # --------------------------------------------------
    # Legacy Market Intelligence Pipeline
    # 
    # Deprecated:
    # orchestrated inside NewsEngine.process().
    #
    # This method is retained temporarily during
    # migration and should not be used.
    # --------------------------------------------------

    def _process_market_news(self, news):
        try:
            classified_news = self.news_classifier.classify(news)
            if classified_news is None:
                return

            impact = self.impact_engine.evaluate(classified_news)
            if impact is None:
                return

            self.market_catalyst.update(impact)
            self.market_memory.remember(impact)
            self.market_environment.update(impact)

        except Exception as e:
            print("\n========== MARKET INTELLIGENCE ERROR ==========")
            print(e)
            print("===============================================\n")