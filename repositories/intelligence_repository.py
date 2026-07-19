from datetime import datetime

from repositories.database import Database

from news.news_models import MarketStory

class IntelligenceRepository:

    def __init__(self):

        self.db = Database().connection

        self.cursor = self.db.cursor()
        self.last_read_id = 0

        self._create_tables()

    # --------------------------------------------------

    def _create_tables(self):

        self.cursor.execute(
        """

        CREATE TABLE IF NOT EXISTS market_stories(

            id SERIAL PRIMARY KEY,

            created_at TEXT,

            story_name TEXT,

            story_id TEXT,
                            
            category TEXT,
            
            subcategory TEXT,
                            
            event_type TEXT,

            catalyst TEXT,

            sector TEXT,

            industry TEXT,

            theme TEXT,

            confidence REAL,

            story_strength REAL,

            priority INTEGER,

            lifecycle TEXT,

            expected_duration TEXT,

            evidence_count INTEGER,

            contradiction_count INTEGER,

            updated_at TEXT,

            affected_symbols TEXT[]
        )

        """)

        self.db.commit()

        # Safe for both fresh installs (CREATE TABLE above already
        # includes the column) and the already-running Railway
        # database (this adds it without touching existing rows).
        self.cursor.execute(
        """
        ALTER TABLE market_stories
        ADD COLUMN IF NOT EXISTS affected_symbols TEXT[]
        """
        )

        self.db.commit()

        self.cursor.execute(
        """

        CREATE TABLE IF NOT EXISTS raw_news(

            id SERIAL PRIMARY KEY,

            news_hash TEXT UNIQUE,

            source TEXT,

            headline TEXT,

            published_at TEXT,

            url TEXT,

            processed BOOLEAN DEFAULT FALSE,

            created_at TEXT

        )

        """

        )

        self.db.commit()

    # --------------------------------------------------

    def save_story(
        self,
        story,
    ):

        self.cursor.execute(
            """

            INSERT INTO market_stories(

                created_at,

                story_name,

                story_id,

                category,

                subcategory,

                event_type,
                catalyst,
                sector,
                industry,
                theme,
                confidence,
                story_strength,
                priority,
                lifecycle,
                expected_duration,
                evidence_count,
                contradiction_count,
                updated_at,
                affected_symbols
                
            )

            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)

            """,

            (

                datetime.now().isoformat(),

                getattr(story, "name", ""),

                getattr(story, "story_id", ""),

                getattr(story, "category", ""),

                getattr(story, "subcategory", ""),
                
                getattr(story, "event_type", ""),
                getattr(story, "catalyst", ""),
                getattr(story, "sector", ""),
                getattr(story, "industry", ""),
                getattr(story, "theme", ""),
                getattr(story, "confidence", 0),
                getattr(story, "story_strength", 0),
                getattr(story, "priority", 0),
                getattr(story, "lifecycle", ""),
                getattr(story, "expected_duration", ""),
                getattr(story, "evidence_count", 0),
                getattr(story, "contradiction_count", 0),
                getattr(story, "updated_at", datetime.now().isoformat()),
                list(getattr(story, "affected_symbols", []) or []),

            )

        )

        self.db.commit()

    # --------------------------------------------------

    def _row_to_story(
            self,
            row
    ):
        """
        Convert one database row into a
        MarketStory object.
        """
        return MarketStory(
            story_id=row[3],
            name=row[2],
            category=row[4],
            subcategory=row[5],
            event_type=row[6],
            catalyst=row[7],
            sector=row[8],
            industry=row[9],
            theme=row[10],

            confidence=row[11],
            story_strength=row[12],

            story_direction="UNKNOWN",

            priority=row[13],
            lifecycle=row[14],
            expected_duration=row[15],

            supporting_news=[],
            affected_symbols=list(row[19]) if len(row) > 19 and row[19] else [],
            leading_symbols=list(row[19]) if len(row) > 19 and row[19] else [],

            evidence_count=row[16],
            contradiction_count=row[17],

            created_at=row[1],
            updated_at=row[18],
    )

    # --------------------------------------------------

    def load_intelligence(self):

        self.cursor.execute("""

        SELECT *

        FROM market_stories

        ORDER BY id DESC

        """)

        return self.cursor.fetchall()
    
    # --------------------------------------------------

    def recent_stories(self, hours=48, limit=40):
        """
        Most recent market stories from the DB (regardless
        of session read-cursor) — the actual news currently
        'around the market'. Used by the pre-market brief.
        """
        try:
            self.cursor.execute(
                """
                SELECT *
                FROM market_stories
                ORDER BY id DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = self.cursor.fetchall()
            return [self._row_to_story(r) for r in rows]
        except Exception:
            return []

    # --------------------------------------------------

    def load_new_intelligence(self):

        self.cursor.execute(

            """

            SELECT *

            FROM market_stories

            WHERE id > %s

            ORDER BY id

            """,

            (

                self.last_read_id,

            )

        )

        rows = self.cursor.fetchall()

        if rows:

            self.last_read_id = rows[-1][0]
            
        stories = []

                 
        for row in rows:
            stories.append(
                self._row_to_story(row)
            )

        return stories

    # --------------------------------------------------

    def generate_news_hash(self, news):
        """
        Generate a stable unique hash for one news item.
        """
        import hashlib

        text = (
            f"{news.source.value}|"
            f"{news.headline.strip()}|"
            f"{news.published_at}"
        )

        return hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()

    # --------------------------------------------------

    def news_exists(self, news_hash):
        """
        Returns True if this news was already stored.
        """
        self.cursor.execute(
            """
            SELECT 1
            FROM raw_news
            WHERE news_hash=%s
            LIMIT 1
            """,
            (
                news_hash,
            )
        )
        return self.cursor.fetchone() is not None

    # --------------------------------------------------

    def save_raw_news(
        self,
        news,
        news_hash
    ):
        """
        Store raw news before any processing.
        """
        self.cursor.execute(
            """
            INSERT INTO raw_news(
                news_hash,
                source,
                headline,
                published_at,
                url,
                processed
            )
            VALUES(%s,%s,%s,%s,%s,%s)
            ON CONFLICT (news_hash)
            DO NOTHING
            """,
            (
                news_hash,
                news.source.value,
                news.headline,
                str(news.published_at),
                getattr(news, "url", ""),
                False,
            )
        )
        self.db.commit()