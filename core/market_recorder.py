"""
==========================================================
Market Recorder
==========================================================

Mission
-------
Continuously record market and portfolio state so every
trading session can be replayed later.

This module NEVER:
- Executes trades
- Generates signals
- Makes decisions
- Blocks execution

Author : H&M ORB AUTO TRADER
==========================================================
"""

import sqlite3
import time
from datetime import datetime
from threading import Lock


class MarketRecorder:

    def __init__(self, interval_seconds=1):
        self.lock = Lock()
        self.snapshot_count = 0
        self.session_id = None
        
        # Configuration for recording intervals
        self.interval_seconds = interval_seconds
        self.last_record_time = 0

        self.db = sqlite3.connect(
            "market_recorder.db",
            check_same_thread=False
        )

        # Performance Optimizations
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=NORMAL")
        self.db.execute("PRAGMA temp_store=MEMORY")

        self.cursor = self.db.cursor()
        self._create_tables()
        self._start_session()

    # --------------------------------------------------

    def _create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions(
            session_id TEXT PRIMARY KEY,
            trade_date TEXT,
            start_time TEXT,
            end_time TEXT
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_snapshots(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            timestamp TEXT,
            floating_mtm REAL,
            realized_pnl REAL,
            net_pnl REAL,
            open_positions INTEGER,
            capital_used REAL,
            available_capital REAL
        )
        """)
        self.db.commit()

    # --------------------------------------------------

    def _start_session(self):
        now = datetime.now()
        self.session_id = now.strftime("%Y%m%d_%H%M%S")

        self.cursor.execute(
            """
            INSERT INTO sessions
            VALUES(?,?,?,?)
            """,
            (
                self.session_id,
                now.strftime("%Y-%m-%d"),
                now.strftime("%H:%M:%S"),
                None
            )
        )
        self.db.commit()

    # --------------------------------------------------

    def record(
        self,
        floating_mtm,
        realized_pnl,
        net_pnl,
        open_positions,
        capital_used,
        available_capital
    ):
        with self.lock:
            # Thread-safe interval throttling
            current_time = time.time()
            if (current_time - self.last_record_time < self.interval_seconds):
                return
            self.last_record_time = current_time

            timestamp = datetime.now().strftime("%H:%M:%S")

            self.cursor.execute(
                """
                INSERT INTO portfolio_snapshots(
                    session_id,
                    timestamp,
                    floating_mtm,
                    realized_pnl,
                    net_pnl,
                    open_positions,
                    capital_used,
                    available_capital
                )
                VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    self.session_id,
                    timestamp,
                    floating_mtm,
                    realized_pnl,
                    net_pnl,
                    open_positions,
                    capital_used,
                    available_capital
                )
            )

            self.snapshot_count += 1

            if self.snapshot_count % 25 == 0:
                self.db.commit()

    # --------------------------------------------------

    def end_session(self):
        with self.lock:
            self.cursor.execute(
                """
                UPDATE sessions
                SET end_time=?
                WHERE session_id=?
                """,
                (
                    datetime.now().strftime("%H:%M:%S"),
                    self.session_id
                )
            )
            self.db.commit()

    # --------------------------------------------------

    def flush(self):
        with self.lock:
            self.db.commit()

    # --------------------------------------------------

    def health(self):
        return {
            "session_id": self.session_id,
            "snapshots": self.snapshot_count,
            "interval": self.interval_seconds,
            "database": "CONNECTED"
        }

    # --------------------------------------------------

    def close(self):
        try:
            self.flush()
            self.end_session()
        finally:
            self.db.close()