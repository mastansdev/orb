"""
Market Memory

Responsibilities
----------------
Maintain a historical memory of market catalysts.

Owns:
    • Catalyst Timeline
    • Active Catalysts
    • Historical Memory
    • Catalyst Statistics

Does NOT:
    • Collect News
    • Classify News
    • Calculate Impact
    • Determine Market Environment
    • Trigger Trades
    • Execute Orders

Consumes ImpactResult objects produced by ImpactEngine.

This module is the persistent memory layer of the
Market Intelligence pipeline.
"""

from copy import deepcopy
from datetime import datetime
from news.news_models import ImpactResult
from repositories.memory_repository import MemoryRepository


class MarketMemory:

    def __init__(self, repository=None):
        # Persistent memory (survives restarts).
        # Falls back to in-memory-only mode if the
        # local database cannot be opened.
        if repository is not None:
            self.repository = repository
        else:
            try:
                self.repository = MemoryRepository()
            except Exception as e:
                print(f"[MEMORY] Persistence unavailable: {e}")
                self.repository = None

        self.reset()

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def reset(self):
        self._history = []
        self._active = {}
        self._remembered = 0
        self._forgotten = 0
        self._expired = 0

    # --------------------------------------------------
    # Remember
    # --------------------------------------------------

    def remember(
        self,
        impact: ImpactResult
    ):
        impact = deepcopy(impact)
        rule = impact.rule_name
        
        if not rule or rule == "UNKNOWN":
            return False

        event = {
            "timestamp": datetime.now(),
            "rule": impact.rule_name,
            "category": impact.category,
            "sub_category": impact.subcategory,
            "event_type": impact.event_type,
            "market_regime": impact.market_regime_hint,
            "market_impact": impact.market_impact,
            "market_score": impact.market_score,
            "confidence": impact.confidence,
            "confidence_source": impact.confidence_source,
            "active": True,
        }

        self._history.append(event)
        self._active[rule] = event
        self._remembered += 1

        # ---------------------------------
        # Persist to institutional memory
        # ---------------------------------
        if self.repository is not None:
            try:
                self.repository.save_market_event(event)
            except Exception as e:
                print(f"[MEMORY] Persist failed: {e}")

        return True

    # --------------------------------------------------
    # Historical Recall
    # --------------------------------------------------

    def similar_events(self, rule, limit=20):
        """
        'This catalyst has occurred before — what happened?'
        Returns previous occurrences of the same rule from
        persistent memory.
        """
        if self.repository is None:
            return []

        try:
            return self.repository.similar_market_events(
                rule,
                limit
            )
        except Exception:
            return []

    # --------------------------------------------------
    # ORB Outcome Memory
    # --------------------------------------------------

    def record_orb_outcome(self, symbol, sector, outcome, pnl=0.0):
        """
        outcome: 'SUCCESS' (target) or 'FAILED' (stoploss)
        """
        if self.repository is None:
            return

        try:
            self.repository.save_orb_outcome(
                symbol,
                sector,
                outcome,
                pnl
            )
        except Exception as e:
            print(f"[MEMORY] ORB outcome persist failed: {e}")

    # --------------------------------------------------

    def orb_failures_today(self, symbol):
        if self.repository is None:
            return 0

        try:
            return self.repository.orb_failures_today(symbol)
        except Exception:
            return 0

    # --------------------------------------------------

    def orb_stats(self, symbol):
        if self.repository is None:
            return {"symbol": symbol, "samples": 0}

        try:
            return self.repository.orb_stats(symbol)
        except Exception:
            return {"symbol": symbol, "samples": 0}

    # --------------------------------------------------
    # Trade Outcome Memory
    # --------------------------------------------------

    def record_trade_outcome(self, trade):
        if self.repository is None:
            return

        try:
            self.repository.save_trade_outcome(trade)
        except Exception as e:
            print(f"[MEMORY] Trade outcome persist failed: {e}")

    # --------------------------------------------------

    def symbol_trade_stats(self, symbol):
        if self.repository is None:
            return {"symbol": symbol, "trades": 0}

        try:
            return self.repository.symbol_trade_stats(symbol)
        except Exception:
            return {"symbol": symbol, "trades": 0}

    # --------------------------------------------------
    # Sector Leadership Memory
    # --------------------------------------------------

    def record_sector_day(self, sector, rank, score):
        if self.repository is None:
            return

        try:
            self.repository.save_sector_day(sector, rank, score)
        except Exception:
            pass

    # --------------------------------------------------

    def sector_leadership_streak(self, sector, top_n=3):
        if self.repository is None:
            return 0

        try:
            return self.repository.sector_leadership_streak(
                sector,
                top_n
            )
        except Exception:
            return 0

    # --------------------------------------------------
    # Forget
    # --------------------------------------------------

    def forget(
        self,
        rule: str
    ):
        event = self._active.pop(rule, None)

        if event is None:
            return False

        event["active"] = False
        self._forgotten += 1

        return True

    # --------------------------------------------------
    # Expire
    # --------------------------------------------------

    def expire(
        self,
        rule: str
    ):
        event = self._active.pop(rule, None)

        if event is None:
            return False

        event["active"] = False
        self._expired += 1

        return True

    # --------------------------------------------------
    # Read Only
    # --------------------------------------------------

    def active(self):
        return deepcopy(self._active)

    # --------------------------------------------------

    def history(self):
        return deepcopy(self._history)

    # --------------------------------------------------

    def active_rules(self):
        return list(self._active.keys())

    # --------------------------------------------------

    def is_active(
        self,
        rule: str
    ) -> bool:
        return rule in self._active

    # --------------------------------------------------
    # Snapshot
    # --------------------------------------------------

    def get_snapshot(self) -> dict:
        """
        Return a read-only snapshot for
        IntelligenceEngine.
        """

        return {

            "active": deepcopy(self._active),

            "active_rules": self.active_rules(),

            "history_count": len(self._history),

            "remembered": self._remembered,
        }

    # --------------------------------------------------

    def stats(self):
        return {
            "remembered": self._remembered,
            "active": len(self._active),
            "forgotten": self._forgotten,
            "expired": self._expired,
            "history": len(self._history),
        }