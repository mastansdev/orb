# ORB AUTO TRADER - SYSTEM ARCHITECTURE

---

# PURPOSE

This document explains how the ORB AUTO TRADER works from startup to shutdown.

It is not a development log.

It is not a roadmap.

It is the permanent reference document that explains the complete working architecture of the bot.

PROJECT_BRAIN.md explains **what we are building**.

SYSTEM_ARCHITECTURE.md explains **how the system works**.

---

# CORE PHILOSOPHY

Every module has only one responsibility.

No module should perform another module's work.

The system always works in one direction:

Market Data

↓

Intelligence

↓

Trade Decision

↓

Execution

↓

Monitoring

↓

Analytics

Execution never becomes intelligent.

Intelligence never places trades.

---

# COMPLETE SYSTEM FLOW

User runs:

```
py main.py
```

↓

System starts

↓

Market data connection established

↓

Live market ticks received

↓

Market intelligence updated

↓

Trade evaluated

↓

Trade approved or rejected

↓

Execution (if approved)

↓

Position managed

↓

Trade logged

↓

Reports generated

---

# STARTUP SEQUENCE

## 1. main.py

Purpose

Entry point of the application.

Responsibilities

* Starts the entire system.
* Loads configuration.
* Creates all required modules.
* Starts the market feed.
* Keeps the application running.

main.py never analyses stocks.

main.py never places trades.

It only starts the system.

---

## 2. Master Loader

Purpose

Loads static market information.

Contains

* Symbol
* Security ID
* Company Name
* Sector
* Industry
* Theme
* Lot Size
* F&O Status

This information changes very rarely.

Every intelligence engine uses this information.

Master Loader is the single source of truth for static stock metadata.

---

## 3. Market Data Engine

Purpose

Connects to Dhan MarketFeed.

Responsibilities

* Connect WebSocket
* Receive live ticks
* Monitor connection
* Reconnect automatically
* Pass every tick to the Engine

It never decides trades.

It only receives live market information.

---

## 4. Engine

Purpose

Acts as the central coordinator.

Every market tick enters here first.

Example

Market Tick

↓

Engine

↓

Distribute tick to intelligence modules

The Engine does not analyse stocks.

It only distributes information.

---

# MARKET INTELLIGENCE LAYER

Every engine performs one independent analysis.

Each engine produces its own opinion.

No engine executes trades.

---

## Historical ORB Engine

Purpose

Build the official ORB range using historical market data.

Outputs

* ORB High
* ORB Low
* ORB Width

---

## Live ORB Engine

Purpose

Fallback when historical ORB cannot be obtained.

Produces the same ORB information using live ticks.

---

## ORB Quality Engine

Purpose

Evaluate the quality of the ORB.

Checks

* ORB Width
* Breakout Quality
* Entry Buffer
* Fake Breakout Detection

Produces an ORB quality assessment.

---

## Sector Engine

Purpose

Measure the strength of the stock's sector.

Example

If most IT stocks are strong,

then the IT sector is strong.

Outputs

* Participation
* Average Change
* Leader
* Laggard
* Sector Status
* Sector Score

---

## Industry Engine

Purpose

Measure the strength of the stock's industry.

Industry is more specific than sector.

Example

Sector

Financial Services

Industry

Private Banks

---

## Theme Engine

Purpose

Evaluate whether a market theme is active.

Examples

* Defence
* Railway
* Renewable Energy
* PSU
* AI
* EV

---

## News Engine

Purpose

Analyse market news.

Checks

* Positive news
* Negative news
* Breaking news
* High impact events

Produces a News Score.

---

## Results Engine

Purpose

Analyse quarterly company results.

Checks

* Revenue
* Profit
* Margins
* Guidance

Produces a Results Score.

---

## Market Breadth Engine

Purpose

Measure overall market health.

Checks

* Advancing stocks
* Declining stocks
* Market participation

Produces a Breadth Score.

---

## Additional Intelligence Engines

Future engines include

* Relative Volume
* Liquidity
* Gap Quality
* Delivery Percentage
* Momentum
* Volatility
* OI
* Institutional Activity

Each engine has one responsibility.

---

# TRADE SELECTION ENGINE v2

Purpose

Acts as the brain of the system.

It receives results from every intelligence engine.

Example Inputs

* ORB
* Sector
* Industry
* Theme
* News
* Results
* Breadth
* Liquidity
* Momentum
* Gap
* Delivery
* Volatility

The Trade Selection Engine never places trades.

It only decides whether the trade deserves capital.

Outputs

* Approved
* Watch
* Reject

Reason for decision

Institutional Score

Trade Grade

---

# EXECUTION LAYER

The execution layer is frozen.

Its responsibility begins only after a trade has been approved.

It never analyses market intelligence.

---

## Risk Manager

Checks

* Maximum daily loss
* Position risk
* Stop loss
* Allowed exposure

Decides whether execution is safe.

---

## Capital Manager

Determines

* Capital allocation
* Quantity
* Position size

Never decides trade quality.

---

## Execution

Places the order.

Paper or Live.

Nothing else.

---

## Position Manager

Monitors open trades.

Handles

* Target
* Stop Loss
* Trailing Stop
* Time Exit
* Hard Exit

---

# MONITORING

Monitors system health.

Includes

* Telegram
* Bot Monitor
* Watchdog
* Event Logger
* Error Logger
* Trade Logger

Monitoring never influences trade decisions.

---

# ANALYTICS

Records performance after trading.

Examples

* Daily P&L
* Win Rate
* Drawdown
* Sector Performance
* Industry Performance
* Theme Performance
* Capital Utilization
* Execution Latency
* Rejection Analysis

Analytics improves future development.

It never changes live execution.

---

# FUTURE AI LAYER

AI is an advisor.

It never executes trades.

Future responsibilities

* Summarise News
* Summarise Results
* Explain Corporate Actions
* Detect Sector Rotation
* Detect Institutional Activity
* Explain Trade Decisions
* Trade Forensic Analysis

AI assists decision making.

Final trading decisions remain rule-based.

---

# INFORMATION FLOW

The system always follows one direction.

Dhan MarketFeed

↓

Market Data Engine

↓

Engine

↓

Intelligence Engines

↓

Trade Selection Engine

↓

Risk Manager

↓

Capital Manager

↓

Execution

↓

Position Manager

↓

Monitoring

↓

Analytics

No module should bypass this flow.

---

# DESIGN PRINCIPLES

1. One responsibility per module.

2. Execution layer remains free from intelligence.

3. Intelligence layer never executes trades.

4. Every new engine must improve profitability or reduce unnecessary trades.

5. All trade decisions must be explainable.

6. Prefer modular, reusable components over tightly coupled code.

7. Avoid duplicate data ownership.

8. Build for long-term maintainability rather than short-term convenience.

---

# LONG-TERM VISION

Build an institutional-grade ORB trading framework where every trade is evaluated using multiple independent intelligence engines before capital is committed.

The objective is not to trade more.

The objective is to trade fewer, higher-quality opportunities while protecting capital, maintaining stable execution, and providing complete transparency for every trade decision.
