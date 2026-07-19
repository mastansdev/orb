# ORB AUTO TRADER

**Version 2.6.0 — Institutional AI Trading System (Paper)**

An institutional-grade intraday trading system for NSE: evidence-based
decisions, permanent memory, causal reasoning, independent risk governance —
with ORB breakouts as the execution trigger.

> Philosophy: *Evidence contributes; Conviction decides; Risk authorizes;
> Execution acts.* See `docs/INSTITUTIONAL_TRADING_CONSTITUTION.md`.

---

## Quick Start

```
py run_all_tests.py     # verify everything (should print 6/6)
py main.py              # start the bot (paper trading)
py dashboard.py         # live dashboard → http://localhost:8181
```

Manage via Telegram: `/status /brief /risk /fno /causal /edge /eod` … (24 commands, `/help` lists all).

## Repository Map

| Folder | Contents |
|---|---|
| `core/` | engine, ORB, candles, strategy, master loader, recorder |
| `intelligence/` | brain, conviction, evidence, causal reasoning, knowledge graph, memory engines |
| `news/` | news pipeline: classify → stories → impact |
| `trading/` | execution, risk governor, positions, portfolio, edge analyzer |
| `notifications/` | telegram command center, loggers |
| `collectors/` | RSS, BSE, NSE, SEBI/RBI/PIB feeds |
| `repositories/` | SQLite memory + Postgres intelligence persistence |
| `tests/`, `tools/` | test suite, smoke test, forensics |
| `docs/` | **BOT_KNOWLEDGE_MAP.md** ← start here, constitution, specs |
| `Masterdata/`, `data/` | stock master, graph edges, calendars, universe |

Full use-case guide: **`docs/BOT_KNOWLEDGE_MAP.md`**

## Safety

Paper mode by default (`TRADING_MODE = "PAPER"`, `ENABLE_ORDER_PLACEMENT = False`).
Independent Risk Governor with daily-loss kill switch, loss-streak pause,
portfolio heat and sector caps. Config coherence audit at every startup.
