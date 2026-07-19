"""
Institutional Layer Test Suite

Covers the modules added in the institutional upgrade:

    • RiskGovernor       (daily lockout, streaks, heat, sector cap)
    • ConvictionEngine   (Strength × Agreement × Confidence)
    • MemoryRepository   (persistence)
    • MarketMemory       (ORB outcomes, streaks)
    • PatternEngine      (repeated pattern evidence)
    • CompanyIntelligence(profiles, events, evidence)

Run:
    py tests/test_institutional_layer.py
"""

import os
import sys
import tempfile

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

PASSED = 0
FAILED = 0


def check(name, condition):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  ✓ {name}")
    else:
        FAILED += 1
        print(f"  ✗ {name}")


# ==========================================================
# Fakes
# ==========================================================

class FakeCapitalManager:
    def __init__(self):
        self.realized = 0.0
        self.floating = 0.0

    def pnl(self):
        return self.realized

    def floating_mtm(self):
        return self.floating


class FakeTradeController:
    def __init__(self):
        self.trading = True
        self.entries = True
        self.exit_all = False

    def disable_entries(self):
        self.entries = False

    def disable_trading(self):
        self.trading = False

    def request_exit_all(self):
        self.exit_all = True


# ==========================================================
# Risk Governor
# ==========================================================

def test_risk_governor():
    print("\nRiskGovernor")

    from trading.risk_governor import RiskGovernor
    from config import DAILY_MAX_LOSS, MAX_CONSECUTIVE_LOSSES

    capital = FakeCapitalManager()
    controller = FakeTradeController()
    governor = RiskGovernor(capital, controller, telegram=None)

    # Normal entry allowed
    allowed, reason = governor.entry_allowed({}, 0, "")
    check("entry allowed when healthy", allowed)

    # Daily loss lockout
    capital.realized = -(DAILY_MAX_LOSS + 1)
    allowed, reason = governor.entry_allowed({}, 0, "")
    check("daily loss blocks entry", not allowed)
    check("kill switch locked", governor.locked)
    check("entries disabled", not controller.entries)
    check("trading disabled", not controller.trading)
    check("exit-all requested", controller.exit_all)

    # Lock is permanent for the session
    capital.realized = 0
    allowed, reason = governor.entry_allowed({}, 0, "")
    check("lock is permanent", not allowed)

    # Consecutive losses
    capital2 = FakeCapitalManager()
    controller2 = FakeTradeController()
    governor2 = RiskGovernor(capital2, controller2, telegram=None)

    for _ in range(MAX_CONSECUTIVE_LOSSES):
        governor2.on_trade_closed(-100)

    allowed, reason = governor2.entry_allowed({}, 0, "")
    check("loss streak blocks entry", not allowed)

    # Winner resets streak
    governor3 = RiskGovernor(
        FakeCapitalManager(), FakeTradeController(), None
    )
    governor3.on_trade_closed(-100)
    governor3.on_trade_closed(500)
    check("winner resets streak", governor3.consecutive_losses == 0)

    # Portfolio heat
    from config import MAX_PORTFOLIO_HEAT
    governor4 = RiskGovernor(
        FakeCapitalManager(), FakeTradeController(), None
    )
    trades = {
        "1": {"entry": 100, "stop_loss": 90, "qty": 100,
              "sector": "IT"},
    }
    heat = governor4.portfolio_heat(trades)
    check("heat computed", heat == 1000.0)

    allowed, reason = governor4.entry_allowed(
        trades, MAX_PORTFOLIO_HEAT, ""
    )
    check("heat cap blocks entry", not allowed)

    # Sector cap
    from config import MAX_POSITIONS_PER_SECTOR
    trades5 = {
        str(i): {"entry": 100, "stop_loss": 99, "qty": 1,
                 "sector": "BANKING"}
        for i in range(MAX_POSITIONS_PER_SECTOR)
    }
    governor5 = RiskGovernor(
        FakeCapitalManager(), FakeTradeController(), None
    )
    allowed, reason = governor5.entry_allowed(
        trades5, 0, "BANKING"
    )
    check("sector cap blocks entry", not allowed)

    allowed, reason = governor5.entry_allowed(trades5, 0, "IT")
    check("other sector still allowed", allowed)


# ==========================================================
# Conviction Engine
# ==========================================================

def test_conviction_engine():
    print("\nConvictionEngine")

    from intelligence.conviction_engine import ConvictionEngine
    from intelligence.evidence import Evidence

    engine = ConvictionEngine()

    def make(provider, rec, score, confidence=90):
        return Evidence(
            provider=provider,
            recommendation=rec,
            score=score,
            confidence=confidence,
        )

    # Aligned bullish evidence
    aligned = [
        make("sector", "STRONG", 80),
        make("industry", "STRONG", 75),
        make("relative_strength", "LEADER", 85),
        make("theme", "STRONG", 70),
    ]

    snapshot = engine.evaluate(aligned)
    check("score computed", snapshot["score"] is not None)
    check("ready for scoring", snapshot["ready_for_scoring"])
    check("bullish alignment", snapshot["alignment"] == "BULLISH")
    check("high score when aligned", snapshot["score"] > 55)
    check("grade assigned", snapshot["grade"] in ("A+", "A", "B", "C"))

    # Conflict reduces conviction
    conflicted = aligned[:3] + [make("theme", "WEAK", 70)]
    conflict_snapshot = engine.evaluate(conflicted)
    check(
        "conflict reduces score",
        conflict_snapshot["score"] < snapshot["score"]
    )
    check("conflict recorded", len(conflict_snapshot["conflicts"]) > 0)

    # Missing required providers reduce confidence
    partial = aligned[:2]
    partial_snapshot = engine.evaluate(partial)
    check(
        "missing required detected",
        len(partial_snapshot["missing_required"]) == 2
    )
    check(
        "not ready for scoring",
        not partial_snapshot["ready_for_scoring"]
    )
    check(
        "incompleteness reduces confidence",
        partial_snapshot["confidence"] < snapshot["confidence"]
    )

    # Empty evidence
    empty_snapshot = engine.evaluate([])
    check("empty evidence handled", empty_snapshot["score"] == 0.0)


# ==========================================================
# Memory Repository + Market Memory
# ==========================================================

def test_memory():
    print("\nMemoryRepository + MarketMemory")

    from repositories.memory_repository import MemoryRepository
    from intelligence.market_memory import MarketMemory

    db_file = os.path.join(
        tempfile.gettempdir(), "test_inst_memory.db"
    )
    if os.path.exists(db_file):
        os.remove(db_file)

    repo = MemoryRepository(db_file)
    memory = MarketMemory(repository=repo)

    # ORB outcomes
    memory.record_orb_outcome("TESTSTOCK", "IT", "FAILED", -500)
    memory.record_orb_outcome("TESTSTOCK", "IT", "FAILED", -300)
    memory.record_orb_outcome("TESTSTOCK", "IT", "SUCCESS", 900)

    check(
        "orb failures today counted",
        memory.orb_failures_today("TESTSTOCK") == 2
    )

    stats = memory.orb_stats("TESTSTOCK")
    check("orb samples", stats["samples"] == 3)
    check("orb win rate", stats["win_rate"] == 33.3)

    # Trade outcomes
    memory.record_trade_outcome({
        "symbol": "TESTSTOCK",
        "sector": "IT",
        "exit_reason": "TARGET",
        "pnl": 900,
    })
    trade_stats = memory.symbol_trade_stats("TESTSTOCK")
    check("trade recorded", trade_stats["trades"] == 1)

    # Sector leadership streak
    memory.record_sector_day("IT", 1, 80)
    check(
        "sector streak works",
        memory.sector_leadership_streak("IT") == 1
    )
    memory.record_sector_day("PHARMA", 9, 10)
    check(
        "weak sector no streak",
        memory.sector_leadership_streak("PHARMA") == 0
    )

    # Persistence across instances
    repo2 = MemoryRepository(db_file)
    memory2 = MarketMemory(repository=repo2)
    check(
        "memory survives restart",
        memory2.orb_stats("TESTSTOCK")["samples"] == 3
    )

    repo.close()
    repo2.close()


# ==========================================================
# Pattern Engine
# ==========================================================

def test_pattern_engine():
    print("\nPatternEngine")

    from repositories.memory_repository import MemoryRepository
    from intelligence.market_memory import MarketMemory
    from intelligence.pattern_engine import PatternEngine
    from config import MAX_ORB_FAILURES_PER_DAY

    db_file = os.path.join(
        tempfile.gettempdir(), "test_inst_pattern.db"
    )
    if os.path.exists(db_file):
        os.remove(db_file)

    memory = MarketMemory(
        repository=MemoryRepository(db_file)
    )
    patterns = PatternEngine(memory)

    # No history → no evidence
    check(
        "no evidence without history",
        patterns.build_evidence("CLEANSTOCK") == []
    )

    # Repeated failures today → AVOID evidence
    for _ in range(MAX_ORB_FAILURES_PER_DAY):
        memory.record_orb_outcome(
            "FAILSTOCK", "AUTO", "FAILED", -200
        )

    evidence = patterns.build_evidence("FAILSTOCK")
    check("failure pattern detected", len(evidence) >= 1)
    check(
        "failure pattern says AVOID",
        any(e.recommendation == "AVOID" for e in evidence)
    )

    # Sector streak → BUY evidence
    for _ in range(1):
        memory.record_sector_day("DEFENCE", 1, 90)

    # only 1 day → no streak evidence yet (needs 3)
    evidence2 = patterns.build_evidence("HAL", "DEFENCE")
    streak_evidence = [
        e for e in evidence2
        if e.facts.get("pattern") == "SECTOR_LEADERSHIP_STREAK"
    ]
    check("1-day streak not enough", len(streak_evidence) == 0)

    # Report is printable
    report = patterns.report("FAILSTOCK", "AUTO")
    check("report generated", "FAILSTOCK" in report)


# ==========================================================
# Company Intelligence
# ==========================================================

def test_company_intelligence():
    print("\nCompanyIntelligence")

    from repositories.memory_repository import MemoryRepository
    from intelligence.company_intelligence import CompanyIntelligence

    db_file = os.path.join(
        tempfile.gettempdir(), "test_inst_company.db"
    )
    if os.path.exists(db_file):
        os.remove(db_file)

    company = CompanyIntelligence(
        repository=MemoryRepository(db_file)
    )

    # Profile access (works even without master data)
    profile = company.get_profile("TESTCO")
    check("profile created", profile["symbol"] == "TESTCO")
    check(
        "future containers exist",
        "promoters" in profile and "plants" in profile
    )

    # Event recording
    company.record_event(
        "TESTCO", "ORDER_WIN",
        headline="TESTCO wins ₹500 crore order",
        source="TEST"
    )
    company.record_trade("TESTCO", "TARGET", 1500.0)

    full = company.get_full_profile("TESTCO")
    check(
        "events recorded",
        len(full.get("recent_events", [])) == 2
    )

    # Evidence requires >= 5 trades
    check(
        "no evidence below 5 trades",
        company.build_evidence("TESTCO") == []
    )

    for i in range(5):
        company.repository.save_trade_outcome({
            "symbol": "WINSTOCK",
            "pnl": 100,
            "exit_reason": "TARGET",
        })

    evidence = company.build_evidence("WINSTOCK")
    check("evidence after 5 trades", len(evidence) == 1)
    check(
        "positive history says BUY",
        evidence[0].recommendation == "BUY"
    )

    # Report
    report = company.report("TESTCO")
    check("dossier generated", "TESTCO" in report)


# ==========================================================
# Event Intelligence + F&O Opportunity Engine
# ==========================================================

class FakeStory:
    def __init__(self, **kwargs):
        self.story_id = kwargs.get("story_id", "S1")
        self.name = kwargs.get(
            "name", "TESTCO wins large defence order"
        )
        self.catalyst = kwargs.get("catalyst", "ORDER_WIN")
        self.category = "Corporate"
        self.subcategory = "Order"
        self.event_type = kwargs.get("event_type", "ORDER_WIN")
        self.sector = kwargs.get("sector", "DEFENCE")
        self.industry = "Defence Electronics"
        self.theme = "DEFENCE"
        self.confidence = kwargs.get("confidence", 80.0)
        self.story_strength = 70.0
        self.story_direction = kwargs.get(
            "direction", "STRENGTHENING"
        )
        self.priority = kwargs.get("priority", 90)
        self.lifecycle = "STRONG"
        self.expected_duration = kwargs.get(
            "horizon", "INTRADAY"
        )
        self.affected_symbols = kwargs.get(
            "symbols", ["FNOSTOCK"]
        )


def test_event_and_fno():
    print("\nEventIntelligence + FnOOpportunityEngine")

    from repositories.memory_repository import MemoryRepository
    from intelligence.event_intelligence import EventIntelligence
    from intelligence.fno_opportunity_engine import FnOOpportunityEngine
    from intelligence.company_intelligence import CompanyIntelligence

    db_file = os.path.join(
        tempfile.gettempdir(), "test_inst_events.db"
    )
    if os.path.exists(db_file):
        os.remove(db_file)

    repo = MemoryRepository(db_file)
    company = CompanyIntelligence(repository=repo)

    # Mark FNOSTOCK as an F&O name
    company.get_profile("FNOSTOCK")["fno"] = "YES"
    company.get_profile("CASHSTOCK")["fno"] = ""

    events_engine = EventIntelligence(
        repository=repo,
        company_intelligence=company
    )
    fno = FnOOpportunityEngine(
        company_intelligence=company,
        repository=repo
    )

    # Process a story
    story = FakeStory()
    events = events_engine.process_story(story)

    check("events created", len(events) == 1)
    check(
        "event persisted per symbol",
        len(repo.symbol_structured_events("FNOSTOCK")) == 1
    )

    # Living profile evolved
    profile = company.get_profile("FNOSTOCK")
    check(
        "living profile updated",
        profile["catalyst_count"] == 1
        and profile["last_event_type"] == "ORDER_WIN"
    )

    # Duplicate story ignored
    events2 = events_engine.process_story(story)
    check("duplicate story ignored", events2 == [])

    # F&O watchlist
    for event in events:
        fno.ingest_event(event)

    watchlist = fno.get_watchlist()
    check("fno watchlist populated", len(watchlist) == 1)

    # Non-F&O symbol rejected
    story_cash = FakeStory(
        story_id="S2", symbols=["CASHSTOCK"]
    )
    for event in events_engine.process_story(story_cash):
        added = fno.ingest_event(event)
    check("non-F&O symbol rejected", "CASHSTOCK" not in fno.watchlist)

    # Low-importance rejected
    story_weak = FakeStory(
        story_id="S3", symbols=["FNOSTOCK2"],
        priority=20, confidence=30
    )
    company.get_profile("FNOSTOCK2")["fno"] = "YES"
    for event in events_engine.process_story(story_weak):
        fno.ingest_event(event)
    check(
        "weak catalyst rejected",
        "FNOSTOCK2" not in fno.watchlist
    )

    # Evidence generation
    event_evidence = events_engine.build_evidence("FNOSTOCK")
    check("event evidence built", len(event_evidence) >= 1)
    check(
        "event evidence bullish",
        event_evidence[0].recommendation == "BUY"
    )

    fno_evidence = fno.build_evidence("FNOSTOCK")
    check("fno evidence built", len(fno_evidence) == 1)
    check(
        "fno provider correct",
        fno_evidence[0].provider == "FNO_CATALYST"
    )

    # Watchlist rebuild from memory (restart survival)
    fno2 = FnOOpportunityEngine(
        company_intelligence=company,
        repository=repo
    )
    check(
        "watchlist survives restart",
        "FNOSTOCK" in fno2.watchlist
    )

    # Reports
    check(
        "events report",
        "FNOSTOCK" in events_engine.report("FNOSTOCK")
    )
    check("fno report", "FNOSTOCK" in fno.report())

    # Calibration report structure
    repo.save_trade_outcome(
        {"symbol": "X", "conviction": 75, "pnl": 500}
    )
    repo.save_trade_outcome(
        {"symbol": "Y", "conviction": 45, "pnl": -300}
    )
    calibration = repo.calibration_report()
    band_70 = next(
        b for b in calibration if b["band"] == "70-84"
    )
    check(
        "calibration bands work",
        band_70["trades"] == 1 and band_70["win_rate"] == 100.0
    )

    repo.close()


# ==========================================================
# Knowledge Graph + Results Calendar + Dynamic Manager
# ==========================================================

def test_knowledge_graph():
    print("\nKnowledgeGraph")

    from repositories.memory_repository import MemoryRepository
    from intelligence.company_intelligence import CompanyIntelligence
    from intelligence.knowledge_graph import KnowledgeGraph

    db_file = os.path.join(
        tempfile.gettempdir(), "test_inst_graph.db"
    )
    if os.path.exists(db_file):
        os.remove(db_file)

    repo = MemoryRepository(db_file)
    company = CompanyIntelligence(repository=repo)

    # Build a small synthetic universe
    for sym in ("ALPHA", "BETA", "GAMMA"):
        p = company.get_profile(sym)
        p["industry"] = "TESTIND"
        p["themes"] = ["TESTTHEME"]

    graph = KnowledgeGraph(
        company_intelligence=company,
        repository=repo
    )

    neighbors = graph.neighbors("ALPHA")
    check(
        "industry peers seeded",
        any(n["symbol"] == "BETA" for n in neighbors)
    )

    # Curated edge
    graph.add_edge(
        "ALPHA", "DELTA", "supplier_of",
        weight=0.6, persist=True
    )
    check(
        "curated edge added",
        any(
            n["symbol"] == "DELTA"
            for n in graph.neighbors("ALPHA")
        )
    )

    # Propagation: strong order win on ALPHA
    event = {
        "symbol": "ALPHA",
        "event_type": "ORDER_WIN",
        "importance": 90,
    }
    spillovers = graph.propagate(event)
    check("propagation produces spillovers", len(spillovers) > 0)

    supplier_spill = [
        s for s in spillovers if s["symbol"] == "DELTA"
    ]
    check(
        "supplier gets positive spillover",
        supplier_spill and supplier_spill[0]["impact"] > 0
    )

    # Sympathy evidence
    ev = graph.build_sympathy_evidence("DELTA", spillovers)
    check("sympathy evidence built", len(ev) == 1)
    check(
        "sympathy has path explanation",
        "ALPHA" in ev[0].reason
    )

    # Materiality floor: weak event → no spillover
    weak = graph.propagate(
        {"symbol": "ALPHA", "event_type": "ORDER_WIN",
         "importance": 10}
    )
    check("materiality floor holds", weak == [])

    repo.close()


def test_results_calendar():
    print("\nResultsCalendar")

    from repositories.memory_repository import MemoryRepository
    from intelligence.results_calendar import ResultsCalendar
    from datetime import datetime

    db_file = os.path.join(
        tempfile.gettempdir(), "test_inst_calendar.db"
    )
    if os.path.exists(db_file):
        os.remove(db_file)

    repo = MemoryRepository(db_file)
    calendar = ResultsCalendar(repository=repo)

    today = datetime.now().strftime("%Y-%m-%d")

    check("add entry", calendar.add("EVENTSTOCK", today))
    check("bad date rejected", not calendar.add("X", "18-07-2026"))
    check(
        "event today detected",
        calendar.has_event_today("EVENTSTOCK")
    )
    check(
        "no event for others",
        not calendar.has_event_today("QUIET")
    )

    evidence = calendar.build_evidence("EVENTSTOCK")
    check("event-risk evidence", len(evidence) == 1)
    check(
        "evidence says AVOID",
        evidence[0].recommendation == "AVOID"
    )

    # Persistence across restart
    calendar2 = ResultsCalendar(repository=repo)
    check(
        "calendar survives restart",
        calendar2.has_event_today("EVENTSTOCK")
    )

    check("report renders", "EVENTSTOCK" in calendar.report())

    repo.close()


def test_dynamic_trade_manager():
    print("\nDynamicTradeManager")

    from trading.dynamic_trade_manager import DynamicTradeManager
    from config import (
        PARTIAL_BOOK_AT_R,
        TRAIL_AFTER_R,
        TRAIL_DISTANCE_R,
    )

    manager = DynamicTradeManager()

    def make_trade(**overrides):
        trade = {
            "entry": 100.0,
            "risk": 10.0,
            "qty": 10,
            "stop_loss": 90.0,
            "trail_sl": 90.0,
            "highest_price": 100.0,
            "partial_done": False,
        }
        trade.update(overrides)
        return trade

    # Below 1R → hold
    advice = manager.advise("T", make_trade(), 105.0)
    check("below 1R holds", advice["action"] == "HOLD")

    # At partial-book level → partial
    trigger = 100.0 + PARTIAL_BOOK_AT_R * 10.0
    advice = manager.advise("T", make_trade(), trigger)
    check(
        "partial booked at R",
        advice["action"] == "PARTIAL_BOOK"
        and 0 < advice["qty"] < 10
    )

    # Already booked → no repeat
    advice = manager.advise(
        "T", make_trade(partial_done=True), trigger
    )
    check(
        "no repeat partial",
        advice["action"] != "PARTIAL_BOOK"
    )

    # Deep in profit → trail ratchet
    high = 100.0 + (TRAIL_AFTER_R + 0.5) * 10.0
    trade = make_trade(
        partial_done=True, highest_price=high
    )
    advice = manager.advise("T", trade, high)
    check("trail ratchets", advice["action"] == "TIGHTEN")

    expected = high - TRAIL_DISTANCE_R * 10.0
    check(
        "trail level correct",
        abs(advice["new_trail"] - expected) < 0.01
    )

    # Ratchet never widens
    trade2 = make_trade(
        partial_done=True,
        highest_price=high,
        trail_sl=expected + 5,
    )
    advice = manager.advise("T", trade2, high)
    check(
        "trail never widens",
        advice["action"] == "HOLD"
    )


# ==========================================================
# Priority Upgrades (edge, coherence, outcomes,
# harvester, execution quality)
# ==========================================================

def test_priority_upgrades():
    print("\nPriority Upgrades")

    # --- Edge Analyzer on a synthetic log ---
    from trading.edge_analyzer import EdgeAnalyzer

    log = os.path.join(
        tempfile.gettempdir(), "test_edge_log.csv"
    )
    with open(log, "w", encoding="utf-8") as f:
        f.write(
            "Date,EntryTime,Symbol,Sector,Industry,Theme,"
            "Qty,EntryPrice,ExitTime,ExitPrice,PnL,"
            "HoldingSeconds,ExitReason,Conviction,TradeID\n"
        )
        # 2 wins, 1 loss + one SMOKETEST row to exclude
        f.write(
            "2026-07-18,10:15:00,AAA,IT,X,Y,10,100,11:00:00,"
            "110,100,2700,TARGET,80,t1\n"
        )
        f.write(
            "2026-07-18,11:15:00,BBB,IT,X,Y,10,100,12:00:00,"
            "105,50,2700,TARGET,60,t2\n"
        )
        f.write(
            "2026-07-18,14:15:00,CCC,AUTO,X,Y,10,100,14:30:00,"
            "95,-50,900,STOPLOSS,30,t3\n"
        )
        f.write(
            "2026-07-18,09:33:00,DDD,SMOKETEST_SECTOR,X,Y,"
            "10,100,09:45:00,90,-100,720,STOPLOSS,50,t4\n"
        )

    analyzer = EdgeAnalyzer(log_file=log)
    result = analyzer.analyze()

    check("edge: smoketest excluded", result["trades"] == 3)
    check("edge: win rate", result["win_rate"] == 66.7)
    check(
        "edge: charges reduce expectancy",
        result["net_expectancy"] < result["gross_expectancy"]
    )
    check(
        "edge: insufficient-data verdict",
        "INSUFFICIENT" in result["verdict"]
    )
    check(
        "edge: report renders",
        "VERDICT" in analyzer.report()
    )

    # --- Risk coherence audit ---
    from trading.risk_governor import RiskGovernor

    warnings, facts = RiskGovernor.coherence_audit()
    check(
        "coherence: facts computed",
        facts["daily_max_loss"] > 0
    )
    # Current config is knowingly incoherent —
    # audit must catch it
    check(
        "coherence: catches current config",
        len(warnings) >= 1
    )

    # --- Event outcome write-back ---
    from repositories.memory_repository import MemoryRepository

    db_file = os.path.join(
        tempfile.gettempdir(), "test_outcomes.db"
    )
    if os.path.exists(db_file):
        os.remove(db_file)

    repo = MemoryRepository(db_file)

    for i in range(6):
        repo.save_structured_event({
            "event_type": "ORDER_WIN",
            "symbol": f"SYM{i}",
            "importance": 60,
        })

    graded = repo.write_event_outcomes(
        lambda symbol: 2.0  # every symbol +2% day
    )
    check("outcomes: graded all", graded == 6)

    stats = repo.event_type_reaction_stats("ORDER_WIN")
    check(
        "outcomes: reaction stats",
        stats["samples"] == 6
        and stats["avg_move"] == 2.0
        and stats["positive_rate"] == 100.0
    )

    # Expected reaction speaks only with enough samples
    from intelligence.event_intelligence import EventIntelligence
    ei = EventIntelligence(repository=repo)
    reaction = ei.expected_reaction("ORDER_WIN")
    check(
        "outcomes: expected reaction available",
        reaction is not None and reaction["avg_move"] == 2.0
    )
    check(
        "outcomes: insufficient history is honest",
        ei.expected_reaction("NEVER_SEEN") is None
    )

    # --- Calendar harvester ---
    from intelligence.calendar_harvester import CalendarHarvester
    from intelligence.results_calendar import ResultsCalendar
    from datetime import datetime, timedelta

    calendar = ResultsCalendar(repository=repo)
    harvester = CalendarHarvester(calendar)

    future = (
        datetime.now() + timedelta(days=7)
    )

    class Story:
        pass

    story = Story()
    story.name = (
        f"Board Meeting Intimation — meeting scheduled "
        f"on {future.strftime('%d %B %Y')} to consider "
        f"quarterly results"
    )
    story.affected_symbols = ["HARVESTCO"]

    added = harvester.harvest_story(story)
    check("harvester: wordy date extracted", added == 1)

    story2 = Story()
    story2.name = (
        f"XYZ Ltd board meeting on "
        f"{future.strftime('%d/%m/%Y')}"
    )
    story2.affected_symbols = ["NUMCO"]
    check(
        "harvester: numeric date extracted",
        harvester.harvest_story(story2) == 1
    )

    story3 = Story()
    story3.name = "Company wins large export order"
    story3.affected_symbols = ["NOISECO"]
    check(
        "harvester: non-meeting ignored",
        harvester.harvest_story(story3) == 0
    )

    # --- Execution quality ---
    from trading.execution_quality import ExecutionQuality

    fills = os.path.join(
        tempfile.gettempdir(), "test_fills.csv"
    )
    if os.path.exists(fills):
        os.remove(fills)

    eq = ExecutionQuality(file_name=fills)

    # BUY filled 0.5 higher than intended = adverse
    eq.record(
        "LIVE", "BUY", "AAA", 10, 100.0, 100.5,
        "o1", "FILLED"
    )
    # SELL filled lower = adverse
    eq.record(
        "LIVE", "SELL", "AAA", 10, 100.0, 99.8,
        "o2", "FILLED"
    )

    summary = eq.summary()
    check(
        "tca: fills recorded",
        summary["fills"] == 2 and summary["graded"] == 2
    )
    check(
        "tca: adverse slippage positive",
        summary["avg_slippage_bps"] > 0
    )
    check(
        "tca: rupee cost computed",
        summary["total_slippage_rupees"] == 7.0
    )

    repo.close()


# ==========================================================
# Causal Reasoning Engine
# ==========================================================

def test_causal_reasoning():
    print("\nCausalReasoningEngine")

    from repositories.memory_repository import MemoryRepository
    from intelligence.company_intelligence import CompanyIntelligence
    from intelligence.causal_reasoning_engine import CausalReasoningEngine
    from intelligence.causal_knowledge import CAUSAL_MODELS

    check(
        "knowledge base loaded (30+ models)",
        len(CAUSAL_MODELS) >= 25
    )

    # Every model is structurally valid
    valid = all(
        m.get("key") and m.get("triggers")
        and m.get("effects") and m.get("horizon")
        in ("INTRADAY", "SHORT", "MEDIUM", "LONG")
        for m in CAUSAL_MODELS
    )
    check("all models structurally valid", valid)

    db_file = os.path.join(
        tempfile.gettempdir(), "test_causal.db"
    )
    if os.path.exists(db_file):
        os.remove(db_file)

    repo = MemoryRepository(db_file)
    company = CompanyIntelligence(repository=repo)

    # Synthetic universe
    paints = company.get_profile("PAINTCO")
    paints["industry"] = "PAINTS"
    paints["sector"] = "Consumer"

    upstream = company.get_profile("OILCO")
    upstream["industry"] = "OIL EXPLORATION"
    upstream["sector"] = "Oil & Gas"

    bank = company.get_profile("BANKCO")
    bank["industry"] = "PRIVATE BANK"
    bank["sector"] = "Banking"

    engine = CausalReasoningEngine(
        company_intelligence=company,
        repository=repo
    )

    # Crude spike event
    crude_event = {
        "event_type": "COMMODITY_MOVE",
        "catalyst": "CRUDE",
        "headline": "Brent crude spike above $95 on supply fears",
        "importance": 70,
    }

    chains = engine.analyze(crude_event)
    check("crude event matched", len(chains) > 0)
    check(
        "paint chain negative",
        any(
            c["target"] == "PAINT" and c["sign"] == -1
            for c in chains
        )
    )

    # Symbol resolution
    paint_evidence = engine.build_evidence("PAINTCO")
    check("paint co gets causal evidence", len(paint_evidence) == 1)
    check(
        "paint evidence bearish",
        paint_evidence[0].recommendation == "SELL"
    )

    oil_evidence = engine.build_evidence("OILCO")
    check("upstream gets causal evidence", len(oil_evidence) == 1)
    check(
        "upstream evidence bullish",
        oil_evidence[0].recommendation == "BUY"
    )

    check(
        "unrelated symbol unaffected",
        engine.build_evidence("BANKCO") == []
    )

    # Rate cut event hits banks
    rate_event = {
        "event_type": "POLICY",
        "catalyst": "RBI",
        "headline": "RBI cuts repo rate by 25 bps, stance accommodative",
        "importance": 80,
    }
    engine.analyze(rate_event)

    bank_evidence = engine.build_evidence("BANKCO")
    check("rate cut reaches banks", len(bank_evidence) == 1)
    check(
        "bank evidence bullish",
        bank_evidence[0].recommendation == "BUY"
    )

    # Explanation contains the mechanism
    check(
        "explanation carries root cause",
        "Causal[" in bank_evidence[0].reason
    )

    # Regulatory moat compression matches
    moat_event = {
        "event_type": "REGULATORY",
        "catalyst": "CERC",
        "headline": "Regulator approves market coupling for power exchanges",
        "importance": 80,
    }
    moat_chains = engine.analyze(moat_event)
    check(
        "IEX-lesson model fires",
        any(
            c["model_key"] == "REGULATORY_MOAT_COMPRESSION"
            for c in moat_chains
        )
    )

    # Non-event doesn't fire
    noise = {
        "event_type": "OTHER",
        "catalyst": "",
        "headline": "Company announces annual general meeting",
        "importance": 30,
    }
    check("noise ignored", engine.analyze(noise) == [])

    # Reports
    check(
        "report renders",
        "CAUSAL" in engine.report()
    )
    check(
        "symbol report renders",
        "PAINTCO" in engine.report("PAINTCO")
    )

    repo.close()


# ==========================================================
# Adaptive Limits + Shock Guards + Market State
# ==========================================================

def test_adaptive_and_shock():
    print("\nAdaptive Limits + Shock Guards")

    from trading.risk_governor import RiskGovernor
    from config import (
        DAILY_MAX_LOSS,
        PEAK_GUARD_MIN_PROFIT,
        PEAK_GIVEBACK_PCT,
    )

    governor = RiskGovernor(
        FakeCapitalManager(), FakeTradeController(), None
    )

    # Regime adaptation
    governor.set_market_state({"regime": "BEARISH"})
    check(
        "bearish tightens loss limit",
        governor.daily_max_loss < DAILY_MAX_LOSS
    )

    governor.set_market_state({"regime": "TRENDING_UP"})
    check(
        "trending restores loss limit",
        governor.daily_max_loss == DAILY_MAX_LOSS
    )
    check(
        "trending expands profit room",
        governor.daily_max_profit > DAILY_MAX_LOSS
    )

    # Peak-giveback shock
    shock_fired = []
    governor2 = RiskGovernor(
        FakeCapitalManager(), FakeTradeController(), None
    )
    governor2.shock_callback = (
        lambda reason: shock_fired.append(reason)
    )

    peak = PEAK_GUARD_MIN_PROFIT + 2000
    governor2.on_tick(peak)
    check("peak tracked", governor2.day_peak_pnl == peak)

    # Small dip: no shock
    governor2.on_tick(peak * (1 - PEAK_GIVEBACK_PCT / 2))
    check("small giveback tolerated", not governor2.locked)

    # Big giveback: shock
    governor2.on_tick(peak * (1 - PEAK_GIVEBACK_PCT) - 1)
    check("giveback fires kill switch", governor2.locked)
    check("shock callback invoked", len(shock_fired) == 1)
    check(
        "reason mentions giveback",
        "GIVEBACK" in governor2.lock_reason
    )

    # Market state classification
    from intelligence.market_state_engine import (
        MarketStateEngine,
    )
    from intelligence.price_engine import price_engine

    engine = MarketStateEngine()

    # Simulate a bearish tape on real price engine
    symbols = list(price_engine.prices.keys())[:100]
    for sym in symbols:
        price_engine.prices[sym]["previous_close"] = 100.0
        price_engine.prices[sym]["ltp"] = 98.0
        price_engine.prices[sym]["change"] = -2.0

    state = engine.compute()
    check(
        "bearish tape classified",
        state["regime"] in ("BEARISH", "TRENDING_DOWN")
    )

    # Shock responder triggers on breadth collapse
    from trading.shock_responder import ShockResponder
    from intelligence.company_intelligence import (
        CompanyIntelligence,
    )

    controller = FakeTradeController()
    responder = ShockResponder(
        trade_controller=controller,
        sector_engine=None,
        company_intelligence=CompanyIntelligence(
            repository=None
        ),
        telegram=None,
    )

    fired = responder.check_market(
        {"breadth_pct": 10, "avg_change": -2.5}
    )
    check("breadth collapse triggers responder", fired)
    check("responder exits all", controller.exit_all)
    check("responder disables entries", not controller.entries)

    # Only once per session
    controller.exit_all = False
    fired2 = responder.check_market(
        {"breadth_pct": 5, "avg_change": -3.0}
    )
    check("responder fires once", not fired2)

    # Reset price engine state for other tests
    for sym in symbols:
        price_engine.prices[sym]["previous_close"] = None
        price_engine.prices[sym]["change"] = 0.0


# ==========================================================
# Event-driven entry mode (selection-level)
# ==========================================================

def test_event_entry_mode():
    print("\nEvent Entry Mode")

    from trading.trade_selection_engine import (
        TradeSelectionEngine,
    )

    # EVENT mode must bypass the ORB structure gate;
    # ORB mode must still enforce it.
    engine = TradeSelectionEngine.__new__(
        TradeSelectionEngine
    )
    # Only what _score_orb path needs
    weak_orb = {"high": 100.2, "low": 100.0}

    result = TradeSelectionEngine._score_orb(
        engine, weak_orb
    )
    check("weak ORB fails structure gate", not result["passed"])

    # Strategy honors global cutoff
    from core.strategy import Strategy
    from config import ENTRY_CUTOFF_TIME

    s = Strategy()
    orb = {
        "high": 100, "low": 95,
        "completed": True, "entry_taken": False,
    }
    candle = {"close": 100.5}

    check(
        "entry allowed before cutoff",
        s.is_buy_signal(orb, "14:59:00", candle) is True
    )
    check(
        f"entry blocked after {ENTRY_CUTOFF_TIME}",
        s.is_buy_signal(
            orb, ENTRY_CUTOFF_TIME + ":01", candle
        ) is False
    )


# ==========================================================
# Priced-in detector (buy rumor / sell news)
# ==========================================================

def test_priced_in():
    print("\nPriced-In Detector")

    from repositories.memory_repository import MemoryRepository
    from intelligence.event_intelligence import EventIntelligence
    from config import (
        PRICED_IN_WARN_PCT,
        PRICED_IN_FADE_PCT,
    )

    db_file = os.path.join(
        tempfile.gettempdir(), "test_pricedin.db"
    )
    if os.path.exists(db_file):
        os.remove(db_file)

    repo = MemoryRepository(db_file)

    # price lookup: FRESHCO flat, RUNCO already +6%
    prices = {"FRESHCO": 0.5, "RUNCO": 6.0, "WARMCO": 3.5}

    ei = EventIntelligence(
        repository=repo,
        price_lookup=lambda s: prices.get(s),
    )

    story = FakeStory(
        story_id="P1",
        symbols=["FRESHCO", "RUNCO", "WARMCO"],
    )
    events = ei.process_story(story)
    check("events created for all", len(events) == 3)

    by_symbol = {e["symbol"]: e for e in events}
    check(
        "prior move captured",
        by_symbol["RUNCO"]["prior_move"] == 6.0
    )

    fresh = ei.build_evidence("FRESHCO")
    check("fresh news → BUY", fresh[0].recommendation == "BUY")

    run = ei.build_evidence("RUNCO")
    check(
        "fully priced → no BUY",
        run and run[0].recommendation == "WAIT"
    )
    check(
        "fade tagged in reason",
        "PRICED-IN" in run[0].reason
    )

    warm = ei.build_evidence("WARMCO")
    check(
        "partial priced → still BUY but haircut",
        warm[0].recommendation == "BUY"
        and warm[0].score < fresh[0].score
    )
    check(
        "haircut tagged",
        "priced-in" in warm[0].reason
    )

    repo.close()


# ==========================================================
# Brain conviction gate (integration)
# ==========================================================

def test_brain_gate():
    print("\nBrain Conviction Gate (unit-level)")

    # Verify PATTERN evidence flows into negative strength
    from intelligence.evidence import Evidence

    avoid = Evidence(
        provider="PATTERN",
        recommendation="AVOID",
        score=60,
        confidence=90,
        reason="test",
    )

    snapshot = avoid.snapshot()
    check(
        "pattern evidence snapshot ok",
        snapshot["recommendation"] == "AVOID"
        and snapshot["score"] == 60
    )


# ==========================================================

if __name__ == "__main__":
    print("=" * 60)
    print("INSTITUTIONAL LAYER TEST SUITE")
    print("=" * 60)

    test_risk_governor()
    test_conviction_engine()
    test_memory()
    test_pattern_engine()
    test_company_intelligence()
    test_event_and_fno()
    test_knowledge_graph()
    test_results_calendar()
    test_dynamic_trade_manager()
    test_priority_upgrades()
    test_causal_reasoning()
    test_adaptive_and_shock()
    test_event_entry_mode()
    test_priced_in()
    test_brain_gate()

    print()
    print("=" * 60)
    print(f"PASSED : {PASSED}")
    print(f"FAILED : {FAILED}")
    print("=" * 60)

    sys.exit(1 if FAILED else 0)
