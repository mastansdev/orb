# ORB AUTO TRADER - MODULE DEPENDENCIES

---

# PURPOSE

This document explains how every Python module is connected.

It answers four questions for every module.

1. Who creates it?
2. What does it depend on?
3. Which modules use it?
4. What is its responsibility?

This document is the primary developer reference.

Never modify a module before understanding its dependencies.

---

# HIGH LEVEL DEPENDENCY FLOW

main.py

↓

engine.py

↓

market_data.py

↓

Market Feed

↓

Engine distributes every market tick

↓

Intelligence Layer

↓

Trade Selection Engine

↓

Execution Layer

↓

Monitoring

↓

Analytics

---

# MODULE DETAILS

================================================================================
main.py
=======

Purpose

Application entry point.

Created By

User

Started Using

```
py main.py
```

Responsibilities

* Load configuration
* Create Engine
* Start Market Data
* Keep application running

Depends On

* engine.py

Used By

None

Public Responsibility

Start the trading system.

Never performs analysis.

Never places trades.

---

================================================================================
engine.py
=========

Purpose

Central coordinator of the entire trading system.

Created By

main.py

Depends On

* market_data.py
* orb_engine.py
* sector_engine.py (currently sector_strength.py)
* strategy.py
* risk_manager.py
* capital_manager.py
* position_manager.py
* trade_logger.py
* telegram
* future intelligence engines

Used By

main.py

Responsibilities

* Receive every live tick
* Distribute ticks to intelligence modules
* Coordinate the complete workflow

Engine never decides whether a trade is good.

Engine never places orders.

Engine only coordinates modules.

---

================================================================================
market_data.py
==============

Purpose

Connect to Dhan MarketFeed.

Created By

engine.py

Depends On

* Dhan WebSocket

Used By

engine.py

Responsibilities

* Connect
* Receive ticks
* Reconnect automatically
* Pass ticks to Engine

Never analyses data.

---

================================================================================
master_loader.py
================

Purpose

Single source of static stock metadata.

Created By

Engine during startup.

Depends On

master_database.xlsx

Used By

* Sector Engine
* Industry Engine
* Theme Engine
* Future Intelligence Engines

Provides

* Symbol
* Security ID
* Company
* Sector
* Industry
* Theme
* Lot Size
* F&O

Never stores live market prices.

---

================================================================================
orb_engine.py
=============

Purpose

Calculate ORB levels.

Created By

engine.py

Depends On

Live market ticks

Used By

Trade Selection Engine

Responsibilities

* ORB High
* ORB Low
* Breakout detection
* ORB quality

Never executes trades.

---

================================================================================
sector_engine.py
(Currently sector_strength.py)
==============================

Purpose

Evaluate sector strength.

Created By

engine.py

Depends On

* master_loader.py
* Daily market data (Previous Close)
* Live market ticks

Used By

Trade Selection Engine

Responsibilities

* Sector participation
* Average change
* Sector ranking
* Leader
* Laggard
* Sector score

Never performs execution.

---

================================================================================
industry_engine.py
==================

Purpose

Evaluate industry strength.

Created By

engine.py

Depends On

* master_loader.py
* Sector Engine
* Live market data

Used By

Trade Selection Engine

Responsibilities

* Industry ranking
* Industry score
* Industry participation

---

================================================================================
theme_engine.py
===============

Purpose

Evaluate active market themes.

Created By

engine.py

Depends On

* master_loader.py
* News Engine
* Market data

Used By

Trade Selection Engine

---

================================================================================
news_engine.py
==============

Purpose

Analyse market news.

Created By

engine.py

Depends On

External news sources.

Used By

Trade Selection Engine

Outputs

News Score

Positive

Negative

Neutral

---

================================================================================
results_engine.py
=================

Purpose

Analyse company quarterly results.

Created By

engine.py

Depends On

Corporate result announcements.

Used By

Trade Selection Engine

---

================================================================================
market_breadth_engine.py
========================

Purpose

Measure overall market health.

Created By

engine.py

Depends On

Complete market data.

Used By

Trade Selection Engine

---

================================================================================
trade_selection_engine.py
=========================

Purpose

Brain of the trading system.

Created By

engine.py

Depends On

All intelligence engines.

Receives

ORB

Sector

Industry

Theme

News

Results

Breadth

Liquidity

Momentum

Gap

Volatility

Delivery

Outputs

Approved

Watch

Reject

Institutional Score

Reason

Never places orders.

---

================================================================================
strategy.py
===========

Purpose

Convert an approved trade into an executable trading instruction.

Created By

engine.py

Depends On

Trade Selection Engine

Used By

Risk Manager

Responsibilities

* Entry confirmation
* Trading rules
* Execution preparation

---

================================================================================
risk_manager.py
===============

Purpose

Protect trading capital.

Created By

engine.py

Checks

* Risk
* Stop loss
* Daily loss
* Position limits

Outputs

Approved

Rejected

Never evaluates market intelligence.

---

================================================================================
capital_manager.py
==================

Purpose

Determine capital allocation.

Created By

engine.py

Depends On

Risk Manager

Responsibilities

* Quantity
* Position sizing
* Available capital

Never decides trade quality.

---

================================================================================
paper_execution.py / live_execution.py
======================================

Purpose

Place orders.

Created By

engine.py

Depends On

Capital Manager

Responsibilities

Execute trades.

Nothing else.

---

================================================================================
position_manager.py
===================

Purpose

Manage open positions.

Created By

engine.py

Responsibilities

* Stop Loss
* Target
* Trailing Stop
* Time Exit
* Hard Exit

Never analyses new trades.

---

================================================================================
trade_logger.py
===============

Purpose

Permanent trade record.

Created By

engine.py

Responsibilities

Store

* Entry
* Exit
* P&L
* Time
* Quantity
* Reason

---

================================================================================
telegram.py
===========

Purpose

Notify the trader.

Responsibilities

* Alerts
* Trade updates
* Error notifications

Telegram never decides trades.

---

# DEPENDENCY RULES

1.

Information always flows downward.

Never upward.

2.

Execution Layer never calls Intelligence Layer.

3.

Every intelligence engine must be independent.

4.

One module owns one responsibility.

5.

No duplicate market calculations.

6.

Static metadata belongs in Master Loader.

7.

Live prices belong to the Market Data layer.

8.

Trade Selection is the only module allowed to combine multiple intelligence engines.

9.

Execution modules only consume approved trade instructions.

10.

Before modifying any module, understand every dependency listed above.

---

END OF DOCUMENT
