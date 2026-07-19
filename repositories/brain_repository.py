from datetime import datetime
from repositories.database import Database


class BrainRepository:

    def __init__(self):
        self.db = Database().connection
        self.cursor = self.db.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS brain_decisions(
            id SERIAL PRIMARY KEY,
            created_at TEXT,
            symbol TEXT,
            action TEXT,
            confidence REAL,
            score REAL
        )
        """)
        self.db.commit()

    # --------------------------------------------------
    def save_decision(self, decision):
        self.cursor.execute(
            """
            INSERT INTO brain_decisions(
                created_at,
                symbol,
                action,
                confidence,
                score
            )
            VALUES(%s, %s, %s, %s, %s)
            """,
            (
                datetime.now().isoformat(),
                getattr(decision, "symbol", ""),
                getattr(
                    getattr(decision, "action", None),
                    "name",
                    str(getattr(decision, "action", ""))
                ),
                getattr(decision, "confidence", 0),
                getattr(decision, "score", 0),
            )
        )
        self.db.commit()

    # --------------------------------------------------
    def load_decisions(self):
        self.cursor.execute(
            """
            SELECT *
            FROM brain_decisions
            ORDER BY id DESC
            """
        )
        return self.cursor.fetchall()