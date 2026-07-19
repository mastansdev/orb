"""
==========================================================
F&O Opportunity Engine
==========================================================

Mission
-------
The primary execution universe is NSE F&O stocks.

When Event Intelligence detects a high-conviction
institutional catalyst on an F&O name, this engine
places it on a live CATALYST WATCHLIST with an expiry.

While a symbol is on the watchlist:
    • it carries positive FNO_CATALYST evidence into
      trade selection (catalyst-backed breakouts
      outrank naked breakouts)
    • it is visible to the operator via /fno

The watchlist is rebuilt from persistent event memory
on restart — a catalyst from this morning survives a
bot restart.

This engine NEVER:
    • places orders
    • sizes positions
    • overrides the Risk Governor

Author : H&M ORB AUTO TRADER
==========================================================
"""

from datetime import datetime, timedelta

from intelligence.evidence import Evidence


class FnOOpportunityEngine:

    # Minimum event importance to join the watchlist
    MIN_IMPORTANCE = 40

    # Watchlist entry lifetime by horizon hint
    HORIZON_HOURS = {
        "INTRADAY": 6,
        "SHORT": 24,
        "MEDIUM": 72,
        "LONG": 120,
    }
    DEFAULT_HOURS = 24

    def __init__(self, company_intelligence, repository=None):
        self.company_intelligence = company_intelligence
        self.repository = repository

        # symbol → watchlist entry
        self.watchlist = {}

        self._rebuild_from_memory()

    # --------------------------------------------------
    # F&O Universe
    # --------------------------------------------------

    def is_fno(self, symbol):
        try:
            profile = self.company_intelligence.get_profile(
                symbol
            )
            return str(
                profile.get("fno", "")
            ).strip().upper() in ("YES", "Y", "TRUE", "1", "FNO")
        except Exception:
            return False

    # --------------------------------------------------
    # Ingest
    # --------------------------------------------------

    def ingest_event(self, event):
        """
        Called by the engine for every structured event.
        Adds F&O symbols with material catalysts to the
        watchlist.
        """
        symbol = event.get("symbol", "")

        if not symbol:
            return False

        importance = float(event.get("importance", 0) or 0)

        if importance < self.MIN_IMPORTANCE:
            return False

        if not self.is_fno(symbol):
            return False

        direction = str(event.get("direction", "")).upper()

        expires_at = datetime.now() + timedelta(
            hours=self._lifetime_hours(
                event.get("horizon", "")
            )
        )

        existing = self.watchlist.get(symbol)

        # Keep the strongest catalyst per symbol
        if existing and existing["importance"] >= importance:
            existing["expires_at"] = max(
                existing["expires_at"], expires_at
            )
            return True

        self.watchlist[symbol] = {
            "symbol": symbol,
            "catalyst": event.get("catalyst", ""),
            "event_type": event.get("event_type", ""),
            "headline": event.get("headline", "")[:120],
            "direction": direction,
            "prior_move": event.get("prior_move"),
            "importance": importance,
            "confidence": float(
                event.get("confidence", 0) or 0
            ),
            "added_at": datetime.now(),
            "expires_at": expires_at,
        }

        print(
            f"[FNO] Watchlist add: {symbol} "
            f"({event.get('event_type', '?')}, "
            f"imp {importance})"
        )

        return True

    # --------------------------------------------------

    def _lifetime_hours(self, horizon):
        horizon = str(horizon or "").upper()

        for key, hours in self.HORIZON_HOURS.items():
            if key in horizon:
                return hours

        return self.DEFAULT_HOURS

    # --------------------------------------------------

    def _rebuild_from_memory(self):
        """
        Restore the watchlist from the last 2 days of
        persisted structured events (restart safety).
        """
        if self.repository is None:
            return

        try:
            since = (
                datetime.now() - timedelta(days=2)
            ).strftime("%Y-%m-%d")

            events = self.repository.recent_structured_events(
                since
            )

            for event in events:
                self.ingest_event(event)

            if self.watchlist:
                print(
                    f"[FNO] Watchlist rebuilt: "
                    f"{len(self.watchlist)} symbol(s)"
                )

        except Exception as e:
            print(f"[FNO] Rebuild failed: {e}")

    # --------------------------------------------------
    # Expiry
    # --------------------------------------------------

    def _prune(self):
        now = datetime.now()

        expired = [
            symbol
            for symbol, entry in self.watchlist.items()
            if entry["expires_at"] <= now
        ]

        for symbol in expired:
            del self.watchlist[symbol]

    # --------------------------------------------------
    # Evidence
    # --------------------------------------------------

    def build_evidence(self, symbol):
        """
        FNO_CATALYST evidence when a live catalyst
        exists for this symbol.
        """
        self._prune()

        entry = self.watchlist.get(symbol)

        if entry is None:
            return []

        direction = entry.get("direction", "")

        if direction in (
            "WEAKENING", "CONTRADICTED", "NEGATIVE"
        ):
            recommendation = "SELL"
        else:
            recommendation = "BUY"

        return [
            Evidence(
                provider="FNO_CATALYST",
                symbol=symbol,
                recommendation=recommendation,
                score=min(100.0, entry["importance"]),
                confidence=min(95.0, entry["confidence"]),
                reason=(
                    f"Live F&O catalyst: "
                    f"{entry.get('event_type', '?')} — "
                    f"{entry.get('headline', '')[:70]}"
                ),
                facts={
                    "catalyst": entry.get("catalyst"),
                    "event_type": entry.get("event_type"),
                    "importance": entry["importance"],
                    "expires_at": str(entry["expires_at"]),
                },
            )
        ]

    # --------------------------------------------------
    # Reports
    # --------------------------------------------------

    def get_watchlist(self):
        self._prune()

        return sorted(
            self.watchlist.values(),
            key=lambda e: e["importance"],
            reverse=True,
        )

    # --------------------------------------------------

    def report(self, limit=10):
        entries = self.get_watchlist()

        if not entries:
            return (
                "F&O CATALYST WATCHLIST\n\n"
                "No live catalysts."
            )

        lines = ["F&O CATALYST WATCHLIST", ""]

        for i, entry in enumerate(entries[:limit], start=1):
            lines.append(
                f"{i:02d}. {entry['symbol']:<12} "
                f"imp {entry['importance']:.0f} "
                f"({entry.get('event_type', '?')})"
            )
            lines.append(
                f"    {entry.get('headline', '')[:70]}"
            )

        return "\n".join(lines)
