# ORB AUTO TRADER

## Version

**Version:** 1.0.0-PAPER

---

# Overview

ORB Auto Trader is an automated Opening Range Breakout (ORB) trading system for the Indian stock market.

The bot:

* Connects to Dhan Market Feed
* Monitors a dynamic stock universe
* Builds the 09:15–09:30 Opening Range
* Detects ORB breakouts
* Executes paper trades
* Manages risk automatically
* Sends Telegram alerts
* Logs every completed trade
* Generates trade analytics and daily reports

---

# Features

## Trading

* Dynamic Stock Universe
* Live Market Feed (Dhan)
* ORB Builder
* Breakout Detection
* Paper Trading
* Risk Management
* Position Sizing

## Monitoring

* Live Bot Dashboard
* Watchdog
* System Health Check

## Notifications

* Startup Alert
* BUY Alert
* SELL Alert
* Daily Telegram Report

## Analytics

* Trade Logger
* Trade Analytics Dashboard

---

# Project Structure

```text
orb-auto-trader/

├── main.py
├── market_data.py
├── engine.py
├── strategy.py
├── orb_engine.py
├── tick_cache.py
├── risk_manager.py
├── position_manager.py
├── paper_execution.py
├── trade_logger.py
├── trade_analytics.py
├── telegram_notifier.py
├── telegram_daily_report.py
├── bot_monitor.py
├── watchdog.py
├── system_check.py
├── config.py
├── trade_log.csv
├── .env
├── data/
├── tests/
├── logs/
├── reports/
└── README.md
```

---

# Environment Variables

Create a `.env` file.

Required variables:

```
DHAN_CLIENT_ID=

DHAN_ACCESS_TOKEN=

TELEGRAM_BOT_TOKEN=

TELEGRAM_CHAT_ID=
```

---

# Installation

Install required packages:

```bash
py -m pip install -r requirements.txt
```

---

# Daily Workflow

Before Market

```bash
py system_check.py
```

If all checks pass:

```bash
py main.py
```

---

# During Market

The bot automatically:

* Builds ORB
* Detects breakouts
* Executes paper trades
* Sends Telegram notifications
* Logs completed trades

---

# After Market

View analytics:

```bash
py test_trade_analytics.py
```

Send Telegram summary:

```bash
py test_daily_report.py
```

---

# Telegram Notifications

Supported notifications:

* Bot Started
* BUY Executed
* SELL Executed
* Daily Report

---

# Current Status

Version: **1.0.0-PAPER**

Status:

* Paper Trading Ready
* Awaiting Live Market Validation

---

# Future Roadmap

## Version 1.1

* Signal Logger
* Auto Reconnect
* Professional Logging
* Daily Reports Automation

## Version 2.0

* Live Trading
* Dhan Order Placement
* Portfolio Tracking
* News Scanner
* AI-powered Alerts
* Sector Strength Analysis
* Institutional Flow Analysis

---

# License

Private Project

Developed for personal automated trading and research.
