"""
==========================================================
Memory Repository
==========================================================

Persistent storage layer for institutional memory.

Uses a local SQLite database so memory survives
restarts and never depends on network services.

Owns tables:
    • market_events     — remembered market catalysts
    • orb_outcomes      — every ORB breakout result
    • trade_outcomes    — every closed trade
    • sector_days       — daily sector leadership record
    • company_events    — permanent per-company history

This module NEVER:
    • decides anything
    • scores anything
    • talks to brokers

It only remembers.

Author : H&M ORB AUTO TRADER
==========================================================
"""

import json
import sqlite3
from datetime import datetime
from threading import RLock

from config import MEMORY_DB_FILE


class MemoryRepository:

    def __init__(self, db_file=None):
        self._lock = RLock()

        self.db = sqlite3.connect(
            db_file or MEMORY_DB_FILE,
            check_same_thread=False
        )

        self.cursor = self.db.cursor()
        self._create_tables()

    # --------------------------------------------------

    def _create_tables(self):
        with self._lock:
            self.cursor.executescript("""

            CREATE TABLE IF NOT EXISTS market_events(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                trade_date TEXT,
                rule TEXT,
                category TEXT,
                sub_category TEXT,
                event_type TEXT,
                market_regime TEXT,
                market_impact TEXT,
                market_score REAL,
                confidence REAL,
                active INTEGER
            );

            CREATE TABLE IF NOT EXISTS orb_outcomes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                trade_date TEXT,
                symbol TEXT,
                sector TEXT,
                outcome TEXT,
                pnl REAL
            );

            CREATE TABLE IF NOT EXISTS trade_outcomes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                trade_date TEXT,
                symbol TEXT,
                sector TEXT,
                industry TEXT,
                theme TEXT,
                entry_time TEXT,
                exit_time TEXT,
                exit_reason TEXT,
                conviction REAL,
                pnl REAL
            );

            CREATE TABLE IF NOT EXISTS sector_days(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_date TEXT,
                sector TEXT,
                rank INTEGER,
                score REAL,
                UNIQUE(trade_date, sector)
            );

            CREATE TABLE IF NOT EXISTS company_events(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                trade_date TEXT,
                symbol TEXT,
                event_type TEXT,
                headline TEXT,
                source TEXT,
                payload TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_orb_symbol_date
                ON orb_outcomes(symbol, trade_date);

            CREATE INDEX IF NOT EXISTS idx_trades_symbol
                ON trade_outcomes(symbol);

            CREATE INDEX IF NOT EXISTS idx_company_symbol
                ON company_events(symbol);

            CREATE TABLE IF NOT EXISTS structured_events(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                trade_date TEXT,
                event_type TEXT,
                catalyst TEXT,
                symbol TEXT,
                sector TEXT,
                industry TEXT,
                theme TEXT,
                direction TEXT,
                importance REAL,
                severity REAL,
                confidence REAL,
                horizon TEXT,
                headline TEXT,
                story_id TEXT,
                realized_move REAL,
                prior_move REAL
            );

            CREATE INDEX IF NOT EXISTS idx_sevents_symbol
                ON structured_events(symbol);

            CREATE INDEX IF NOT EXISTS idx_sevents_type
                ON structured_events(event_type);

            CREATE TABLE IF NOT EXISTS trade_decisions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                trade_date TEXT,
                time TEXT,
                symbol TEXT,
                action TEXT,
                sector TEXT,
                conviction REAL,
                reason TEXT,
                evidence TEXT,
                pnl REAL
            );

            CREATE INDEX IF NOT EXISTS idx_decisions_date
                ON trade_decisions(trade_date);

            CREATE INDEX IF NOT EXISTS idx_decisions_symbol
                ON trade_decisions(symbol);

            """)
            self.db.commit()

            # Migration: prior_move on existing DBs
            try:
                self.cursor.execute(
                    "ALTER TABLE structured_events "
                    "ADD COLUMN prior_move REAL"
                )
                self.db.commit()
            except Exception:
                pass  # column already exists

            # Migration: abnormal_move (market-adjusted
            # reaction — the TRUE event impact, and the
            # input to the reaction-decay model)
            try:
                self.cursor.execute(
                    "ALTER TABLE structured_events "
                    "ADD COLUMN abnormal_move REAL"
                )
                self.db.commit()
            except Exception:
                pass

    # --------------------------------------------------

    @staticmethod
    def _today():
        return datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def _now():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --------------------------------------------------
    # Market Events
    # --------------------------------------------------

    def save_market_event(self, event):
        with self._lock:
            self.cursor.execute(
                """
                INSERT INTO market_events(
                    created_at, trade_date, rule, category,
                    sub_category, event_type, market_regime,
                    market_impact, market_score, confidence,
                    active
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    self._now(),
                    self._today(),
                    event.get("rule", ""),
                    event.get("category", ""),
                    event.get("sub_category", ""),
                    event.get("event_type", ""),
                    event.get("market_regime", ""),
                    event.get("market_impact", ""),
                    event.get("market_score", 0),
                    event.get("confidence", 0),
                    1 if event.get("active") else 0,
                ),
            )
            self.db.commit()

    # --------------------------------------------------

    def similar_market_events(self, rule, limit=20):
        """
        All previous occurrences of the same catalyst rule.
        This is the seed of Market Memory:
        'What happened the last N times this occurred?'
        """
        with self._lock:
            self.cursor.execute(
                """
                SELECT trade_date, market_impact,
                       market_score, confidence
                FROM market_events
                WHERE rule = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (rule, limit),
            )
            rows = self.cursor.fetchall()

        return [
            {
                "trade_date": row[0],
                "market_impact": row[1],
                "market_score": row[2],
                "confidence": row[3],
            }
            for row in rows
        ]

    # --------------------------------------------------
    # ORB Outcomes
    # --------------------------------------------------

    def save_orb_outcome(self, symbol, sector, outcome, pnl):
        with self._lock:
            self.cursor.execute(
                """
                INSERT INTO orb_outcomes(
                    created_at, trade_date, symbol,
                    sector, outcome, pnl
                )
                VALUES(?,?,?,?,?,?)
                """,
                (
                    self._now(),
                    self._today(),
                    symbol,
                    sector,
                    outcome,
                    pnl,
                ),
            )
            self.db.commit()

    # --------------------------------------------------

    def orb_failures_today(self, symbol):
        with self._lock:
            self.cursor.execute(
                """
                SELECT COUNT(*)
                FROM orb_outcomes
                WHERE symbol = ?
                  AND trade_date = ?
                  AND outcome = 'FAILED'
                """,
                (symbol, self._today()),
            )
            row = self.cursor.fetchone()

        return row[0] if row else 0

    # --------------------------------------------------

    def orb_stats(self, symbol, limit=50):
        """
        Historical ORB behaviour of one symbol.
        """
        with self._lock:
            self.cursor.execute(
                """
                SELECT outcome, pnl
                FROM orb_outcomes
                WHERE symbol = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (symbol, limit),
            )
            rows = self.cursor.fetchall()

        total = len(rows)
        wins = sum(1 for r in rows if r[0] == "SUCCESS")

        return {
            "symbol": symbol,
            "samples": total,
            "successes": wins,
            "failures": total - wins,
            "win_rate": round(wins / total * 100, 1) if total else None,
            "total_pnl": round(sum(r[1] or 0 for r in rows), 2),
        }

    # --------------------------------------------------
    # Trade Outcomes
    # --------------------------------------------------

    def save_trade_outcome(self, trade):
        with self._lock:
            self.cursor.execute(
                """
                INSERT INTO trade_outcomes(
                    created_at, trade_date, symbol, sector,
                    industry, theme, entry_time, exit_time,
                    exit_reason, conviction, pnl
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    self._now(),
                    trade.get("trade_date", self._today()),
                    trade.get("symbol", ""),
                    trade.get("sector", ""),
                    trade.get("industry", ""),
                    trade.get("theme", ""),
                    trade.get("entry_time", ""),
                    trade.get("exit_time", ""),
                    trade.get("exit_reason", ""),
                    trade.get("conviction", 0),
                    trade.get("pnl", 0),
                ),
            )
            self.db.commit()

    # --------------------------------------------------

    def symbol_trade_stats(self, symbol, limit=100):
        with self._lock:
            self.cursor.execute(
                """
                SELECT pnl, exit_reason
                FROM trade_outcomes
                WHERE symbol = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (symbol, limit),
            )
            rows = self.cursor.fetchall()

        total = len(rows)
        wins = sum(1 for r in rows if (r[0] or 0) > 0)

        return {
            "symbol": symbol,
            "trades": total,
            "wins": wins,
            "losses": total - wins,
            "win_rate": round(wins / total * 100, 1) if total else None,
            "total_pnl": round(sum(r[0] or 0 for r in rows), 2),
        }

    # --------------------------------------------------

    def sector_trade_stats(self, sector, limit=200):
        with self._lock:
            self.cursor.execute(
                """
                SELECT pnl
                FROM trade_outcomes
                WHERE sector = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (sector, limit),
            )
            rows = self.cursor.fetchall()

        total = len(rows)
        wins = sum(1 for r in rows if (r[0] or 0) > 0)

        return {
            "sector": sector,
            "trades": total,
            "win_rate": round(wins / total * 100, 1) if total else None,
            "total_pnl": round(sum(r[0] or 0 for r in rows), 2),
        }

    # --------------------------------------------------
    # Sector Leadership Days
    # --------------------------------------------------

    def save_sector_day(self, sector, rank, score):
        with self._lock:
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO sector_days(
                    trade_date, sector, rank, score
                )
                VALUES(?,?,?,?)
                """,
                (self._today(), sector, rank, score),
            )
            self.db.commit()

    # --------------------------------------------------

    def sector_leadership_streak(self, sector, top_n=3):
        """
        How many consecutive recorded days this sector
        has ranked in the top N.
        """
        with self._lock:
            self.cursor.execute(
                """
                SELECT trade_date, rank
                FROM sector_days
                WHERE sector = ?
                ORDER BY trade_date DESC
                LIMIT 30
                """,
                (sector,),
            )
            rows = self.cursor.fetchall()

        streak = 0
        for _, rank in rows:
            if rank is not None and rank <= top_n:
                streak += 1
            else:
                break

        return streak

    # --------------------------------------------------
    # Company Events
    # --------------------------------------------------

    def save_company_event(
        self,
        symbol,
        event_type,
        headline="",
        source="",
        payload=None,
    ):
        with self._lock:
            self.cursor.execute(
                """
                INSERT INTO company_events(
                    created_at, trade_date, symbol,
                    event_type, headline, source, payload
                )
                VALUES(?,?,?,?,?,?,?)
                """,
                (
                    self._now(),
                    self._today(),
                    symbol,
                    event_type,
                    headline,
                    source,
                    json.dumps(payload or {}, default=str),
                ),
            )
            self.db.commit()

    # --------------------------------------------------

    def company_events(self, symbol, limit=50):
        with self._lock:
            self.cursor.execute(
                """
                SELECT created_at, event_type,
                       headline, source
                FROM company_events
                WHERE symbol = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (symbol, limit),
            )
            rows = self.cursor.fetchall()

        return [
            {
                "created_at": row[0],
                "event_type": row[1],
                "headline": row[2],
                "source": row[3],
            }
            for row in rows
        ]

    # --------------------------------------------------
    # Structured Events (Event Intelligence)
    # --------------------------------------------------

    def save_structured_event(self, event):
        """
        event: dict with the structured_events columns.
        One row per (event, symbol).
        """
        with self._lock:
            self.cursor.execute(
                """
                INSERT INTO structured_events(
                    created_at, trade_date, event_type,
                    catalyst, symbol, sector, industry,
                    theme, direction, importance, severity,
                    confidence, horizon, headline, story_id,
                    realized_move, prior_move
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    self._now(),
                    self._today(),
                    event.get("event_type", ""),
                    event.get("catalyst", ""),
                    event.get("symbol", ""),
                    event.get("sector", ""),
                    event.get("industry", ""),
                    event.get("theme", ""),
                    event.get("direction", ""),
                    event.get("importance", 0),
                    event.get("severity", 0),
                    event.get("confidence", 0),
                    event.get("horizon", ""),
                    event.get("headline", ""),
                    event.get("story_id", ""),
                    None,
                    event.get("prior_move"),
                ),
            )
            self.db.commit()

    # --------------------------------------------------

    def symbol_structured_events(self, symbol, limit=20):
        with self._lock:
            self.cursor.execute(
                """
                SELECT created_at, event_type, catalyst,
                       direction, importance, confidence,
                       horizon, headline, prior_move
                FROM structured_events
                WHERE symbol = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (symbol, limit),
            )
            rows = self.cursor.fetchall()

        return [
            {
                "created_at": r[0],
                "event_type": r[1],
                "catalyst": r[2],
                "direction": r[3],
                "importance": r[4],
                "confidence": r[5],
                "horizon": r[6],
                "headline": r[7],
                "prior_move": r[8],
            }
            for r in rows
        ]

    # --------------------------------------------------

    def recent_structured_events(self, since_date, limit=200):
        """
        Events since a trade_date (inclusive) —
        used to rebuild the F&O watchlist on restart.
        """
        with self._lock:
            self.cursor.execute(
                """
                SELECT created_at, event_type, catalyst,
                       symbol, sector, theme, direction,
                       importance, confidence, horizon,
                       headline
                FROM structured_events
                WHERE trade_date >= ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (since_date, limit),
            )
            rows = self.cursor.fetchall()

        return [
            {
                "created_at": r[0],
                "event_type": r[1],
                "catalyst": r[2],
                "symbol": r[3],
                "sector": r[4],
                "theme": r[5],
                "direction": r[6],
                "importance": r[7],
                "confidence": r[8],
                "horizon": r[9],
                "headline": r[10],
            }
            for r in rows
        ]

    # --------------------------------------------------

    def event_type_history(self, event_type, limit=50):
        """
        Historical instances of one event type —
        the seed of 'what happened the last N times'.
        """
        with self._lock:
            self.cursor.execute(
                """
                SELECT trade_date, symbol, direction,
                       importance, realized_move
                FROM structured_events
                WHERE event_type = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (event_type, limit),
            )
            rows = self.cursor.fetchall()

        return [
            {
                "trade_date": r[0],
                "symbol": r[1],
                "direction": r[2],
                "importance": r[3],
                "realized_move": r[4],
            }
            for r in rows
        ]

    # --------------------------------------------------

    def write_event_outcomes(
        self,
        price_change_lookup,
        market_change=None
    ):
        """
        Outcome write-back: for today's structured
        events, record:
          • realized_move  = the symbol's raw day change
          • abnormal_move  = realized_move − market_change
            (the TRUE, market-adjusted event impact —
            the event-study measure and the input to the
            reaction-decay model)

        price_change_lookup(symbol) → % change or None.
        market_change → the market's avg day change %
            (e.g. breadth avg). If None, abnormal = raw.

        This is what turns event memory into PREDICTIVE
        memory.
        """
        updated = 0

        with self._lock:
            self.cursor.execute(
                """
                SELECT id, symbol
                FROM structured_events
                WHERE trade_date = ?
                  AND symbol != ''
                  AND realized_move IS NULL
                """,
                (self._today(),),
            )
            rows = self.cursor.fetchall()

        for event_id, symbol in rows:
            try:
                change = price_change_lookup(symbol)
            except Exception:
                change = None

            if change is None:
                continue

            change = round(float(change), 2)

            abnormal = change
            if market_change is not None:
                abnormal = round(
                    change - float(market_change), 2
                )

            with self._lock:
                self.cursor.execute(
                    """
                    UPDATE structured_events
                    SET realized_move = ?,
                        abnormal_move = ?
                    WHERE id = ?
                    """,
                    (change, abnormal, event_id),
                )
            updated += 1

        if updated:
            with self._lock:
                self.db.commit()

        return updated

    # --------------------------------------------------

    def event_type_abnormal_series(self, event_type, limit=60):
        """
        Chronological series of abnormal (market-adjusted)
        moves for one event type — OLDEST first. This is
        the raw input to the reaction-decay model:
        'is each successive shock of this type getting
        smaller as the market anticipates it?'
        """
        with self._lock:
            self.cursor.execute(
                """
                SELECT trade_date, symbol, direction,
                       abnormal_move
                FROM structured_events
                WHERE event_type = ?
                  AND abnormal_move IS NOT NULL
                ORDER BY id ASC
                LIMIT ?
                """,
                (event_type, limit),
            )
            rows = self.cursor.fetchall()

        return [
            {
                "trade_date": r[0],
                "symbol": r[1],
                "direction": r[2],
                "abnormal_move": r[3],
            }
            for r in rows
        ]

    # --------------------------------------------------

    def save_decision(
        self,
        symbol,
        action,
        reason,
        sector="",
        conviction=0,
        evidence="",
        pnl=None,
    ):
        """
        Permanent record of WHY every trade action was
        taken: ENTRY / EXIT / HOLD / REJECT / REPLACE.
        This is the memory that lets the bot explain
        itself and learn across 200+ days.
        """
        now = datetime.now()
        with self._lock:
            self.cursor.execute(
                """
                INSERT INTO trade_decisions(
                    created_at, trade_date, time, symbol,
                    action, sector, conviction, reason,
                    evidence, pnl
                )
                VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    self._now(),
                    self._today(),
                    now.strftime("%H:%M:%S"),
                    symbol,
                    action,
                    sector,
                    conviction or 0,
                    str(reason)[:500],
                    str(evidence)[:1000],
                    pnl,
                ),
            )
            self.db.commit()

    # --------------------------------------------------

    def decisions_for_date(self, trade_date, limit=200):
        with self._lock:
            self.cursor.execute(
                """
                SELECT time, symbol, action, conviction,
                       reason, pnl
                FROM trade_decisions
                WHERE trade_date = ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (trade_date, limit),
            )
            rows = self.cursor.fetchall()

        return [
            {
                "time": r[0], "symbol": r[1],
                "action": r[2], "conviction": r[3],
                "reason": r[4], "pnl": r[5],
            }
            for r in rows
        ]

    # --------------------------------------------------

    def decisions_for_symbol(self, symbol, limit=50):
        with self._lock:
            self.cursor.execute(
                """
                SELECT trade_date, time, action,
                       conviction, reason, pnl
                FROM trade_decisions
                WHERE symbol = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (symbol, limit),
            )
            rows = self.cursor.fetchall()

        return [
            {
                "trade_date": r[0], "time": r[1],
                "action": r[2], "conviction": r[3],
                "reason": r[4], "pnl": r[5],
            }
            for r in rows
        ]

    # --------------------------------------------------

    def decision_counts(self, days_back=200):
        """Action tally over recent history (learning stats)."""
        with self._lock:
            self.cursor.execute(
                """
                SELECT action, COUNT(*),
                       COALESCE(SUM(pnl),0)
                FROM trade_decisions
                GROUP BY action
                ORDER BY COUNT(*) DESC
                """
            )
            rows = self.cursor.fetchall()

        return [
            {"action": r[0], "count": r[1],
             "pnl": round(r[2], 2)}
            for r in rows
        ]

    # --------------------------------------------------

    def known_event_types(self, min_samples=3):
        """
        Event types with enough graded abnormal moves to
        model reaction decay.
        """
        with self._lock:
            self.cursor.execute(
                """
                SELECT event_type, COUNT(*)
                FROM structured_events
                WHERE abnormal_move IS NOT NULL
                GROUP BY event_type
                HAVING COUNT(*) >= ?
                ORDER BY COUNT(*) DESC
                """,
                (min_samples,),
            )
            return [
                {"event_type": r[0], "samples": r[1]}
                for r in self.cursor.fetchall()
            ]

    # --------------------------------------------------

    def event_type_reaction_stats(self, event_type):
        """
        Historical reaction distribution for one event
        type: what actually happened after similar
        events.
        """
        with self._lock:
            self.cursor.execute(
                """
                SELECT realized_move
                FROM structured_events
                WHERE event_type = ?
                  AND realized_move IS NOT NULL
                """,
                (event_type,),
            )
            moves = [r[0] for r in self.cursor.fetchall()]

        if not moves:
            return {
                "event_type": event_type,
                "samples": 0,
            }

        n = len(moves)
        mean = sum(moves) / n
        variance = sum(
            (m - mean) ** 2 for m in moves
        ) / n

        return {
            "event_type": event_type,
            "samples": n,
            "avg_move": round(mean, 2),
            "std_move": round(variance ** 0.5, 2),
            "positive_rate": round(
                sum(1 for m in moves if m > 0) / n * 100, 1
            ),
        }

    # --------------------------------------------------

    def company_event_type_counts(self, symbol):
        with self._lock:
            self.cursor.execute(
                """
                SELECT event_type, COUNT(*)
                FROM structured_events
                WHERE symbol = ?
                GROUP BY event_type
                ORDER BY COUNT(*) DESC
                """,
                (symbol,),
            )
            rows = self.cursor.fetchall()

        return {r[0]: r[1] for r in rows}

    # --------------------------------------------------
    # Learning : Conviction Calibration
    # --------------------------------------------------

    CALIBRATION_BANDS = (
        (0, 40),
        (40, 55),
        (55, 70),
        (70, 85),
        (85, 101),
    )

    def calibration_report(self):
        """
        Conviction band vs. realized outcome.
        The honest measure of whether conviction
        MEANS anything — institutional self-audit.
        """
        with self._lock:
            self.cursor.execute(
                "SELECT conviction, pnl FROM trade_outcomes"
            )
            rows = self.cursor.fetchall()

        report = []

        for low, high in self.CALIBRATION_BANDS:
            band = [
                r for r in rows
                if r[0] is not None and low <= r[0] < high
            ]
            total = len(band)
            wins = sum(1 for r in band if (r[1] or 0) > 0)

            report.append({
                "band": f"{low}-{high - 1 if high <= 100 else 100}",
                "trades": total,
                "wins": wins,
                "win_rate": (
                    round(wins / total * 100, 1)
                    if total else None
                ),
                "total_pnl": round(
                    sum(r[1] or 0 for r in band), 2
                ),
            })

        return report

    # --------------------------------------------------

    def top_sector_streaks(self, top_n=3, limit=10):
        """
        Sectors currently on top-N leadership streaks.
        """
        with self._lock:
            self.cursor.execute(
                "SELECT DISTINCT sector FROM sector_days"
            )
            sectors = [r[0] for r in self.cursor.fetchall()]

        streaks = []
        for sector in sectors:
            streak = self.sector_leadership_streak(
                sector, top_n
            )
            if streak > 0:
                streaks.append(
                    {"sector": sector, "streak": streak}
                )

        streaks.sort(
            key=lambda s: s["streak"], reverse=True
        )
        return streaks[:limit]

    # --------------------------------------------------

    def close(self):
        with self._lock:
            self.db.close()
