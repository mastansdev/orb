"""
==========================================================
News Watchlist  (active, rolling)
==========================================================

The counterpart to intelligence/results_watchlist.py, for
a different kind of catalyst: not a scheduled results date,
but a live news story that just broke on a stock.

    ACTIVE   — a MARKET_STORY-tagged story landed on this
               symbol within the freshness window (30 min,
               matching TradeSelectionEngine's existing
               news-evidence rolling cache). Shown on the
               dashboard / /newswatch as "currently in play".

    (expired) — falls out of ACTIVE once the freshness
               window passes; never marked as a separate
               state, just pruned, since there's nothing
               useful to say about a story that's gone cold
               beyond "it happened."

This module NEVER trades and NEVER decides direction on its
own -- it only tracks WHICH stocks currently have a live news
story attached, for visibility. The actual BUY/WAIT/SELL
lean still comes from the same MARKET_STORY evidence flowing
through ConvictionEngine elsewhere (trade_selection_engine.py).

Author : H&M ORB AUTO TRADER
==========================================================
"""

from datetime import datetime, timedelta


class NewsWatchlist:

    # Matches TradeSelectionEngine._news_evidence_cache's own
    # 30-minute rolling window -- a story stops being "live
    # news" for entry-evidence purposes at the same point it
    # should stop being shown as "in play" on the watchlist.
    FRESHNESS_MINUTES = 30

    def __init__(self):
        # symbol -> {"headline","direction","confidence",
        #            "priority","category","since"}
        self.entries = {}

    # --------------------------------------------------

    def on_story(self, symbol, story):
        """
        Called once per (story, affected symbol) pair --
        same fan-out as Brain.build_news_evidence(), so this
        watchlist only ever lights up for symbols the story
        actually named, never a blanket sector guess.
        """
        symbol = str(symbol).upper().strip()
        if not symbol:
            return

        self.entries[symbol] = {
            "headline": (getattr(story, "name", "") or "")[:150],
            "direction": str(
                getattr(story, "story_direction", "") or ""
            ).upper(),
            "confidence": float(
                getattr(story, "confidence", 0) or 0
            ),
            "priority": float(
                getattr(story, "priority", 0) or 0
            ),
            "category": str(
                getattr(story, "category", "") or ""
            ).upper(),
            "since": datetime.now(),
        }

    # --------------------------------------------------

    def _prune(self):
        cutoff = datetime.now() - timedelta(
            minutes=self.FRESHNESS_MINUTES
        )
        stale = [
            s for s, e in self.entries.items()
            if e["since"] < cutoff
        ]
        for s in stale:
            del self.entries[s]

    # --------------------------------------------------

    def active(self):
        """symbol -> entry dict, for all currently-live news."""
        self._prune()
        return dict(self.entries)

    # --------------------------------------------------

    def is_active(self, symbol):
        self._prune()
        return symbol.upper().strip() in self.entries

    # --------------------------------------------------

    def get(self, symbol):
        self._prune()
        return self.entries.get(symbol.upper().strip())

    # --------------------------------------------------

    def as_list(self, limit=50):
        """
        Dashboard-friendly serialization -- plain dicts with
        ISO timestamps, ranked by priority then recency.
        """
        self._prune()
        rows = [
            {
                "symbol": symbol,
                "headline": e["headline"],
                "direction": e["direction"],
                "confidence": round(e["confidence"], 1),
                "priority": round(e["priority"], 1),
                "category": e["category"],
                "since": e["since"].isoformat(),
            }
            for symbol, e in self.entries.items()
        ]
        rows.sort(
            key=lambda r: (r["priority"], r["since"]),
            reverse=True,
        )
        return rows[:limit]

    # --------------------------------------------------

    def report(self):
        self._prune()

        if not self.entries:
            return (
                "NEWS WATCHLIST (live, rolling 30-min)\n\n"
                "No active news catalysts right now."
            )

        ranked = sorted(
            self.entries.items(),
            key=lambda kv: (kv[1]["priority"], kv[1]["since"]),
            reverse=True,
        )

        lines = [
            "NEWS WATCHLIST (live, rolling 30-min)",
            "",
            f"🟢 ACTIVE: {len(ranked)}",
            "",
        ]
        for symbol, e in ranked[:25]:
            age_min = int(
                (datetime.now() - e["since"]).total_seconds() // 60
            )
            direction = f" [{e['direction']}]" if e["direction"] else ""
            lines.append(
                f"{symbol}{direction} — {age_min}m ago"
            )
            if e["headline"]:
                lines.append(f"   {e['headline'][:90]}")

        return "\n".join(lines)
