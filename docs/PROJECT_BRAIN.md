###### Allocate capital where institutional probability of continuation is highest, and withdraw capital immediately when that probability deteriorates. - Highest Priority

Capital is scarce. Every trade must justify why it deserves capital over the other 749 stocks.
Every position is temporary. The Brain continuously re-evaluates whether the original reason for owning the stock still exists.
Capital has an opportunity cost. A better opportunity may justify rotating capital from an existing position.
Evidence changes conviction. News, government actions, results, sector rotation, market behaviour, and live price action continuously update the Brain's conviction.
Execution is a tool, not the strategy. ORB is today's entry mechanism. The Brain decides whether capital should be allocated; execution decides how.



# ORB AUTO TRADER – PROJECT CONTINUATION PROMPT

You are continuing development of my ORB Auto Trader. This is NOT a new project.

Before suggesting any code:

* Understand the existing architecture.
* Never redesign modules without a clear profitability or risk-management benefit.
* Never assume code. If you need to modify a file, ask me to upload the current version first.
* Always tell me:

  1. Which file to modify.
  2. Which method/class.
  3. Exactly where to insert, replace or delete code.
  4. Whether to run the bot after the change or not.
* Never overwrite previous work by assumption.
* We develop in small verified phases. Every phase must compile before moving to the next.

## Development Philosophy

The bot does not have a trade target. It has a profit objective and a capital protection objective. The number of trades is merely a consequence of market opportunity.

This bot is NOT intended to become another generic ORB breakout bot.

The objective is:

* High conviction trades.
* Institutional-style decision making.
* Quality over quantity.
* Risk reduction first.
* Profitability improvement through better trade selection.

Every new feature must answer:

1. Why is it needed?
2. How does it improve trade quality or risk management?
3. Where does it fit into the architecture?
4. Only then should code be written.

If the feature does not improve profitability, conviction or risk management, do not build it.

---

# Current Architecture

Master Loader

↓

Price Engine

↓

Sector Engine

↓

Industry Engine

↓

Theme Engine

↓

Results Engine (Framework Complete)

↓

System Registry

↓

Intelligence Engine

↓

Trade Selection Engine (Conviction Engine)

---

# Engines Completed

✅ Master Loader

* Loads 750 stocks.
* F&O and Cash support.
* Sector mapping.
* Industry mapping.
* Theme parsing.
* Keyword parsing.
* Peer lookup.
* Reverse indexes.
* Stock profile APIs.

---

✅ Price Engine

Live LTP updates.

---

✅ Sector Engine

* Live updates
* Rankings
* Participation
* Average change
* Leader/Laggard
* Status
* Snapshot APIs

---

✅ Industry Engine

Same architecture as Sector Engine.

---

✅ Theme Engine

Fully completed.

Includes:

* Initialization
* Multi-theme support
* Rankings
* Participation
* Average change
* Leader/Laggard
* Status
* Live updates
* Snapshot
* Top themes
* Bottom themes
* Theme summaries

Theme is fully connected to:

* Engine
* Registry
* Intelligence Engine

---

✅ Results Engine

Framework completed.

Supports:

* Status
* Score
* Revenue surprise
* Profit surprise
* EBITDA surprise
* Guidance
* Result date
* Last update

Waiting for live results parser.

---

✅ Intelligence Engine

Current providers:

* Price
* Sector
* Industry
* Theme
* Results

Returns one unified intelligence snapshot.

---

✅ Trade Selection Engine

Phase 1 completed.

Architecture has been refactored.

Current private methods:

* _score_orb()
* _score_sector()
* _score_industry()
* _score_theme()
* _build_decision()

evaluate() is now an orchestrator.

Theme scoring is implemented as a conviction bonus:

0 Strong Themes → +0

1 Strong Theme → +20

2 Strong Themes → +40

3+ Strong Themes → +60

Theme never rejects trades.

Current scoring:

ORB → 100

Sector → 100

Industry → 100

Theme → 0–60

---

# Current Development Status

Architecture is stable.

Every phase has been verified using:

py main.py

Current result after every change:

* No syntax errors.
* No import errors.
* No startup regressions.

Live trading validation is pending because development occurred during a market holiday.

---

# Coding Rules

Never assume the current file contents.

Always ask me to upload the latest version of any file before suggesting modifications.

After reviewing the uploaded file:

* Verify it.
* Approve it.
* Then suggest only the next change.

Never rewrite entire files when only a small modification is required.

Never create unnecessary files.

Keep the architecture modular.

---

# Development Order

Highest priority now:

1. Relative Strength Engine
2. Connect Results Engine to live earnings parser
3. News Impact Engine
4. Market Breadth Engine
5. Position Sizing Engine
6. Conviction Grades (A+, A, B, C)

These are expected to improve trade quality more than simply adding additional metadata.

---

# Debugging Philosophy

During development:

* Verify every change.
* Approve code before execution.
* Use phased implementation.
* Never perform large rewrites.
* Maintain a runnable bot after every phase.

---


Documentation Priority

1. Source Code
        ↓
2. PROJECT_BRAIN.md
        ↓
3. ARCHITECTURE_HANDBOOK.xlsx

A feature is considered COMPLETE only when all three are updated (if applicable).

# Important

Treat this project as a continuation.

Do not ask me to explain the bot again.

Use the uploaded PROJECT_BRAIN.md as the authoritative project context.

Ask only for the current file being modified, verify it, and continue from the exact point where development stopped.
