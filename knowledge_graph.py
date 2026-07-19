"""
==========================================================
Knowledge Graph
==========================================================

Mission
-------
Connect everything: the relationship layer that lets a
catalyst on one company propagate to its peers,
suppliers, customers, and theme members with WEIGHTS —
so the Brain understands second-order effects instead
of isolated news.

Edge model
----------
{src, dst, edge_type, weight (0-1 materiality),
 confidence, source, last_verified}

Edge sources
------------
1. Seeded from the Master Database:
       company —[member_of]→ sector/industry/theme
       company —[competitor_of]→ industry peers
2. Curated from Masterdata/graph_edges.csv:
       SRC,DST,TYPE,WEIGHT
       (supplier_of / customer_of / subsidiary_of /
        competitor_of — operator- or research-added)
3. Persisted in institutional memory (graph_edges
   table) so learned/curated edges survive restarts.

Propagation
-----------
Event on X → routing table by event class → damped,
weighted spillover to neighbors → SYMPATHY evidence.
Max depth 2. Materiality floor. Paths kept as
explanations.

This module NEVER:
    • trades
    • fetches data over the network

Author : H&M ORB AUTO TRADER
==========================================================
"""

import csv
import os
from datetime import datetime

from evidence import Evidence


class KnowledgeGraph:

    CSV_FILE = os.path.join("Masterdata", "graph_edges.csv")

    # Event-class → which edge types transmit, with sign
    # (+1 sympathy, -1 inverse) and damping multiplier.
    ROUTING = {
        "ORDER_WIN": [
            ("competitor_of", -1, 0.30),
            ("supplier_of", +1, 0.40),
            ("theme_member", +1, 0.25),
        ],
        "ORDER_LOSS": [
            ("competitor_of", +1, 0.30),
            ("supplier_of", -1, 0.40),
        ],
        "RESULTS_BEAT": [
            ("competitor_of", +1, 0.35),
            ("industry_peer", +1, 0.35),
        ],
        "RESULTS_MISS": [
            ("competitor_of", -1, 0.35),
            ("industry_peer", -1, 0.35),
        ],
        "POLICY": [
            ("theme_member", +1, 0.50),
            ("industry_peer", +1, 0.40),
        ],
        "REGULATORY_ACTION": [
            ("industry_peer", -1, 0.30),
            ("subsidiary_of", -1, 0.60),
        ],
        # Default for unknown event types
        "*": [
            ("theme_member", +1, 0.20),
            ("industry_peer", +1, 0.20),
        ],
    }

    # Spillover below this floor is noise, not signal
    MATERIALITY_FLOOR = 15.0

    def __init__(self, company_intelligence, repository=None):
        self.company_intelligence = company_intelligence
        self.repository = repository

        # adjacency: src → list of (dst, edge_type, weight)
        self.edges = {}
        self.edge_count = 0

        self._ensure_table()
        self._seed_from_master()
        self._load_curated()

    # --------------------------------------------------
    # Storage
    # --------------------------------------------------

    def _ensure_table(self):
        if self.repository is None:
            return

        try:
            with self.repository._lock:
                self.repository.cursor.execute("""
                CREATE TABLE IF NOT EXISTS graph_edges(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    src TEXT,
                    dst TEXT,
                    edge_type TEXT,
                    weight REAL,
                    confidence REAL,
                    source TEXT,
                    last_verified TEXT,
                    UNIQUE(src, dst, edge_type)
                )
                """)
                self.repository.db.commit()
        except Exception as e:
            print(f"[GRAPH] Table init failed: {e}")

    # --------------------------------------------------

    def add_edge(
        self,
        src,
        dst,
        edge_type,
        weight=0.5,
        confidence=70,
        source="SEED",
        persist=False,
    ):
        src = str(src).upper()
        dst = str(dst).upper()

        if not src or not dst or src == dst:
            return False

        self.edges.setdefault(src, [])

        # Replace existing same-type edge
        self.edges[src] = [
            e for e in self.edges[src]
            if not (e[0] == dst and e[1] == edge_type)
        ]

        self.edges[src].append((dst, edge_type, weight))
        self.edge_count += 1

        if persist and self.repository is not None:
            try:
                with self.repository._lock:
                    self.repository.cursor.execute(
                        """
                        INSERT OR REPLACE INTO graph_edges(
                            src, dst, edge_type, weight,
                            confidence, source, last_verified
                        )
                        VALUES(?,?,?,?,?,?,?)
                        """,
                        (
                            src, dst, edge_type, weight,
                            confidence, source,
                            datetime.now().strftime(
                                "%Y-%m-%d"
                            ),
                        ),
                    )
                    self.repository.db.commit()
            except Exception:
                pass

        return True

    # --------------------------------------------------
    # Seeding
    # --------------------------------------------------

    def _seed_from_master(self):
        """
        Build industry-peer and theme-member edges from
        company profiles. Peer weight shrinks with group
        size: a 3-company industry is tightly coupled; a
        40-company industry is loosely coupled.
        """
        profiles = self.company_intelligence.profiles

        if not profiles:
            return

        industries = {}
        themes = {}

        for symbol, profile in profiles.items():
            industry = profile.get("industry", "")
            if industry:
                industries.setdefault(
                    industry, []
                ).append(symbol)

            for theme in profile.get("themes", []):
                themes.setdefault(theme, []).append(symbol)

        # Industry peers → competitor-ish edges
        for industry, members in industries.items():
            if len(members) < 2 or len(members) > 40:
                continue

            weight = round(
                min(0.8, 2.0 / len(members)), 3
            )

            for a in members:
                for b in members:
                    if a != b:
                        self.add_edge(
                            a, b, "industry_peer", weight
                        )

        # Theme co-members (weaker)
        for theme, members in themes.items():
            if len(members) < 2 or len(members) > 30:
                continue

            weight = round(
                min(0.5, 1.5 / len(members)), 3
            )

            for a in members:
                for b in members:
                    if a != b:
                        self.add_edge(
                            a, b, "theme_member", weight
                        )

        print(
            f"[GRAPH] Seeded {self.edge_count} edges "
            f"({len(industries)} industries, "
            f"{len(themes)} themes)"
        )

    # --------------------------------------------------

    def _load_curated(self):
        """
        Curated high-value edges (suppliers, customers,
        subsidiaries) from DB + CSV. These carry real
        economic weights and beat seeded edges.
        """
        # From DB
        if self.repository is not None:
            try:
                with self.repository._lock:
                    self.repository.cursor.execute(
                        "SELECT src, dst, edge_type, weight "
                        "FROM graph_edges"
                    )
                    rows = self.repository.cursor.fetchall()

                for src, dst, edge_type, weight in rows:
                    self.add_edge(src, dst, edge_type, weight)

            except Exception:
                pass

        # From CSV
        if not os.path.exists(self.CSV_FILE):
            return

        loaded = 0
        try:
            with open(
                self.CSV_FILE, newline="", encoding="utf-8"
            ) as f:
                for row in csv.reader(f):
                    # Per-row safety: comments, headers,
                    # malformed rows never abort the load
                    try:
                        if (
                            len(row) < 3
                            or row[0].strip().startswith("#")
                            or row[0].strip().upper() == "SRC"
                        ):
                            continue

                        weight = (
                            float(row[3])
                            if len(row) > 3 else 0.5
                        )

                        if self.add_edge(
                            row[0].strip(),
                            row[1].strip(),
                            row[2].strip().lower(),
                            weight,
                            source="CURATED",
                            persist=True,
                        ):
                            loaded += 1

                    except (ValueError, IndexError):
                        continue

            if loaded:
                print(
                    f"[GRAPH] Loaded {loaded} curated edges"
                )

        except Exception as e:
            print(f"[GRAPH] CSV load failed: {e}")

    # --------------------------------------------------
    # Query
    # --------------------------------------------------

    def neighbors(self, symbol, edge_types=None):
        symbol = str(symbol).upper()

        result = []
        for dst, edge_type, weight in self.edges.get(
            symbol, []
        ):
            if edge_types and edge_type not in edge_types:
                continue
            result.append(
                {
                    "symbol": dst,
                    "edge_type": edge_type,
                    "weight": weight,
                }
            )

        result.sort(key=lambda e: -e["weight"])
        return result

    # --------------------------------------------------
    # Propagation
    # --------------------------------------------------

    def propagate(self, event):
        """
        One structured event → ranked spillover list:
        [{symbol, impact (signed 0-100), path, depth}]
        """
        origin = str(event.get("symbol", "")).upper()
        importance = float(event.get("importance", 0) or 0)
        event_type = str(
            event.get("event_type", "")
        ).upper()

        if not origin or importance <= 0:
            return []

        routes = self.ROUTING.get(
            event_type, self.ROUTING["*"]
        )

        spillovers = {}

        for dst, edge_type, weight in self.edges.get(
            origin, []
        ):
            for route_type, sign, damping in routes:
                if edge_type != route_type:
                    continue

                impact = importance * weight * damping * sign

                if abs(impact) < self.MATERIALITY_FLOOR:
                    continue

                existing = spillovers.get(dst)

                if (
                    existing is None
                    or abs(impact) > abs(existing["impact"])
                ):
                    spillovers[dst] = {
                        "symbol": dst,
                        "impact": round(impact, 1),
                        "path": (
                            f"{origin} —[{edge_type} "
                            f"w={weight}]→ {dst}"
                        ),
                        "depth": 1,
                        "event_type": event_type,
                    }

        result = sorted(
            spillovers.values(),
            key=lambda s: -abs(s["impact"]),
        )

        return result

    # --------------------------------------------------
    # Evidence
    # --------------------------------------------------

    def build_sympathy_evidence(self, symbol, spillovers):
        """
        SYMPATHY evidence for a candidate symbol from a
        precomputed spillover list.
        """
        symbol = str(symbol).upper()

        for spill in spillovers:
            if spill["symbol"] != symbol:
                continue

            impact = spill["impact"]

            return [
                Evidence(
                    provider="SYMPATHY",
                    symbol=symbol,
                    recommendation=(
                        "BUY" if impact > 0 else "SELL"
                    ),
                    score=min(100.0, abs(impact)),
                    confidence=60,
                    reason=(
                        f"Spillover: {spill['path']} "
                        f"({spill['event_type']})"
                    ),
                    facts=dict(spill),
                )
            ]

        return []

    # --------------------------------------------------

    def report(self, symbol):
        symbol = str(symbol).upper()

        neighbors = self.neighbors(symbol)

        if not neighbors:
            return (
                f"KNOWLEDGE GRAPH : {symbol}\n\n"
                "No edges. Add curated edges via\n"
                "Masterdata/graph_edges.csv "
                "(SRC,DST,TYPE,WEIGHT)"
            )

        lines = [
            f"KNOWLEDGE GRAPH : {symbol}",
            f"({len(neighbors)} connections)",
            "",
        ]

        by_type = {}
        for n in neighbors:
            by_type.setdefault(
                n["edge_type"], []
            ).append(n)

        for edge_type, items in by_type.items():
            lines.append(f"{edge_type}:")
            for n in items[:8]:
                lines.append(
                    f"• {n['symbol']} (w={n['weight']})"
                )
            lines.append("")

        return "\n".join(lines).strip()
