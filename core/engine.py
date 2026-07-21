from datetime import datetime
import os
from dotenv import load_dotenv
from core.historical_data import HistoricalData
from notifications.telegram_notifier import TelegramNotifier
from trading.position_recovery import PositionRecovery
from trading.open_position_manager import OpenPositionManager
from trading.trade_selection_engine import TradeSelectionEngine
import traceback
from config import ORB_BUFFER
from trading.portfolio_risk_manager import PortfolioOpportunity
from trading.trade_policy_manager import TradePolicyManager

from core.day_summary import DaySummary
from core.watchdog import Watchdog
from core.bot_monitor import BotMonitor
from core.tick_cache import TickCache
from core.orb_engine import ORBEngine
from core.strategy import Strategy
from trading.position_manager import PositionManager
from trading.execution import Execution
from trading.broker_sync import BrokerSync
from trading.risk_manager import RiskManager
from trading.trade_logger import TradeLogger
from trading.capital_manager import CapitalManager
from intelligence.sector_engine import SectorEngine
from intelligence.price_engine import price_engine
from intelligence.industry_engine import IndustryEngine
from intelligence.results_engine import ResultsEngine
from intelligence.theme_engine import ThemeEngine
from intelligence.relative_strength_engine import RelativeStrengthEngine
from intelligence.market_mood_engine import MarketMoodEngine
from core.candle_engine import candle_engine
from config import DECISION_TRACE

# Core infrastructure routing elements
from core.system_registry import SystemRegistry
from intelligence.intelligence_engine import IntelligenceEngine
from trading.portfolio_risk_manager import PortfolioRiskManager
from trading.allocation_trigger_engine import AllocationTriggerEngine
from trading.capital_allocation_engine import CapitalAllocationEngine
from intelligence.opportunity_ranker import OpportunityRanker
from trading.portfolio_intelligence_engine import PortfolioIntelligenceEngine

from core.decision_audit import DecisionAudit

# Portfolio Control
from trading.trade_controller import TradeController
from core.market_recorder import MarketRecorder
from trading.portfolio_ledger import PortfolioLedger

# Market Intelligence Collectors & Models
from collectors.news_rss_collector import NewsRSSCollector
from collectors.bse_corporate_collector import BSECorporateCollector
from news.news_classifier import NewsClassifier
from news.impact_engine import ImpactEngine
from news.market_catalyst import MarketCatalyst
from intelligence.market_memory import MarketMemory
from intelligence.market_environment import MarketEnvironment
from news.news_engine import NewsEngine

# Institutional Risk & Memory Intelligence
from trading.risk_governor import RiskGovernor
from intelligence.pattern_engine import PatternEngine
from intelligence.company_intelligence import CompanyIntelligence
from intelligence.event_intelligence import EventIntelligence
from intelligence.fno_opportunity_engine import FnOOpportunityEngine
from intelligence.knowledge_graph import KnowledgeGraph
from intelligence.results_calendar import ResultsCalendar
from trading.dynamic_trade_manager import DynamicTradeManager
from intelligence.causal_reasoning_engine import CausalReasoningEngine
from intelligence.market_state_engine import market_state_engine
from intelligence.reaction_decay import ReactionDecayEngine
from trading.shock_responder import ShockResponder
from collectors.results_calendar_collector import (
    ResultsCalendarCollector,
    NseResultsCalendarCollector,
)

from intelligence.intelligence_context import IntelligenceContext

load_dotenv()


# ==========================================================
# Portfolio view adapter for the Capital Allocation Cycle
#
# PortfolioIntelligenceEngine.evaluate() needs a generic
# "portfolio" object with .weakest_position(). PortfolioLedger
# is deliberately scoped to financial accounting only (its own
# docstring: "Does NOT: Manage positions"), so this stays a
# small, separate, read-only view over Engine.trades instead of
# adding position logic to the ledger.
# ==========================================================

class _WeakestPosition:
    def __init__(self, symbol, conviction, holding_seconds):
        self.symbol = symbol
        self.conviction = conviction
        self.holding_seconds = holding_seconds


class TradesPortfolioView:

    def __init__(self, trades):
        self._trades = trades

    def __bool__(self):
        return bool(self._trades)

    def weakest_position(self):
        if not self._trades:
            return None

        sid, trade = min(
            self._trades.items(),
            key=lambda item: item[1].get("conviction", 0),
        )

        holding_seconds = self._holding_seconds(
            trade.get("entry_time", "")
        )

        return _WeakestPosition(
            symbol=trade.get("symbol", "?"),
            conviction=trade.get("conviction", 0),
            holding_seconds=holding_seconds,
        )

    @staticmethod
    def _holding_seconds(entry_time):
        """
        entry_time is a bare "HH:MM:SS" string with no date, so
        naive subtraction against now() can go negative in edge
        cases (same class of issue already fixed in
        PositionThesisEngine._minutes_since). Never let a
        negative diff look like "just entered."
        """
        if not entry_time:
            return 0
        try:
            now = datetime.now()
            hh, mm, ss = (entry_time.split(":") + ["0", "0"])[:3]
            entered = now.replace(
                hour=int(hh), minute=int(mm),
                second=int(ss), microsecond=0
            )
            elapsed = (now - entered).total_seconds()
            return elapsed if elapsed >= 0 else 999999
        except Exception:
            return 999999


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
        from trading.option_leg import OptionLeg
        # Additive ATM option leg — rides alongside the equity entry,
        # never modifies it. Telegram is attached after it is created below.
        self.option_leg = OptionLeg(self.execution)
        self.broker_sync = BrokerSync()
        self.risk_manager = RiskManager()
        from config import MAX_OPEN_POSITIONS
        self.portfolio_risk_manager = PortfolioRiskManager(
            max_open_trades=MAX_OPEN_POSITIONS
        )
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
        # Give the option leg a handle to Telegram for entry/exit alerts
        self.option_leg.telegram = self.telegram

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

        # Capital profile banner — makes the active
        # account size and leverage impossible to miss.
        from config import (
            CAPITAL_PROFILE,
            CAPITAL,
            MIS_LEVERAGE,
            BUYING_POWER,
            MAX_CAPITAL_PER_TRADE,
            TRADING_MODE,
        )
        print("\n" + "=" * 60)
        print(f"  CAPITAL PROFILE : {CAPITAL_PROFILE}  "
              f"({TRADING_MODE} mode)")
        print("=" * 60)
        print(f"  Equity        : ₹{CAPITAL:,.0f}")
        print(f"  Leverage      : {MIS_LEVERAGE}× (MIS)")
        print(f"  Buying Power  : ₹{BUYING_POWER:,.0f}")
        print(f"  Max per trade : ₹{MAX_CAPITAL_PER_TRADE:,.0f} "
              f"(value)")
        print("=" * 60 + "\n")

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
            company_intelligence=self.company_intelligence,
            price_lookup=price_engine.get_change
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

        # --------------------------------------------------
        # Fix (2026-07-20): wire these 5 intelligence engines
        # into the Brain's evidence pipeline.
        #
        # Root cause found live: self.trade_selection_engine =
        # TradeSelectionEngine() was called with ZERO arguments
        # up in __init__ (before any of these 5 engines existed
        # yet). TradeSelectionEngine's pattern_engine,
        # company_intelligence, event_intelligence, fno_engine,
        # and knowledge_graph all default to None, and every
        # evidence-gathering block that uses them is guarded by
        # "if self.xxx is not None:" -- so all of it was silently
        # skipped, every candidate, every day, despite each of
        # these engines being fully built, instantiated, and
        # passing its own dedicated tests. This is what was
        # confirmed live as "Continuation" always showing 0.0 in
        # the Brain's quality inputs (Continuation is derived from
        # Pattern/Company evidence specifically) -- and likely a
        # meaningful chunk of missing event/catalyst richness too.
        #
        # Note: the constructor parameter is named "fno_engine"
        # even though this instance's attribute is
        # "fno_opportunity_engine" -- mapped correctly below.
        # --------------------------------------------------
        self.trade_selection_engine.pattern_engine = (
            self.pattern_engine
        )
        self.trade_selection_engine.company_intelligence = (
            self.company_intelligence
        )
        self.trade_selection_engine.event_intelligence = (
            self.event_intelligence
        )
        self.trade_selection_engine.fno_engine = (
            self.fno_opportunity_engine
        )
        self.trade_selection_engine.knowledge_graph = (
            self.knowledge_graph
        )

        # Results Calendar : no new risk into binary events
        self.results_calendar = ResultsCalendar(
            repository=self.market_memory.repository
        )

        # Results Watchlist : pre-result WATCH → post-result
        # CATALYST (active daily opportunity funnel)
        from intelligence.results_watchlist import (
            ResultsWatchlist,
        )
        self.results_watchlist = ResultsWatchlist(
            results_calendar=self.results_calendar,
            event_intelligence=self.event_intelligence,
        )

        # News Watchlist : which symbols currently have a live
        # news story attached (counterpart to the results
        # watchlist above, for non-scheduled catalysts).
        from intelligence.news_watchlist import NewsWatchlist
        self.news_watchlist = NewsWatchlist()

        # Dashboard Bridge (2026-07-21) : file-based command/
        # state channel to the separate dashboard.py process --
        # powers the interactive Sell / Check Now / Schedule
        # Check controls. See core/dashboard_bridge.py.
        from core.dashboard_bridge import DashboardBridge
        self.dashboard_bridge = DashboardBridge(self)

        # Calendar Harvester : auto-populate the
        # calendar from board-meeting intimations
        from intelligence.calendar_harvester import CalendarHarvester
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

        # Reaction Decay Engine : learns that repeated
        # shocks of the same type shrink as the market
        # anticipates them (1st shock big, 2nd smaller).
        self.reaction_decay = ReactionDecayEngine(
            repository=self.market_memory.repository
        )

        # HOLD BRAIN : continuously re-scores open
        # positions and exits when the thesis decays
        # (withdraw on deterioration).
        from trading.position_thesis import (
            PositionThesisEngine,
        )
        self.position_thesis = PositionThesisEngine(
            trade_selection_engine=self.trade_selection_engine,
            intelligence_engine=self.intelligence_engine,
            sector_engine=self.sector_engine,
        )
        # Share with trade selection for evidence scaling
        self.trade_selection_engine.reaction_decay = (
            self.reaction_decay
        )
        self.trade_selection_engine.results_watchlist = (
            self.results_watchlist
        )
        self.trade_selection_engine.news_watchlist = (
            self.news_watchlist
        )

        # Market State + Shock Responder
        self.market_state_engine = market_state_engine
        self._last_state_check = None

        self.shock_responder = ShockResponder(
            trade_controller=self.trade_controller,
            sector_engine=self.sector_engine,
            company_intelligence=self.company_intelligence,
            telegram=self.telegram,
        )
        # Governor shock guards flow into the responder
        self.risk_governor.shock_callback = (
            self.shock_responder.trigger
        )

        # Event-driven entry session state
        self._entered_today = set()

        # Continuous news ingestion timer (2026-07-21)
        from config import NEWS_INGEST_SECONDS
        self._last_news_ingest = None
        self._news_ingest_seconds = NEWS_INGEST_SECONDS

        # Dashboard live-price sync timer (2026-07-21) -- see
        # process_tick() for why this exists: open_positions.json
        # was previously only rewritten on entry/partial-book/exit
        # and never carried a live price, so dashboard.py's Open
        # Positions table showed a live PnL that never moved for
        # the life of a trade.
        self._last_dashboard_sync = None
        self._dashboard_sync_seconds = 2

        # Auto-populate results calendar in background
        # (network must never delay startup)
        import threading as _threading
        self.results_collector = ResultsCalendarCollector(
            results_calendar=self.results_calendar,
            harvester=self.calendar_harvester,
            company_intelligence=self.company_intelligence,
        )
        _threading.Thread(
            target=self.results_collector.fetch,
            daemon=True,
            name="ResultsCalendarFetch",
        ).start()

        # Second, independent calendar source (2026-07-21).
        # BSE's fetch above has been observed failing to
        # connect from cloud origins -- rather than rely on
        # a single source, NSE's own board-meetings feed
        # runs alongside it. Both write into the SAME
        # results_calendar; neither depends on the other.
        self.nse_results_collector = NseResultsCalendarCollector(
            results_calendar=self.results_calendar,
            harvester=self.calendar_harvester,
            company_intelligence=self.company_intelligence,
        )
        _threading.Thread(
            target=self.nse_results_collector.fetch,
            daemon=True,
            name="NseResultsCalendarFetch",
        ).start()

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

            # Fix (2026-07-21): _entered_today is what EVENT
            # entries check (strategy.is_buy_signal's ORB
            # path uses orb["entry_taken"] instead, already
            # reconciled above via set_entry_taken -- but
            # _entered_today was NEVER reconciled anywhere,
            # confirmed live today causing repeated same-day
            # re-entries on EVENT-mode trades after every
            # kill-switch restart (INDIGO twice, DMART four
            # times, with real repeat losses). Recovering an
            # already-open position's symbol here is free, since
            # we're already looping through self.trades.
            self._entered_today.add(trade["symbol"])

        if self.trades:
            print(f"Recovered {len(self.trades)} open position(s).")

        # ---------------------------------
        # Closed-Today Reconciliation for _entered_today
        #
        # Covers the other half: a symbol that already traded
        # AND CLOSED earlier today (like DMART's first two
        # stopped-out entries) still needs to be blocked from
        # re-entering via EVENT after a restart, even
        # though it's no longer in self.trades. Reads
        # trade_log_v2.csv directly, self-contained -- no
        # dependency on market_data.py wiring this time.
        # ---------------------------------
        try:
            import csv as _csv
            from datetime import date as _date
            from config import TRADE_LOG_FILE

            today_str = _date.today().strftime("%Y-%m-%d")
            closed_today_count = 0

            with open(
                TRADE_LOG_FILE, "r", newline="", encoding="utf-8"
            ) as f:
                for row in _csv.DictReader(f):
                    if row.get("Date") != today_str:
                        continue
                    symbol = row.get("Symbol", "")
                    if symbol:
                        self._entered_today.add(symbol)
                        closed_today_count += 1

            print(
                f"[RECONCILE] {closed_today_count} closed-today "
                f"trade(s) + {len(self.trades)} open position(s) "
                f"= {len(self._entered_today)} symbol(s) protected "
                f"from EVENT re-entry this restart."
            )
        except FileNotFoundError:
            pass  # No trades logged yet today -- nothing to reconcile
        except Exception as e:
            print(f"[RECONCILE] _entered_today check failed: {e}")

        self.monitor.set_orb_completed(self.orb_engine.completed_count())
        self.monitor.set_status("RUNNING")
        self.monitor.set_connection("CONNECTED")

    def process_tick(self, security_id, symbol, ltp, ltt):
        try:
            self.monitor.increment_processed_ticks()

            # ---------------------------------
            # Continuous News Ingestion (2026-07-21)
            #
            # Railway stories used to be consumed ONLY
            # inside evaluate() — no breakout, no news, no
            # watchlist all day. Now every NEWS_INGEST_SECONDS
            # the tick loop pulls fresh stories through the
            # full intelligence chain (events → F&O watchlist
            # → causal → graph), independent of breakouts.
            # ---------------------------------
            now = datetime.now()
            if (
                self._last_news_ingest is None
                or (now - self._last_news_ingest).total_seconds()
                >= self._news_ingest_seconds
            ):
                self._last_news_ingest = now
                try:
                    self.trade_selection_engine.ingest_news()
                except Exception as e:
                    print(f"[NEWS INGEST] {e}")

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

            # ---------------------------------
            # Dashboard Live-Price Sync (2026-07-21, throttled)
            # ---------------------------------
            # self.trades (keyed by security_id, same dict
            # position_recovery.save() writes to open_positions.json)
            # never carried a live price -- it was only ever
            # re-saved on entry/partial-book/exit, so dashboard.py's
            # Open Positions table's "Live PnL" column showed a
            # value that never changed for the whole life of a
            # trade. This refreshes ltp/live_pnl on every open
            # trade dict from the same tick_cache already used for
            # floating MTM above, and re-saves -- throttled to once
            # every few seconds (not every tick) since this is a
            # full JSON rewrite, not a hot-path calculation.
            if (
                self._last_dashboard_sync is None
                or (now - self._last_dashboard_sync).total_seconds()
                >= self._dashboard_sync_seconds
            ):
                self._last_dashboard_sync = now

                if self.trades:
                    try:
                        for sid, trade in self.trades.items():
                            tick = self.tick_cache.get(sid)
                            if tick is None:
                                continue
                            live_ltp = tick["ltp"]
                            trade["ltp"] = live_ltp
                            trade["live_pnl"] = round(
                                (live_ltp - trade.get("entry", 0))
                                * trade.get("qty", 0),
                                2,
                            )
                        self.position_recovery.save(self.trades)
                    except Exception as e:
                        print(f"[DASHBOARD SYNC] {e}")

                # Interactive dashboard bridge (2026-07-21):
                # process any Sell / Check Now / Schedule Check
                # commands the dashboard wrote, fire any
                # scheduled checks whose time has arrived, and
                # publish fresh watchlist/response state for the
                # dashboard to read. Same throttle as the
                # position sync above -- all file I/O, no need
                # to do this every single tick.
                try:
                    self.dashboard_bridge.process_commands()
                    self.dashboard_bridge.run_due_schedules()
                    self.dashboard_bridge.write_state()
                except Exception as e:
                    print(f"[DASHBOARD BRIDGE] {e}")

            # --------------------------------------------------
            # Shock Guards + Adaptive Limits
            # --------------------------------------------------
            day_pnl = self.capital_manager.pnl() + total_mtm
            self.risk_governor.on_tick(day_pnl)

            # Throttled market-state refresh (every 30s):
            # regime drives the governor's daily limits
            # and the shock responder's breadth check.
            now_wall = datetime.now()
            if (
                self._last_state_check is None
                or (now_wall - self._last_state_check)
                .total_seconds() >= 30
            ):
                self._last_state_check = now_wall
                state = self.market_state_engine.compute()
                self.risk_governor.set_market_state(state)
                self.shock_responder.check_market(state)

                # Regime-adaptive conviction gate (2026-07-21):
                # feed the same live regime data already used by
                # RiskGovernor into the Brain, so its conviction
                # threshold actually reflects current conditions
                # instead of a permanent "NORMAL" placeholder.
                # state is a dict here (confirmed from
                # RiskGovernor.set_market_state's own
                # state.get("regime", "WARMUP") usage), not an
                # object -- matched that access style exactly.
                self.trade_selection_engine.brain.set_market_regime(
                    regime=state.get("regime", "WARMUP"),
                    confidence=state.get("confidence", 0.0),
                    description=state.get("description", ""),
                    dominant_factor=state.get("dominant_factor", ""),
                )

                # News-feed staleness alarm: if Railway
                # goes silent during market hours, say so
                # instead of trading blind.
                self._check_news_staleness(now_wall)

                # Capital Allocation Cycle: is a better
                # opportunity waiting in the pool than my
                # weakest currently open position? Runs on the
                # same 30s throttle -- no need for a separate
                # timer, and the engine's own minimum-hold-time
                # guard (10 min) means checking this often
                # doesn't cause thrashing.
                self.run_capital_allocation_cycle()

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

            trade = self.trades.get(security_id)

            # NOTE: orb may be None (early session).
            # Exits must still process, and event-driven
            # entries may proceed without an ORB.
            if orb is None and trade is None:
                event_probe = self._event_entry_candidate(
                    symbol, security_id, ltt
                )
                if event_probe is None:
                    return

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

                # --------------------------------------------------
                # ENTRY SIGNAL : ORB breakout OR event catalyst
                # --------------------------------------------------
                entry_mode = "ORB"
                signal = False

                # Manage open option legs every tick: Greeks-aware premium
                # trailing stop (ratchets up, never gives back), hard stop,
                # optional target, and same-day time stop. Cheap no-op when
                # nothing is open; polling is throttled internally.
                self.option_leg.manage(ltt)

                if orb is not None:
                    last_closed_candle = (
                        self.candle_engine.get_latest(symbol)
                    )
                    signal = self.strategy.is_buy_signal(
                        orb, ltt, last_closed_candle
                    )

                event_candidate = None
                if not signal:
                    event_candidate = (
                        self._event_entry_candidate(
                            symbol, security_id, ltt
                        )
                    )
                    if event_candidate is not None:
                        signal = True
                        entry_mode = "EVENT"

                # REMOVED 2026-07-21: Momentum-Runner path
                # (pre-9:30 pure-price entries, no catalyst).
                # It fired universe-wide at 09:16 and produced
                # random trades. Core ideology: news arms the
                # system; ORB breakout close pulls the trigger.

                if signal:
                    print(f"\n========== LIVE {entry_mode} CANDIDATE ==========")
                    print(f"Symbol      : {symbol}")
                    print(f"Time        : {ltt}")
                    print(f"LTP         : {ltp:.2f}")
                    if orb is not None:
                        print(f"ORB High    : {orb['high']:.2f}")
                        print(f"ORB Low     : {orb['low']:.2f}")
                    if event_candidate is not None:
                        print(
                            f"Catalyst    : "
                            f"{event_candidate.get('headline', '')[:70]}"
                        )
                    print("========================================\n")

                    intelligence = self.intelligence_engine.get(symbol)
                    decision = self.trade_selection_engine.evaluate(
                        symbol, ltp, orb, intelligence,
                        entry_mode=entry_mode
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

                        # Fix (2026-07-21): rejections were never
                        # persisted anywhere -- only completed trades
                        # got a save_decision() call, so /why SYMBOL
                        # could never explain a MISS, only a trade
                        # that actually happened. Same repository,
                        # same table (trade_decisions already
                        # supports action="REJECT" by design -- it
                        # was simply never called with it).
                        try:
                            reasons_list = decision.get("reasons") or []
                            reason_text = (
                                "; ".join(str(r) for r in reasons_list[:3])
                                if reasons_list
                                else "no reason recorded"
                            )
                            conviction_val = (
                                getattr(brain, "score", 0) if brain else 0
                            )
                            self.market_memory.repository.save_decision(
                                symbol=symbol,
                                action="REJECT",
                                reason=reason_text,
                                conviction=conviction_val or 0,
                                evidence=reason_text,
                            )
                        except Exception as e:
                            print(f"[DECISION LOG] reject-save failed: {e}")

                        return

                    # Validate macro structural layout risk constraints

                    if brain is None:
                        print(f"❌ No Brain decision available for {symbol}")
                        return

                    # Event entries carry a HIGHER
                    # conviction bar than ORB entries.
                    if entry_mode == "EVENT":
                        from config import (
                            EVENT_ENTRY_MIN_CONVICTION,
                        )
                        conviction_now = getattr(
                            brain.opportunity,
                            "conviction", 0
                        )
                        if (
                            conviction_now
                            < EVENT_ENTRY_MIN_CONVICTION
                        ):
                            print(
                                f"❌ EVENT ENTRY BAR: "
                                f"{symbol} conviction "
                                f"{conviction_now:.1f} < "
                                f"{EVENT_ENTRY_MIN_CONVICTION}"
                            )
                            return

                    portfolio_decision = self.portfolio_risk_manager.can_take_trade(
                        opportunity=brain.opportunity
                        )

                    self.decision_audit.record_portfolio_decision(
                        security_id=security_id,
                        portfolio_decision=portfolio_decision
                    )

                    # --------------------------------------------------
                    # POSITION REPLACEMENT : a stronger
                    # candidate evicts the weakest open
                    # position (book full).
                    # --------------------------------------------------
                    if (
                        portfolio_decision.allowed
                        and portfolio_decision.action == "REPLACE"
                        and portfolio_decision.replacement_candidate
                    ):
                        from config import (
                            POSITION_REPLACEMENT_ENABLED,
                        )
                        if not POSITION_REPLACEMENT_ENABLED:
                            self.monitor.increment(
                                "portfolio_rejected"
                            )
                            return

                        weakest = (
                            portfolio_decision
                            .replacement_candidate
                        )

                        for sid_w, trade_w in (
                            self.trades.items()
                        ):
                            if (
                                trade_w.get("symbol")
                                == weakest.symbol
                            ):
                                trade_w["force_exit"] = True
                                self.portfolio_risk_manager.remove_trade(
                                    weakest.symbol
                                )
                                print(
                                    f"♻️ REPLACING "
                                    f"{weakest.symbol} "
                                    f"(conviction "
                                    f"{weakest.conviction:.1f}) "
                                    f"with {symbol}"
                                )
                                self.telegram.send(
                                    f"♻️ POSITION REPLACEMENT\n\n"
                                    f"Out : {weakest.symbol} "
                                    f"(weakest, conviction "
                                    f"{weakest.conviction:.1f})\n"
                                    f"In  : {symbol} "
                                    f"({entry_mode} candidate)"
                                )
                                break

                    if not portfolio_decision.allowed:
                        self.monitor.increment("portfolio_rejected")
                        return

                    self.monitor.increment("signals")

                    # Stop: ORB structure when available,
                    # else percentage stop (event entry
                    # before the range exists).
                    if orb is not None and orb.get("low"):
                        stop_loss = orb["low"] - ORB_BUFFER
                    else:
                        from config import EVENT_ENTRY_STOP_PCT
                        stop_loss = round(
                            ltp * (1 - EVENT_ENTRY_STOP_PCT / 100),
                            2
                        )

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

                    new_conviction = getattr(
                        brain.opportunity, "conviction", 0
                    )

                    risk_allowed, risk_reason, risk_replace_id = (
                        self.risk_governor.entry_allowed(
                            trades=self.trades,
                            new_risk=new_risk,
                            sector=opportunity_sector,
                            new_conviction=new_conviction,
                        )
                    )

                    # --------------------------------------------------
                    # REAL-TIME RISK GOVERNOR REPLACEMENT (2026-07-21)
                    #
                    # Fix for "no trader sits idle" -- confirmed live
                    # that the 30s capital-allocation-cycle alone
                    # wasn't fast/reliable enough (GAIL conviction
                    # 95.4 and KARURVYSYA both expired unused while
                    # blocked by this same heat/sector cap, with the
                    # cycle's own 10-min minimum-hold window
                    # preventing a swap at the exact moments they
                    # appeared). This executes the swap immediately,
                    # at the point of rejection, same pattern as the
                    # existing PortfolioRiskManager REPLACE block
                    # above.
                    # --------------------------------------------------
                    if risk_allowed and risk_replace_id is not None:
                        weakest_trade = self.trades.get(
                            risk_replace_id
                        )

                        if weakest_trade is not None:
                            weakest_symbol = weakest_trade.get(
                                "symbol", "?"
                            )
                            weakest_conviction = weakest_trade.get(
                                "conviction", 0
                            )

                            weakest_trade["force_exit"] = True
                            self.portfolio_risk_manager.remove_trade(
                                weakest_symbol
                            )

                            print(
                                f"♻️ RISK GOVERNOR REPLACE "
                                f"{weakest_symbol} (conviction "
                                f"{weakest_conviction:.1f}) with "
                                f"{symbol} ({new_conviction:.1f}) "
                                f"— {risk_reason}"
                            )
                            self.telegram.send(
                                f"♻️ CAPITAL REALLOCATION "
                                f"(real-time)\n\n"
                                f"Out : {weakest_symbol} (weakest, "
                                f"conviction "
                                f"{weakest_conviction:.1f})\n"
                                f"In  : {symbol} (conviction "
                                f"{new_conviction:.1f})\n\n"
                                f"{risk_reason}"
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
                    new_trade["orb"] = (
                        {"high": orb["high"], "low": orb["low"]}
                        if orb is not None else {}
                    )
                    new_trade["entry_mode"] = entry_mode
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

                    # Fix (2026-07-21): dominant_* on the
                    # intelligence snapshot is only populated
                    # from EVENT facts and was empty on most
                    # trades → every log row said UNKNOWN and
                    # the sector cap / sector evidence saw
                    # nothing. Fall back to the Master DB,
                    # which always knows the sector.
                    from core.master_loader import master_loader

                    new_trade["sector"] = (
                        getattr(
                            opportunity_intelligence,
                            "dominant_sector", ""
                        )
                        or master_loader.get_sector(symbol)
                        or ""
                    )

                    new_trade["industry"] = (
                        getattr(
                            opportunity_intelligence,
                            "dominant_industry", ""
                        )
                        or master_loader.get_industry(symbol)
                        or ""
                    )

                    _themes = master_loader.get_themes(symbol)
                    new_trade["theme"] = (
                        getattr(
                            opportunity_intelligence,
                            "dominant_theme", ""
                        )
                        or (_themes[0] if _themes else "")
                        or ""
                    )

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
                    self._entered_today.add(symbol)
                    self.position_recovery.save(self.trades)

                    # --------------------------------------------------
                    # ADDITIVE ATM OPTION LEG (1 lot, nearest monthly)
                    #
                    # Buys the ATM CALL alongside the equity position on the
                    # same breakout. Fully self-contained and exception-safe:
                    # a failure here can never affect the equity trade above.
                    # --------------------------------------------------
                    self.option_leg.try_enter(
                        symbol=symbol,
                        direction="CE",           # long breakout -> ATM CALL
                        underlying_ltp=ltp,
                        entry_time=ltt,
                        parent_security_id=security_id,
                    )

                    # Permanent decision memory: WHY we entered
                    try:
                        reasons = getattr(
                            brain, "reasons", []
                        ) or []
                        self.market_memory.repository.save_decision(
                            symbol=symbol,
                            action=f"ENTRY_{entry_mode}",
                            reason=" | ".join(
                                str(r) for r in reasons[:6]
                            ),
                            sector=new_trade.get("sector", ""),
                            conviction=new_trade.get(
                                "conviction", 0
                            ),
                            evidence=" | ".join(
                                str(r) for r in reasons
                            ),
                        )
                    except Exception as dec_err:
                        print(f"[DECISION] {dec_err}")

            # ---------------------------------
            # POSITION EXIT PIPELINE
            # ---------------------------------
            else:
                if trade.get("force_exit"):
                    # Position replacement / shock eviction
                    result = self.EXIT_SYSTEM
                elif self.trade_controller.is_exit_all_requested():
                    result = self.EXIT_MANUAL
                elif self.trade_controller.is_exit_requested(
                    security_id
                ):
                    # Per-position manual Sell (dashboard button,
                    # 2026-07-21) -- same EXIT_MANUAL reason as
                    # exit-all, just scoped to this one position.
                    result = self.EXIT_MANUAL
                    self.trade_controller.clear_exit_requested(
                        security_id
                    )
                else:
                    result = self.risk_manager.update(trade, ltp, ltt)

                # --------------------------------------------------
                # Dynamic Trade Management
                # (partial booking / trail ratchet / catalyst exit)
                # --------------------------------------------------
                if result == "ACTIVE":
                    # HOLD BRAIN: exit when the reason to
                    # own has decayed (withdraw on
                    # deterioration) — before the stop.
                    try:
                        thesis = self.position_thesis.advise(
                            symbol, trade, ltp
                        )
                        if thesis["action"] == "THESIS_EXIT":
                            print(
                                f"🧠 THESIS EXIT : {symbol} — "
                                f"{thesis['reason']}"
                            )
                            trade["thesis_exit_reason"] = (
                                thesis["reason"]
                            )
                            result = self.EXIT_SYSTEM
                    except Exception as thesis_err:
                        print(f"[THESIS] {thesis_err}")

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

                        # Permanent decision memory: WHY exit
                        self.market_memory.repository.save_decision(
                            symbol=symbol,
                            action=f"EXIT_{result}",
                            reason=(
                                f"Exit {result} @ {ltp:.2f} "
                                f"(entry {trade.get('entry', 0):.2f}, "
                                f"held {trade.get('entry_time', '')}"
                                f"→{ltt})"
                            ),
                            sector=trade.get("sector", ""),
                            conviction=trade.get("conviction", 0),
                            pnl=round(pnl, 2),
                        )

                    except Exception as memory_error:
                        # Memory failures must never block exits
                        print(f"[MEMORY] Recording failed: {memory_error}")

                    self.position_manager.close_position(security_id, pnl)
                    self.open_position_manager.remove(security_id)
                    del self.trades[security_id]

                    # ADDITIVE: close the linked ATM option leg with the equity
                    self.option_leg.exit_for_parent(security_id, reason=result)
                    
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

    def _check_news_staleness(self, now):
        from config import NEWS_STALENESS_MINUTES

        if not ("09:20" <= now.strftime("%H:%M") <= "15:30"):
            return

        last = self.trade_selection_engine.last_story_time

        reference = last or getattr(
            self, "_session_start", None
        )
        if reference is None:
            self._session_start = now
            return

        silent_minutes = (
            now - reference
        ).total_seconds() / 60

        if silent_minutes < NEWS_STALENESS_MINUTES:
            return

        if getattr(self, "_staleness_alerted", False):
            return
        self._staleness_alerted = True

        self.telegram.send(
            f"📡 NEWS FEED ALERT\n\n"
            f"No stories received from Railway for "
            f"{silent_minutes:.0f} minutes during market "
            f"hours.\n\n"
            f"The bot is trading on price evidence only "
            f"(no news/event/causal input).\n\n"
            f"Check:\n"
            f"1. Railway service logs (is it running?)\n"
            f"2. DATABASE_URL matches between Railway "
            f"and this bot's .env\n"
            f"3. /news for pipeline counters"
        )

    # --------------------------------------------------

    def news_pipeline_report(self):
        """
        The full Railway → Brain chain, visible.
        """
        ts = self.trade_selection_engine

        last = (
            ts.last_story_time.strftime("%H:%M:%S")
            if ts.last_story_time else "NONE this session"
        )

        # Stories in Postgres today (best effort)
        db_today = "n/a"
        try:
            with self.market_memory.repository._lock:
                pass  # local memory is separate; postgres below
            cursor = (
                self.trade_selection_engine
                .brain.intelligence_repository.cursor
            )
            cursor.execute(
                "SELECT COUNT(*) FROM market_stories "
                "WHERE created_at >= %s",
                (datetime.now().strftime("%Y-%m-%d"),),
            )
            db_today = cursor.fetchone()[0]
        except Exception:
            pass

        chains = len(self.causal_engine.active_chains)
        watchlist = len(
            self.fno_opportunity_engine.get_watchlist()
        )

        return (
            "NEWS PIPELINE (Railway → Brain)\n\n"
            f"1. Stories in DB today   : {db_today}\n"
            f"2. Stories → Brain       : "
            f"{ts.stories_received} (this session)\n"
            f"3. Last story received   : {last}\n"
            f"4. Structured events     : "
            f"{self.event_intelligence.events_created}\n"
            f"5. F&O catalyst watchlist: {watchlist}\n"
            f"6. Active causal chains  : {chains}\n\n"
            "Healthy = all numbers grow through the day.\n"
            "Stories stuck at 0 → check Railway logs +\n"
            "DATABASE_URL match (Railway vs bot .env)."
        )

    # --------------------------------------------------

    def _event_entry_candidate(self, symbol, security_id, ltt):
        """
        Rule-001: the Brain may enter on a MASSIVE fresh
        catalyst without waiting for an ORB breakout —
        any time from open until the global 15:14 cutoff.

        Returns the watchlist entry or None.
        """
        from config import (
            EVENT_ENTRY_ENABLED,
            EVENT_ENTRY_MIN_IMPORTANCE,
            EVENT_ENTRY_FRESH_MINUTES,
            ENTRY_CUTOFF_TIME,
        )

        if not EVENT_ENTRY_ENABLED:
            return None

        # Global hard cutoff (MIS)
        if ltt >= ENTRY_CUTOFF_TIME + ":00":
            return None

        if ltt < "09:16:00":
            return None

        if symbol in self._entered_today:
            return None

        if security_id in self.trades:
            return None

        entry = self.fno_opportunity_engine.watchlist.get(
            symbol
        )

        if entry is None:
            return None

        if entry["importance"] < EVENT_ENTRY_MIN_IMPORTANCE:
            return None

        direction = str(
            entry.get("direction", "")
        ).upper()
        if direction in (
            "WEAKENING", "CONTRADICTED", "NEGATIVE"
        ):
            return None

        age_minutes = (
            datetime.now() - entry["added_at"]
        ).total_seconds() / 60

        if age_minutes > EVENT_ENTRY_FRESH_MINUTES:
            return None

        # Buy-the-rumor guard: never chase an event
        # entry on a stock that already ran before
        # its news arrived.
        from config import PRICED_IN_FADE_PCT
        prior_move = entry.get("prior_move")
        if (
            prior_move is not None
            and prior_move >= PRICED_IN_FADE_PCT
        ):
            return None

        return entry

    # --------------------------------------------------

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
        Institutional Capital Allocation Pipeline.

        Checks whether the best-ranked opportunity still waiting
        in the pool is meaningfully better (15+ conviction
        points, per PortfolioIntelligenceEngine's
        replacement_threshold) than the weakest currently open
        position -- and that weakest position has been held past
        the minimum hold time (10 min, prevents thrashing a
        freshly-opened trade). If so, swap it out.

        This is the fix for "don't sit idle when a better
        opportunity appears": RiskGovernor's heat/sector caps
        decide whether a NEW entry is safe; this cycle decides
        whether an EXISTING position should make room for a
        better one, independent of whether a cap is full.
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

        # --------------------------------------------------
        #  2. Ask Portfolio Intelligence: keep or replace?
        # --------------------------------------------------

        portfolio = TradesPortfolioView(self.trades)

        recommendation = self.portfolio_intelligence_engine.evaluate(
            portfolio=portfolio,
            ranked_opportunities=opportunities,
        )

        if recommendation.action != "REPLACE":
            return

        # --------------------------------------------------
        #  3. Execute the replacement
        # --------------------------------------------------

        for sid, trade in self.trades.items():
            if trade.get("symbol") == recommendation.weakest_symbol:
                trade["force_exit"] = True

                print(
                    f"\n♻️ ALLOCATION CYCLE REPLACE\n"
                    f"Out : {recommendation.weakest_symbol} "
                    f"(conviction "
                    f"{recommendation.weakest_conviction:.1f})\n"
                    f"In  : {recommendation.candidate_symbol} "
                    f"(conviction "
                    f"{recommendation.candidate_conviction:.1f})\n"
                )

                self.telegram.send(
                    f"♻️ CAPITAL REALLOCATION\n\n"
                    f"Out : {recommendation.weakest_symbol} "
                    f"(weakest, conviction "
                    f"{recommendation.weakest_conviction:.1f})\n"
                    f"In  : {recommendation.candidate_symbol} "
                    f"(waiting in pool, conviction "
                    f"{recommendation.candidate_conviction:.1f})\n\n"
                    f"{recommendation.reason}"
                )
                break


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

    def premarket_brief(self):
        """
        THE pre-market intelligence brief.

        Combines today's known context with everything
        the bot has LEARNED across all prior days:
          • results-day watchlist (block + hunt)
          • active causal chains (news → expected effect)
          • reaction-decay expectations per event type
          • recent event outcomes (how the market actually
            reacted last time)

        This is the "these news are around the market →
        market may react this way" report that grows
        sharper every trading day.
        """
        from datetime import datetime as _dt

        lines = [
            "🌅 PRE-MARKET INTELLIGENCE BRIEF",
            _dt.now().strftime("%a %d %b %Y %H:%M"),
            "",
        ]

        # 1. Risk state
        risk = self.risk_status()
        lines.append(
            f"Risk : "
            f"{'🔒 LOCKED' if risk['locked'] else '🟢 clear'} "
            f"| Regime {risk.get('regime', 'WARMUP')} "
            f"| Day loss cap ₹{risk['daily_max_loss']:,.0f}"
        )

        # 2. Latest NEWS around the market (pulled live
        #    from the news DB — this is the "these news
        #    are around" part, available even at cold
        #    start / pre-open).
        try:
            stories = (
                self.trade_selection_engine.brain
                .intelligence_repository.recent_stories(
                    limit=25
                )
            )
            # Prefer stories that map to our universe
            mapped = [
                s for s in stories
                if getattr(s, "affected_symbols", None)
            ]
            shown = mapped or stories

            if shown:
                lines.append("")
                lines.append(
                    f"📰 NEWS AROUND THE MARKET "
                    f"({len(shown)} recent):"
                )
                for s in shown[:8]:
                    syms = getattr(
                        s, "affected_symbols", []
                    ) or []
                    tag = (
                        f" → {', '.join(syms[:3])}"
                        if syms else ""
                    )
                    sector = getattr(s, "sector", "") or ""
                    lines.append(
                        f"• {getattr(s, 'name', '')[:70]}"
                        f"{tag}"
                        + (f" [{sector}]" if sector else "")
                    )
            else:
                lines.append("")
                lines.append(
                    "📰 No recent stories in the news DB. "
                    "Check /news (is the Railway service "
                    "running + DATABASE_URL matched?)."
                )
        except Exception as e:
            lines.append("")
            lines.append(
                f"📰 News DB unavailable ({str(e)[:50]}). "
                "Check /news."
            )

        # 3. Results watchlist — today, or NEXT results day
        try:
            wl = self.results_watchlist
            wl.rebuild()
            watching = sorted(
                s for s, e in wl.today.items()
                if e["state"] == "WATCHING"
            )
            if watching:
                lines.append("")
                lines.append(
                    f"📊 REPORT TODAY ({len(watching)}) — "
                    f"entries BLOCKED pre-result, hunted "
                    f"AFTER announcement:"
                )
                lines.append("  " + ", ".join(watching[:20]))
            else:
                # Show the next upcoming results day
                upcoming = self.results_calendar.upcoming(7)
                today_str = _dt.now().strftime("%Y-%m-%d")
                future = {
                    d: s for d, s in upcoming.items()
                    if d > today_str
                }
                if future:
                    nxt = sorted(future.keys())[0]
                    names = future[nxt]
                    lines.append("")
                    lines.append(
                        f"📊 No results today. Next: {nxt} "
                        f"({len(names)} stocks)"
                    )
                    lines.append("  " + ", ".join(names[:15]))
        except Exception:
            pass

        # 4. Active causal chains (news → effect)
        try:
            chains = self.causal_engine.active_chains
            if chains:
                lines.append("")
                lines.append(
                    f"🧩 CAUSAL CHAINS ACTIVE "
                    f"({len(chains)}) — how current news "
                    f"should move stocks:"
                )
                seen = set()
                for c in sorted(
                    chains, key=lambda x: -x["strength"]
                )[:6]:
                    key = c["model_key"]
                    if key in seen:
                        continue
                    seen.add(key)
                    sign = "▲" if c["sign"] > 0 else "▼"
                    lines.append(
                        f"  {sign} {c['target']} "
                        f"— {c['root_cause'][:70]}"
                    )
        except Exception:
            pass

        # 4. Reaction-decay expectations (learned)
        try:
            types = (
                self.market_memory.repository
                .known_event_types()
            )
            if types:
                lines.append("")
                lines.append(
                    "📉 LEARNED REACTIONS — how the market "
                    "NOW reacts to recurring events:"
                )
                for t in types[:6]:
                    m = self.reaction_decay.model(
                        t["event_type"]
                    )
                    if m["status"] == "INSUFFICIENT":
                        continue
                    trend = (
                        "↓ fading" if m["status"] == "DECAYING"
                        else "→ steady"
                    )
                    lines.append(
                        f"  {t['event_type']}: "
                        f"~{m['expected_magnitude']}% move "
                        f"{trend} (n={m['samples']})"
                    )
        except Exception:
            pass

        # 5. Learning depth
        try:
            counts = (
                self.market_memory.repository
                .decision_counts()
            )
            total = sum(c["count"] for c in counts)
            if total:
                lines.append("")
                lines.append(
                    f"🧠 Decision memory: {total} recorded "
                    f"actions across all sessions."
                )
        except Exception:
            pass

        # Header is 3 lines (title, date, blank) + risk.
        # If nothing else attached, memory is still cold.
        if len(lines) <= 5:
            lines.append("")
            lines.append(
                "Learned-reaction memory is still building "
                "(needs recurring graded events). The news "
                "and results sections above are live now; "
                "the historical 'market may react this way' "
                "layer sharpens over ~200 trading days."
            )

        return "\n".join(lines)

    # --------------------------------------------------

    def decay_report(self, event_type=None):
        return self.reaction_decay.report(event_type)

    # --------------------------------------------------

    def premarket_report(self):
        return self.premarket_brief()

    # --------------------------------------------------

    def watchlist_report(self):
        return self.results_watchlist.report()

    # --------------------------------------------------

    def news_watchlist_report(self):
        return self.news_watchlist.report()

    # --------------------------------------------------

    def why_report(self, symbol):
        """Every decision the bot ever made on a symbol."""
        rows = self.market_memory.repository.decisions_for_symbol(
            symbol.upper()
        )
        if not rows:
            return (
                f"DECISION HISTORY : {symbol.upper()}\n\n"
                "No recorded decisions yet."
            )

        lines = [f"DECISION HISTORY : {symbol.upper()}", ""]
        for r in rows[:15]:
            pnl = (
                f" ₹{r['pnl']}" if r["pnl"] is not None
                else ""
            )
            lines.append(
                f"{r['trade_date']} {r['time']} "
                f"[{r['action']}]{pnl}"
            )
            lines.append(f"   {r['reason'][:90]}")
        return "\n".join(lines)

    # --------------------------------------------------

    def profile_report(self):
        from config import (
            CAPITAL_PROFILE,
            CAPITAL,
            MIS_LEVERAGE,
            BUYING_POWER,
            MAX_CAPITAL_PER_TRADE,
            RISK_PER_TRADE,
            DAILY_MAX_LOSS,
            DAILY_MAX_PROFIT,
        )

        cm = self.capital_manager

        return (
            "CAPITAL PROFILE\n\n"
            f"Profile      : {CAPITAL_PROFILE}\n"
            f"Equity       : ₹{CAPITAL:,.0f}\n"
            f"Leverage     : {MIS_LEVERAGE}× (MIS)\n"
            f"Buying Power : ₹{BUYING_POWER:,.0f}\n\n"
            f"Max / trade  : ₹{MAX_CAPITAL_PER_TRADE:,.0f} "
            f"(value)\n"
            f"Risk / trade : {RISK_PER_TRADE:.0%} = "
            f"₹{CAPITAL * RISK_PER_TRADE:,.0f}\n"
            f"Day Max Loss : ₹{DAILY_MAX_LOSS:,.0f}\n"
            f"Day Max Prof : ₹{DAILY_MAX_PROFIT:,.0f}\n\n"
            f"LIVE NOW:\n"
            f"Free Margin  : ₹{cm.available():,.0f}\n"
            f"Margin Used  : ₹{cm.blocked():,.0f}\n"
            f"Exposure     : ₹{cm.exposure():,.0f}\n\n"
            f"To change: set CAPITAL_PROFILE in config.py\n"
            f"(30K 50K 1L 2L 5L 10L 20L 30L 50L 1CR) "
            f"and restart."
        )

    # --------------------------------------------------

    def market_report(self):
        state = self.market_state_engine.compute()
        self.risk_governor.set_market_state(state)

        report = self.market_state_engine.report()

        risk = self.risk_governor.status()
        report += (
            f"\n\nAdaptive Limits ({risk['regime']}):\n"
            f"Max Loss   : ₹{risk['daily_max_loss']:,.0f}\n"
            f"Max Profit : ₹{risk['daily_max_profit']:,.0f}\n"
            f"Day Peak   : ₹{risk['day_peak']:,.0f}"
        )

        shock = self.shock_responder.status()
        if shock["triggered"]:
            report += (
                f"\n\n🚨 SHOCK FIRED {shock['time']}: "
                f"{shock['reason'][:80]}"
            )

        return report

    # --------------------------------------------------

    def fetch_results_calendar(self):
        """
        Runs BOTH independent sources (BSE + NSE) and
        returns the combined count. Either one failing
        (e.g. a connection block) does not stop the other
        from populating the calendar.
        """
        bse_added = 0
        nse_added = 0
        try:
            bse_added = self.results_collector.fetch()
        except Exception as e:
            print(f"[CALENDAR] BSE collector error: {e}")
        try:
            nse_added = self.nse_results_collector.fetch()
        except Exception as e:
            print(f"[CALENDAR-NSE] NSE collector error: {e}")
        return bse_added + nse_added

    # --------------------------------------------------

    def refresh_results_calendar(self):
        """
        Purge future entries (bad/stale matches) and
        re-fetch with strict matching + dedupe, from both
        sources (BSE + NSE).
        """
        removed = self.results_calendar.clear_future()
        added = self.fetch_results_calendar()
        self.results_calendar.dedupe()
        return removed, added

    # --------------------------------------------------

    def trigger_shock(self, reason):
        self.shock_responder.trigger(reason)
        return self.shock_responder.status()

    # --------------------------------------------------

    def edge_report(self):
        from trading.edge_analyzer import EdgeAnalyzer
        return EdgeAnalyzer().report()

    # --------------------------------------------------

    def execution_report(self):
        from trading.execution_quality import ExecutionQuality
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

        # Results-day performance memory: every stock
        # that reported today gets its day move recorded
        # permanently (builds per-stock results behaviour)
        results_recorded = 0
        try:
            from datetime import datetime as _dt
            today = _dt.now().strftime("%Y-%m-%d")
            today_symbols = (
                self.results_calendar.upcoming(0)
                .get(today, [])
            )

            for sym in today_symbols:
                change = price_engine.get_change(sym)
                if change is None:
                    continue

                direction = (
                    "POSITIVE" if change > 0.5 else
                    "NEGATIVE" if change < -0.5 else
                    "NEUTRAL"
                )

                self.market_memory.repository.save_structured_event({
                    "event_type": "RESULTS_DAY",
                    "catalyst": "RESULTS",
                    "symbol": sym,
                    "direction": direction,
                    "importance": 60,
                    "confidence": 90,
                    "horizon": "SHORT",
                    "headline": (
                        f"{sym} results day: "
                        f"closed {change:+.2f}%"
                    ),
                })

                self.company_intelligence.record_event(
                    symbol=sym,
                    event_type="RESULTS_DAY",
                    headline=(
                        f"Results day close {change:+.2f}%"
                    ),
                    source="CALENDAR",
                    payload={"day_change": change},
                )
                results_recorded += 1
        except Exception as results_error:
            print(f"[EOD] Results memory: {results_error}")

        if results_recorded:
            lines.append(
                f"Results-day performance recorded: "
                f"{results_recorded} stock(s)."
            )

        # Event outcome write-back: grade today's
        # structured events with realized day moves AND
        # market-adjusted ABNORMAL moves (the true event
        # impact) — this feeds both predictive memory and
        # the reaction-decay model.
        market_avg = None
        try:
            state = self.market_state_engine.compute()
            market_avg = state.get("avg_change")
        except Exception:
            pass

        graded = self.event_intelligence.write_outcomes(
            price_engine.get_change,
            market_change=market_avg
        )
        lines.append(
            f"Event outcomes graded: {graded} "
            f"(market-adjusted, mkt {market_avg}%)."
        )

        # Show any event types whose shock is now decaying
        try:
            decaying = []
            for t in (
                self.market_memory.repository
                .known_event_types()
            ):
                m = self.reaction_decay.model(
                    t["event_type"]
                )
                if m["status"] == "DECAYING":
                    decaying.append(
                        f"{m['event_type']} ×{m['multiplier']}"
                    )
            if decaying:
                lines.append(
                    "Shock decay detected: "
                    + ", ".join(decaying[:5])
                )
        except Exception:
            pass

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