# 🚀 START HERE — The ORB Auto Trader Handbook

*The friendly "read me first" book. If you only ever read one file, read this one.*
*Written so plainly that a curious 5‑year‑old (and a busy adult at 6am) can follow it.*

---

## 🧒 1. What is this, in one breath?

Imagine the stock market opens like a playground gate at 9:15 in the morning.
In the **first 15 minutes**, each stock draws an invisible **box**: the **highest**
price it touched (roof) and the **lowest** price it touched (floor).

- If the price **jumps over the roof** 🦘 → buyers are excited → it often keeps running **up**.
- That jump is called an **ORB — Opening Range Breakout**.

**This bot watches for those jumps all day, and when a strong one happens on a
good company, it buys — automatically.** Then it babysits the trade and sells to
lock in profit before the day ends.

That's it. Everything else in this folder exists to make that one idea **smart,
safe, and hands‑free**.

---

## 🎯 2. What does the bot actually buy?

For every strong breakout it takes **two things at once**:

1. **The stock (equity)** — the normal share.
2. **1 lot of the ATM CALL option** — *(NEW)* an options bet that pays more when
   the stock moves fast. "ATM" = the strike price closest to where the stock is
   right now.

> **Real example (your ABB trade):** ABB was trading at **7374** when the 10:30
> candle broke out. The bot picks the **7350 CALL, this month's expiry** — because
> 7350 is the strike nearest to 7374 — and buys **1 lot (125 qty)**. Exactly like
> you asked.

The option rides **alongside** the stock. It never replaces it.

---

## 🛡️ 3. Is it safe right now? (Yes.)

The bot is in **PAPER MODE** — it plays with **pretend money** and places **no real
orders**. You can watch it "trade" all day and lose/win nothing real.

Two switches in `config.py` control this:

| Switch | Now | Meaning |
|---|---|---|
| `TRADING_MODE` | `"PAPER"` | Pretend money. Change to `"LIVE"` only when you're 100% ready. |
| `ENABLE_ORDER_PLACEMENT` | `False` | No real orders leave your computer. |

**Leave these as‑is for Monday.** Watch it on paper first. 👀

---

## ▶️ 4. How do I run it? (3 commands)

Open a terminal in this folder and type:

```
py run_all_tests.py     # 1. Health check — should say tests passed
py main.py              # 2. Start the bot (paper trading)
py dashboard.py         # 3. Open the live scoreboard in your browser
```

Then open your browser to 👉 **http://localhost:8181** to see the live dashboard
(profit curve, open positions, trade log).

You also control it from your phone on **Telegram** (see §7).

> **Before market open you need:** your Dhan login keys saved in the `.env` file
> (`DHAN_CLIENT_ID`, `DHAN_ACCESS_TOKEN`) and, for phone alerts,
> `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`. These stay private and are never
> shared to GitHub.

---

## 🧠 5. How the bot "thinks" (the assembly line)

A trade only happens if it survives this line — like passing through 5 gates:

```
   NEWS + PRICE + PATTERNS          "What's going on with this stock?"
            ⬇  (Evidence)
      CONVICTION ENGINE             "How sure are we? Give it a grade."
            ⬇
        BRAIN GATE                  "Do we actually believe this?"
            ⬇
     RISK GOVERNOR                  "Are we allowed? (loss limits, heat)"
            ⬇
       EXECUTION                    "BUY the stock + 1 ATM option."
            ⬇
        MEMORY                      "Remember what happened, learn from it."
```

The bot's motto (from its constitution): **"Evidence contributes; Conviction
decides; Risk authorizes; Execution acts."**

---

## 🗺️ 6. Which file does what? (The map)

You do **not** need to understand every file. This is just so you always know
where to look. Think of it as rooms in a house. 🏠

### 🟢 The Front Door (start here)
| File | Plain English |
|---|---|
| `main.py` | The light switch. Running it starts everything. |
| `market_data.py` | The engine's ignition — connects to Dhan, streams live prices, starts the bot. |
| `config.py` | **The control panel.** Every setting/knob lives here. Your most‑edited file. |
| `dashboard.py` | The live scoreboard website (localhost:8181). |
| `run_all_tests.py` | The pre‑flight health check. |

### 🔵 `core/` — The Heartbeat (prices → breakouts → trades)
| File | Plain English |
|---|---|
| `engine.py` | **The boss.** Ties everything together, decides when to enter/exit. |
| `orb_engine.py` | Draws the 9:15–9:30 box (roof & floor) for each stock. |
| `strategy.py` | The rule: "did a candle *close* above the roof?" (ignores fake pokes). |
| `candle_engine.py` | Builds price candles from the live tick stream. |
| `tick_cache.py` | Short‑term memory of the latest prices. |
| `watchlist.py` | The list of stocks to watch today. |
| `master_loader.py` / `instrument_loader.py` | The phone book — turns a name ("ABB") into an ID the broker understands. |
| `historical_data.py` | Fetches past candles (e.g. yesterday) when needed. |
| `market_recorder.py` / `market_replay.py` | Records a live day and lets you replay it for practice. |
| `watchdog.py` / `bot_monitor.py` | The nurse — checks the bot is alive and healthy. |

### 🟣 `trading/` — The Hands (money, risk, orders) ← *your new option code lives here*
| File | Plain English |
|---|---|
| **`option_leg.py`** | **⭐ NEW. Buys the 1‑lot ATM monthly CALL and babysits it** with a smart trailing exit (see §8). |
| `greeks_check.py` | Reads an option's Greeks (delta/theta/etc.) — the "weather report" for an option. |
| `execution.py` | The single door all buy/sell orders pass through. |
| `paper_execution.py` | Pretend‑money order filler (used now). |
| `live_execution.py` | Real‑money order filler (used only in LIVE mode). |
| `position_manager.py` / `open_position_manager.py` | Keeps track of what you're holding and how big. |
| `risk_governor.py` | **The bodyguard.** Daily loss kill‑switch, loss‑streak pause, heat & sector caps. Can veto any trade. |
| `risk_manager.py` | Sets the stop‑loss and break‑even ratchet per trade. |
| `dynamic_trade_manager.py` | Books partial profit, trails the rest, exits on bad news. |
| `capital_manager.py` / `portfolio_ledger.py` | The wallet — how much money is free vs used. |
| `charges_calculator.py` | Subtracts brokerage/taxes so profit numbers are honest. |
| `edge_analyzer.py` | Report card: are we *actually* making money, after costs? |
| `trade_logger.py` | Writes every trade to `trade_log.csv`. |
| `broker_sync.py` / `position_recovery.py` | If the bot restarts, it re‑finds its open trades. |

### 🟠 `intelligence/` — The Brain (news, conviction, memory, learning)
| File | Plain English |
|---|---|
| `brain.py` | The thinker that weighs all the evidence and forms an opinion. |
| `conviction_engine.py` | Turns evidence into a **confidence grade** (how sure are we?). |
| `evidence.py` / `evidence_builder.py` / `evidence_validator.py` | Collects and sanity‑checks clues. |
| `market_memory.py` / `pattern_engine.py` | **Permanent memory** — remembers past breakouts & outcomes, spots repeat patterns. |
| `company_intelligence.py` | A permanent dossier on each company (like your Kalyan Jewellers rerating story). |
| `causal_knowledge.py` / `causal_reasoning_engine.py` | Cause‑and‑effect brain ("RBI cuts rates → banks up"). |
| `fno_opportunity_engine.py` | Live radar for fresh catalysts across F&O stocks. |
| `sector_engine.py` / `theme_engine.py` / `relative_strength_engine.py` | Which sectors/themes are hot, which stock is strongest. |
| `market_mood_engine.py` / `market_regime_engine.py` | Is the whole market happy, scared, or sideways today? |
| *(others)* | Supporting brains for pricing, results calendars, rankings, decay of old news. |

### 🟡 `news/` + `collectors/` — The Ears (reads the news)
| Folder | Plain English |
|---|---|
| `collectors/` | Fetchers that pull headlines from NSE, BSE, SEBI/RBI, RSS feeds. |
| `news/` | Cleans, de‑duplicates, classifies each story and scores its impact on a stock. |

### ⚪ Supporting rooms
| Folder | Plain English |
|---|---|
| `notifications/` | Telegram alerts + your phone command center + error logs. |
| `repositories/` | The filing cabinets (SQLite/Postgres) where memory is saved. |
| `builders/` | One‑time scripts that build the stock universe & databases. |
| `adapters/` | Translators for outside data sources. |
| `tools/` | Handy check‑up scripts (`health_check.py`, `show_positions.py`, `smoke_test.py`). |
| `docs/` | The deep manuals (see §9). |
| `data/` / `Masterdata/` | The stock master list, option contracts, calendars. **Don't delete.** |

---

## 🎈 7. Where do I get information while it runs?

Three windows into the bot:

1. **📊 Dashboard** — http://localhost:8181 — live profit, positions, trade log.
2. **📱 Telegram** — type these to your bot:

   `/status` `/positions` `/mtm` `/capital` `/health` `/risk`
   `/brief` `/fno` `/exposure` `/edge` `/eod` `/events` `/causal` `/journal`
   `/pause` `/resume` `/exitall` … and `/help` to list them all.

3. **📁 Files you can open** —
   `trade_log.csv` (stock trades) · `option_legs_log.csv` (your option trades, with
   entry/peak/exit + Greeks) · `fills_log.csv` (how well orders filled) · `logs/`
   (error diary).

---

## 🎢 8. How the option trade protects your profit (the "no give‑back" rule)

An option's price is pushed around by many forces at once — how far the stock
moves (**delta/gamma**), time ticking away (**theta**), and nervousness in the market
(**vega/IV**). Trying to track each one separately is fragile.

**The clever shortcut:** the option's *live traded price already contains all of
those forces baked in.* So the bot just watches the **real option price** and uses a
**ratcheting trailing stop**:

- Buys at, say, **₹250**.
- As profit grows, it remembers the **highest price seen** (the "peak"). 📈
- Its exit line trails **15% below the peak — and only ever moves UP, never down.**
  - Peak ₹400 → exit line ₹340. Peak later ₹500 → exit line ₹425. It never loosens.
- Plus a **hard stop** (−25%) as a floor, and a **3:10pm time‑stop** so nothing is
  ever held overnight (that's how it dodges overnight time‑decay and gap risk).
- It writes the Greeks into the log so you can study them later.

**Plain version:** *once you're winning, it refuses to give the profit back.* Exactly
your instruction. ✅

Knobs (in `config.py`): `OPTION_INITIAL_STOP_PCT`, `OPTION_TRAIL_ACTIVATE_PCT`,
`OPTION_TRAIL_GIVEBACK_PCT`, `OPTION_TARGET_PCT`, `OPTION_TIME_STOP`, `OPTION_LOTS`.

---

## 📚 9. Want to go deeper? (the manuals)

Open the `docs/` folder in this order:

1. **`BOT_KNOWLEDGE_MAP.md`** — the "what do I run to get X" guide. Start here.
2. `SYSTEM_ARCHITECTURE.md` — how the pieces connect.
3. `INSTITUTIONAL_TRADING_CONSTITUTION.md` — the bot's rules of conduct.
4. `INSTITUTIONAL_TRADING_PLAYBOOK.md` — the full game plan.
5. `CONVICTION_SPECIFICATION.md` — how confidence grades are calculated.
6. `PROJECT_BRAIN_V2.md` — the deepest "how it all thinks" write‑up.
7. `VERSION.md` — the change history (currently **v3.3.0‑INSTITUTIONAL‑AI**).

---

## 🔧 10. Major upgrades still pending (and why they matter)

Honest list of what's **not** finished yet, roughly most‑useful first:

| Upgrade | What it means | Why it matters |
|---|---|---|
| **🔴 Live F&O order routing for options** | `live_execution.py` currently sends orders on the **equity** exchange only. Before trading options with **real money**, the option order must be routed to the **NSE_FNO** segment. | **Do this before ever flipping options to LIVE.** On PAPER it's fine as‑is. |
| **🟠 Live paper validation of the new gates** | Run one full real market day on paper and confirm Conviction → Brain → Risk → Execution → Memory all behave. | Proves the safety layers work before real money. |
| **🟠 Conviction‑tiered position sizing** | Bet bigger on A‑grade setups, smaller on B‑grade. | Turns "how sure am I" into "how much do I risk." |
| **🟡 Short / PUT side** | Today the bot is **long‑only** (breakouts → CALLs). Breakdowns → PUTs isn't wired yet. | Lets you profit on falling stocks too. |
| **🟡 Capital allocation cycle (Playbook stages 6–10)** | An automatic "how to spread money across ideas" loop. | Smarter use of your whole account. |
| **🟡 Results Engine live parser** | Auto‑read earnings results as they drop. | Avoid trading blindly into a results bomb. |
| **🟡 Evidence freshness/decay** | Old news should fade in importance automatically. | Keeps decisions based on *fresh* facts. |
| **⚪ Company profile enrichment** | Auto‑fill promoters, plants, clients per company. | Richer context for conviction. |
| **⚪ Independent option profit‑booking tiers** | Optional: book part of the option at +50%/+100% (only useful with >1 lot). | Fine‑tune option exits when you scale up lots. |

---

## ✅ 11. Your Monday‑morning checklist

```
[ ] .env has DHAN_CLIENT_ID + DHAN_ACCESS_TOKEN (and Telegram keys)
[ ] config.py: TRADING_MODE = "PAPER"   (keep it paper this week)
[ ] py run_all_tests.py     → tests pass
[ ] py main.py              → bot starts, says "Execution Mode : PAPER"
[ ] py dashboard.py         → open http://localhost:8181
[ ] Telegram /status        → replies
[ ] Watch a paper day. Check trade_log.csv + option_legs_log.csv after close.
```

Trade **on paper** first. When you're confident and have done the **Live F&O
routing** upgrade (§10), *then* consider real money — small.

---

## ⚠️ 12. One honest reminder

This is a powerful tool, not a money printer. Real F&O trading can lose money fast,
and no bot removes that risk. **Paper‑trade, watch, learn, and go slow.** You are
always the pilot; the bot is the co‑pilot. 🧑‍✈️

*Happy (careful) trading!*
