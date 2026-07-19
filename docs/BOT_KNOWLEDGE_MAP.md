# BOT KNOWLEDGE MAP

Version 2.6 · The complete "what runs what, and what you get back"

---

# 1. IS EVERYTHING CONNECTED? — YES. Here is the exact Monday flow.

## The news question, answered honestly

**Q: If news or results are published, does the bot know and start buying?**

**A: It KNOWS immediately. It does NOT buy on news alone — by your own design.**

The flow when news breaks (say "L&T wins ₹5,000 crore order" at 10:20):

```
Railway service (24/7)                      Main bot (py main.py)
──────────────────────                      ─────────────────────
RSS / BSE / SEBI / RBI / PIB collectors
        ↓
classify + match symbols (L&T)
        ↓
Market Story → Postgres  ─────────────────→ Brain.update_intelligence()
                                                    ↓
                                            Event Intelligence:
                                            structured event (type=ORDER_WIN,
                                            importance, direction) → permanent
                                            per-stock memory
                                                    ↓
                                     ┌──────────────┼──────────────────┐
                                     ↓              ↓                  ↓
                              F&O watchlist   Causal chains      Graph spillover
                              (L&T = live     (capital goods+,   (LTTS, LTIM,
                              catalyst)       infra theme+)      suppliers+)
                                                    ↓
                              ALL of this becomes EVIDENCE, waiting.
                                                    ↓
                    WHEN L&T (or a connected stock) BREAKS OUT of its ORB:
                    evidence floods in → conviction ↑ → Brain gate →
                    Risk Governor → PAPER BUY
```

So: **news arms the system; price confirmation pulls the trigger.** A stock with a live catalyst that then breaks out gets dramatically higher conviction than a naked breakout. This is your Constitution: *"Evidence contributes; Conviction decides; Risk authorizes; Execution acts"* — ORB is the execution trigger, per Rule-001.

**Results special case:** a stock whose results are due TODAY (calendar knows via harvester//calendar/CSV) is **hard-blocked** from new entries — "no new risk into binary events." A results *surprise* on a stock NOT in the calendar flows through as a normal catalyst.

**What would make it buy news directly** (not built yet, intentionally): an "immediate institutional entry" execution strategy for exceptional catalysts — your Rule-001 override. The `execution_strategy_selector` stub exists for exactly this.

## The 9 evidence sources feeding every decision

| # | Provider | Source | Says |
|---|---|---|---|
| 1 | sector/industry/theme/RS | live ticks | "Is the group strong right now?" |
| 2 | MARKET_STORY | Railway news | "Is there a narrative?" |
| 3 | EVENT | event memory | "What happened to this stock + how did similar events resolve historically?" |
| 4 | FNO_CATALYST | F&O watchlist | "Live catalyst on this F&O name" |
| 5 | CAUSAL | causal models | "Rate cut → NBFC chain active (+80, O1)" |
| 6 | SYMPATHY | knowledge graph | "BEL's order spills to its supplier" |
| 7 | PATTERN | own history | "Failed 2 ORBs today — avoid" |
| 8 | COMPANY | own history | "We win 65% on this stock" |
| 9 | EVENT_RISK | results calendar | "Results today — block" |

All nine → Conviction (Strength × Agreement × Confidence) → Brain gate (quality + confidence + conviction ≥ 55 + non-bearish) → Portfolio admission → **Risk Governor veto** (daily loss / streak / heat / sector caps) → execution → Dynamic Manager (partials at 1R, trail after 1.5R, catalyst exits) → exit → **everything remembered** (ORB outcome, trade, company event, calibration, event grading at /eod).

---

# 2. WHAT TO RUN IN VS CODE → WHAT YOU GET

| Command | What happens | When |
|---|---|---|
| `py main.py` | **THE BOT.** Coherence audit prints → 750 profiles seed → graph seeds → F&O watchlist rebuilds → Telegram thread starts → Dhan feed connects → trades paper all day → Telegram alerts | Every market morning |
| `py dashboard.py` | **THE WEBSITE** → http://localhost:8181 — live PnL curve, open positions, trade log, PnL-by-hour (your 11 AM question), conviction-vs-PnL quality scatter. Auto-refreshes 5s | Alongside the bot |
| `py run_all_tests.py` | Full suite: 113 unit checks + component tests + 23-check smoke test → `6/6 ALL TESTS PASSED` | Before any live day / after changes |
| `py tools/smoke_test.py` | Full trading day simulated offline (ORB→breakout→buy→exit→memory), isolated from real data | Quick health check |
| `py trading/edge_analyzer.py` | The verdict: net expectancy after charges + hour/sector/conviction breakdowns | Weekly |
| `py railway_main.py` | The 24/7 news service (normally on Railway, not your PC) | Only if running news locally |
| `py trading/charges_calculator.py` | Today's charges + net PnL | EOD |
| `py tools/health_check.py`, `tools/show_positions.py` | Ops utilities | As needed |

**Telegram (24 commands):** monitoring `/status /capital /mtm /positions /health`, intelligence `/brief /fno /causal /events /memory /company /graph /pool /sectors /calendar`, learning `/edge /calibration /execution /journal /eod /risk`, control `/pause /resume /tradingoff /tradingon /exitall`.

**Daily routine:** `py run_all_tests.py` → `py main.py` → `py dashboard.py` (second terminal) → manage via Telegram → `/eod` at close.

---

# 3. THE FOLDER MAP (post-reorganization)

```
orb-auto-trader/
├── main.py                ← START THE BOT
├── dashboard.py           ← START THE WEBSITE
├── run_all_tests.py       ← RUN ALL TESTS
├── market_data.py         (feed loop; main.py's engine room)
├── config.py              (every knob: risk, ORB, conviction, dynamic mgmt)
├── railway_main.py        (24/7 news service entry — deployed on Railway)
├── railway_news_engine.py
│
├── core/                  engine, ORB, candles, strategy, master loader,
│                          recorder, monitor, watchdog, decision audit
├── intelligence/          brain, conviction, evidence, sector/industry/theme/RS,
│                          pattern, company, event, causal knowledge+reasoning,
│                          knowledge graph, F&O engine, calendar, memory
├── news/                  news engine, classifier, models, taxonomy, stories,
│                          impact, symbol matcher
├── trading/               execution (paper/live/quality), risk manager+governor,
│                          capital, positions, portfolio, trade selection,
│                          dynamic manager, edge analyzer, charges
├── notifications/         telegram (notifier, command center, reports), loggers
├── collectors/            RSS, BSE corporate, NSE, SEBI/RBI/PIB regulatory
├── repositories/          persistence (memory SQLite, intelligence Postgres)
├── tests/                 all tests (unit + component)
├── tools/                 smoke test, forensics, health, decision trace
├── Masterdata/            master_database.xlsx, graph_edges.csv,
│                          results_calendar.csv, sector data
├── data/                  universe, scrip master, replay data
├── docs/                  all specs, constitution, playbook, this map
└── (runtime files at root: trade_log_v2.csv, fills_log.csv,
     institutional_memory.db, market_recorder.db, open_positions.json —
     all gitignored)
```

---

# 4. WHAT EACH DATABASE/FILE REMEMBERS

| File | Contains | Used by |
|---|---|---|
| `institutional_memory.db` | ORB outcomes, trade outcomes, structured events (+realized moves), company events, sector days, graph edges, calendar | pattern/company/event/causal/F&O engines |
| `trade_log_v2.csv` | Every closed trade with sector/conviction/timestamps | edge analyzer, dashboard, calibration |
| `fills_log.csv` | Every order: intended vs fill price, slippage bps | /execution, TCA |
| `market_recorder.db` | Per-second PnL/positions snapshots | dashboard live curve |
| `open_positions.json` | Crash recovery state | engine startup |
| Railway Postgres | Raw news, market stories, brain decisions | Brain intelligence loading |
