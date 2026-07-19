# INTELLIGENCE SNAPSHOT SPECIFICATION
Version : v1.0
Date    : 04-Jul-2026

--------------------------------------------------------
PURPOSE
--------------------------------------------------------

This document defines the standard communication contract
between all Intelligence Engines.

Every intelligence module MUST expose the same public
interface.

This contract must never be broken.

--------------------------------------------------------
CORE PRINCIPLES
--------------------------------------------------------

1. One Module = One Responsibility

2. One Responsibility = One Owner

3. Engine.py is the ONLY update pipeline.

4. IntelligenceEngine NEVER owns data.

5. TradeSelectionEngine NEVER communicates directly with
   individual intelligence engines.

6. All intelligence is exchanged only through
   Intelligence Snapshots.

--------------------------------------------------------
STANDARD PUBLIC INTERFACE
--------------------------------------------------------

Every Intelligence Engine MUST expose only:

update(...)

get_snapshot(symbol)

health()

No additional public methods unless absolutely required.

--------------------------------------------------------
SNAPSHOT FORMAT
--------------------------------------------------------

Every engine returns a dictionary.

Example

{
    "engine": "price",

    "symbol": "RELIANCE",

    "data": {

    }
}

--------------------------------------------------------
PRICE ENGINE
--------------------------------------------------------

{
    "engine": "price",

    "symbol": "RELIANCE",

    "data": {

        "ltp": 2987.45,

        "change": 1.82,

        "last_update": "09:45:08"

    }
}

--------------------------------------------------------
SECTOR ENGINE
--------------------------------------------------------

{
    "engine": "sector",

    "symbol": "RELIANCE",

    "data": {

        "sector": "Oil & Gas",

        "rank": 4,

        "strength": 87.2,

        "avg_change": 1.54

    }
}

--------------------------------------------------------
INDUSTRY ENGINE
--------------------------------------------------------

{
    "engine": "industry",

    "symbol": "RELIANCE",

    "data": {

        "industry": "Refineries",

        "rank": 2,

        "strength": 91.3,

        "avg_change": 2.14

    }
}

--------------------------------------------------------
FUTURE MODULES
--------------------------------------------------------

Every future module follows the same format.

Theme

Results

News

Breadth

Institutional Score

AI

--------------------------------------------------------
INTELLIGENCE ENGINE
--------------------------------------------------------

Responsibilities

Read snapshots.

Merge snapshots.

Return one combined Intelligence Snapshot.

Never calculate.

Never update.

Never own data.

--------------------------------------------------------
MERGED SNAPSHOT
--------------------------------------------------------

Example

{

    "price": {...},

    "sector": {...},

    "industry": {...},

    "theme": None,

    "results": None,

    "news": None,

    "breadth": None,

    "institutional_score": None

}

--------------------------------------------------------
TRADE SELECTION ENGINE
--------------------------------------------------------

Receives ONLY:

evaluate(

    symbol,

    ltp,

    orb,

    intelligence

)

TradeSelectionEngine must never know where
the intelligence originated.

--------------------------------------------------------
ENGINE OWNERSHIP
--------------------------------------------------------

Engine.py owns

PriceEngine

SectorEngine

IndustryEngine

ThemeEngine

ResultsEngine

NewsEngine

BreadthEngine

IntelligenceEngine owns NONE of them.

--------------------------------------------------------
PROJECT RULE
--------------------------------------------------------

Any new intelligence module must implement
the standard interface and snapshot format.

If it cannot follow this specification,
its design must be reconsidered before implementation.