# ORB AUTO TRADER

## Current Version

**Version:** 3.4.0-CATALYST-GATE

---

## Status

🟢 Simplified to the core ideology (2026-07-21):
**news arms the system; ORB breakout close pulls the trigger.**

### v3.4.0 changes

* **ONE entry trigger.** Removed the Momentum-Runner path
  (pre-9:30 pure-price buys — source of the random 09:16
  entries) and disabled event-driven no-ORB entries
  (`EVENT_ENTRY_ENABLED = False`). The only trigger left:
  a 1-min candle CLOSE above the ORB high, within limits.
* **CATALYST GATE (new, `config.py`).** An ORB breakout may
  only become a trade if the symbol carries live catalyst
  evidence (EVENT / FNO_CATALYST / RESULTS_LIVE / CAUSAL /
  SYMPATHY, score ≥ 25). Naked breakouts are rejected with
  reason "NO LIVE CATALYST". Whole universe still scanned.
* **Simplified risk stack.** Kept: per-trade stop, partial
  + trail, profit lock, daily max loss kill switch, max
  positions, heat cap, 15:15 flat. Disabled: thesis-decay
  exits, shock responder, peak-giveback + fast-drop guards,
  adaptive regime limits, consecutive-loss pause (=0).
* **Sector fix.** Trade rows no longer log UNKNOWN — sector/
  industry/theme now fall back to the Master Database.
* **New tool:** `py tools/news_pipeline_check.py` — run
  pre-market; verifies Railway → Postgres → symbols chain.
  If it reports BROKEN, the bot will take zero trades that
  day (catalyst gate working as designed) — fix Railway first.

### v3.4.1 (same day)

* **Continuous news ingestion.** Stories were only consumed
  inside evaluate() — no breakout meant no news, no
  watchlist, all day. The tick loop now runs
  `ingest_news()` every `NEWS_INGEST_SECONDS` (60s), so the
  watchlist builds continuously, independent of breakouts.
* **UTC/IST fix.** Railway (UTC) timestamps made every
  story look 5h30m stale on the IST bot. All DB timestamps
  now written as naive IST (`ist_now()`); check tool
  auto-detects legacy UTC rows. **Redeploy Railway.**
* **ACTIVE MARKET SCANNER (second arming path).** The bot
  actively scans the whole market: top
  `MARKET_SCAN_TOP_N` (20) stocks by live % change (min
  +2.0%) are armed even without matched news. ORB close
  breakout + Brain + Risk still required. Not the old
  momentum path — leaders only, no pre-9:30 entries.

---

## Completed Modules

### Core Engine

* Universe Builder
* Instrument Loader
* Tick Cache
* ORB Engine (live + historical fallback)
* Strategy (closed-candle breakout confirmation)
* Position Manager
* Risk Manager (breakeven ratchet fixed)
* Paper + Live Execution
* Trade Logger
* Position Recovery + Broker Sync

### Institutional Layer (v2.1)

* Risk Governor — daily loss kill switch, loss-streak pause,
  portfolio heat cap, sector concentration cap, veto power
* Conviction Engine — Strength × Agreement × Confidence, grades,
  conflict handling, Brain conviction gate
* Memory Repository — persistent SQLite institutional memory
* Market Memory — persistent catalysts, ORB outcomes,
  trade outcomes, sector leadership, similar-event recall
* Pattern Engine — repeated ORB failure detection, historical
  win-rate evidence, sector streak evidence
* Company Intelligence — permanent dossiers (750 companies),
  event history, behavioral evidence
* News evidence connected into the live decision flow

### Institutional AI Layer (v2.2)

* Event Intelligence — every story becomes a structured,
  permanent, per-stock event (type, importance, severity,
  confidence, horizon, direction, historical similarity)
* F&O Opportunity Engine — live catalyst watchlist over the
  F&O universe, restart-safe, feeds FNO_CATALYST evidence
* Living Company Profiles — profiles evolve automatically
  on every event (last catalyst, event mix, counts)
* Conviction Calibration — conviction band vs. realized
  outcome (the learning layer's honesty check)
* Portfolio Exposure Intelligence — sector/theme
  concentration with warnings
* Institutional desk commands: /brief /fno /exposure
  /calibration /events /journal /eod

### Intelligence Carriers & Dynamics (v2.3)

* Regulatory Collector — SEBI, RBI (press + notifications),
  PIB feeds registered in both the Railway 24/7 service and
  the main bot (feed URLs pending live validation — sandbox
  network was blocked; parsing logic fixture-tested)
* Results Calendar — "no new risk into binary events":
  entries on stocks with results today are hard-blocked;
  /calendar to view/add; CSV + DB persistence
* Knowledge Graph — weighted edges seeded from master
  (industry peers, theme members) + curated supplier/
  customer/subsidiary edges via Masterdata/graph_edges.csv;
  event-class routing tables; damped propagation with
  materiality floor; SYMPATHY spillover evidence; /graph
* Dynamic Trade Manager — partial profit booking at 1R
  (config), trail ratchet after 1.5R, catalyst exits when a
  fresh negative event hits a held name; partial-exit
  support in Position Manager and Engine

### Priority Upgrades (v2.4)

* Edge Analyzer — expectancy NET of all charges from the
  trade log, with hour/sector/conviction/exit breakdowns
  and an honest verdict (min 30 trades); /edge command;
  standalone: py edge_analyzer.py
* Risk Config Coherence Audit — every startup detects
  contradictory limits (per-trade risk vs daily loss vs
  heat vs position count) and prints warnings
* Event Outcome Write-Back — /eod grades today's
  structured events with realized day moves; event
  evidence now cites historical reaction distributions
  ("hist avg +2.1% ±1.4, n=7") once ≥5 graded samples
* Calendar Harvester — board-meeting intimations in the
  news flow auto-populate the results calendar (wordy +
  numeric date formats)
* Execution Hardening — LIMIT/SL price mapping, order
  retries, post-placement fill confirmation, slippage
  capture to fills_log.csv (paper + live); /execution
* Starter curated graph edges (Masterdata/graph_edges.csv,
  ~30 public relationships — REVIEW before trusting)
* Test isolation: smoke test no longer touches real trade
  log or fills log

### Cause & Effect Intelligence (v2.5)

* Causal Knowledge Base (causal_knowledge.py) — ~30
  permanent institutional cause-effect models across
  monetary policy (RBI cut/hike/liquidity/FX), Fed
  (hike/QT, cut/QE), commodities (crude both ways, steel,
  base metals, gold, coal/gas, agri), currency (INR both
  ways), government policy (budget capex, defence,
  railway, PLI, renewables/EV, rural), trade (China+1,
  import duties), geopolitics (war, shipping, elections),
  regulatory (moat compression — the IEX lesson, SEBI
  tightening), natural events (monsoon both ways,
  floods, heat waves) — each with 1st/2nd/3rd-order
  effects, signs, strengths, horizons, leading
  indicators, and what institutions monitor
* Causal Reasoning Engine — events activate damped
  chains (2nd order ×0.5, 3rd ×0.25, materiality floor),
  resolved to symbols via profiles, merged with own
  graded history ("never reasons from scratch"),
  emitting CAUSAL evidence with the full mechanism as
  explanation; restart-safe; /causal [SYMBOL] command

### Clean Architecture + Dashboard (v2.6)

* Repository reorganized into layer packages: core/,
  intelligence/, news/, trading/, notifications/ — all
  imports rewritten and verified; docs consolidated in
  docs/; 19 dead/empty files deleted
* docs/BOT_KNOWLEDGE_MAP.md — complete run→result guide
* Live Dashboard (dashboard.py → http://localhost:8181):
  live PnL curve, open positions, trade log, PnL-by-hour
  analysis, conviction-vs-PnL quality scatter (stdlib
  only, auto-refresh 5s)
* run_all_tests.py updated (6 suites)

### Intelligence

* Sector / Industry / Theme / Relative Strength Engines
* Market Mood, Market Environment, Market Catalyst
* News Engine + Railway news service
* Evidence Builder / Validator, Brain, Opportunity Pool

### Monitoring & Control

* Bot Monitor, Watchdog, Event/Error Loggers
* Telegram Command Center:
  /status /capital /mtm /positions /health
  /risk /memory /company /pool /sectors
  /pause /resume /tradingoff /tradingon /exitall

### Tests

* tests/test_institutional_layer.py (185 checks)
* tools/smoke_test.py (end-to-end paper pipeline, 23 checks)
* Refreshed: risk manager, strategy, position manager,
  capital manager tests

---

## Pending

* Live paper session validation of the new gates (next market day)
* Stages 6–10 of the Institutional Playbook (capital allocation cycle)
* Conviction-tiered position sizing
* Results Engine live parser
* Evidence lifecycle (freshness/decay) in Evidence Validator
* Company profile enrichment collectors (promoters, plants, clients)

---

## Next Milestone

First paper session with the full institutional pipeline:
Evidence → Conviction → Brain Gate → Risk Governor → Execution
→ Memory → Pattern learning visible in /memory reports.

---

Last Updated: 18-Jul-2026
