"""
==========================================================
Company Intelligence Engine
==========================================================

Mission
-------
Every company has a PERMANENT profile that grows over
time. When a symbol appears anywhere, the Brain should
already know the company.

Profile fields (v1)
-------------------
    • company name
    • core business
    • sector / industry / themes
    • keywords
    • fno / lot size
    • event history   (permanent, from MemoryRepository)
    • trade history   (what happened when WE traded it)
    • behavioral stats (ORB win rate etc.)

Growth path (documented, not yet populated):
    products, brands, plants, management, promoters,
    customers, suppliers, export/import exposure,
    geographic exposure, historical results,
    management commentary.
    These fields exist in the profile as empty
    containers so future collectors can fill them
    without schema changes.

Data sources
------------
    • Masterdata/master_database.xlsx  (static seed)
    • MemoryRepository                 (event history)
    • News stories                     (recorded as events)

This engine NEVER:
    • decides trades
    • scores conviction
    • executes anything

Author : H&M ORB AUTO TRADER
==========================================================
"""

import json
import re

from evidence import Evidence
from repositories.memory_repository import MemoryRepository


class CompanyIntelligence:

    MASTER_DATABASE = "Masterdata/master_database.xlsx"

    def __init__(self, repository=None):

        # Permanent event storage
        if repository is not None:
            self.repository = repository
        else:
            try:
                self.repository = MemoryRepository()
            except Exception as e:
                print(f"[COMPANY] Persistence unavailable: {e}")
                self.repository = None

        # Static profiles seeded from the master database
        self.profiles = {}

        self._seed_from_master()

    # --------------------------------------------------
    # Static Seed
    # --------------------------------------------------

    def _seed_from_master(self):
        """
        Load static company facts from the master
        database. Failure is non-fatal: profiles are
        then built lazily as empty shells.
        """
        try:
            import pandas as pd

            df = pd.read_excel(
                self.MASTER_DATABASE,
                dtype=str
            ).fillna("")

            df.columns = (
                df.columns
                .str.strip()
                .str.upper()
                .str.replace(r"\s+", " ", regex=True)
            )

            for _, row in df.iterrows():
                symbol = str(row.get("SYMBOL", "")).strip().upper()

                if not symbol:
                    continue

                themes = [
                    t.strip()
                    for t in re.split(
                        r"[|,]",
                        str(row.get("THEMES", ""))
                    )
                    if t.strip()
                ]

                keywords = [
                    k.strip().upper()
                    for k in re.split(
                        r"[|,]",
                        str(row.get("KEYWORDS", ""))
                    )
                    if k.strip()
                ]

                self.profiles[symbol] = self._empty_profile(
                    symbol
                )

                self.profiles[symbol].update({
                    "company_name": row.get("COMPANY NAME", ""),
                    "core_business": row.get("CORE BUSINESS", ""),
                    "sector": row.get("SECTOR", ""),
                    "industry": row.get("INDUSTRY", ""),
                    "themes": themes,
                    "keywords": keywords,
                    "fno": row.get("FNO", ""),
                    "lot_size": row.get("LOT SIZE", ""),
                })

            print(
                f"[COMPANY] Profiles seeded : "
                f"{len(self.profiles)}"
            )

        except Exception as e:
            print(f"[COMPANY] Master seed unavailable: {e}")

    # --------------------------------------------------

    @staticmethod
    def _empty_profile(symbol):
        return {
            "symbol": symbol,
            "company_name": "",
            "core_business": "",
            "sector": "",
            "industry": "",
            "themes": [],
            "keywords": [],
            "fno": "",
            "lot_size": "",

            # Future enrichment containers
            "products": [],
            "brands": [],
            "plants": [],
            "management": [],
            "promoters": [],
            "customers": [],
            "suppliers": [],
            "export_exposure": "",
            "import_exposure": "",
            "geographic_exposure": [],

            # Living intelligence (auto-evolving)
            "last_catalyst": "",
            "last_event_type": "",
            "last_event_at": "",
            "catalyst_count": 0,
            "profile_updated_at": "",
        }

    # --------------------------------------------------
    # PUBLIC : Profile Access
    # --------------------------------------------------

    def get_profile(self, symbol):
        symbol = symbol.upper()

        profile = self.profiles.get(symbol)

        if profile is None:
            profile = self._empty_profile(symbol)
            self.profiles[symbol] = profile

        return profile

    # --------------------------------------------------

    def get_full_profile(self, symbol):
        """
        Static profile + permanent event history +
        behavioral statistics. This is the 'company
        dossier' — precomputed knowledge, retrieved
        in milliseconds.
        """
        profile = dict(self.get_profile(symbol))

        if self.repository is not None:
            try:
                profile["recent_events"] = (
                    self.repository.company_events(symbol, 20)
                )
                profile["trade_stats"] = (
                    self.repository.symbol_trade_stats(symbol)
                )
                profile["orb_stats"] = (
                    self.repository.orb_stats(symbol)
                )
            except Exception:
                pass

        return profile

    # --------------------------------------------------
    # PUBLIC : Permanent Event Recording
    # --------------------------------------------------

    def record_event(
        self,
        symbol,
        event_type,
        headline="",
        source="",
        payload=None,
    ):
        if self.repository is None:
            return

        try:
            self.repository.save_company_event(
                symbol=symbol.upper(),
                event_type=event_type,
                headline=headline,
                source=source,
                payload=payload,
            )
        except Exception as e:
            print(f"[COMPANY] Event persist failed: {e}")

    # --------------------------------------------------

    def record_trade(self, symbol, exit_reason, pnl):
        self.record_event(
            symbol=symbol,
            event_type="TRADE",
            headline=(
                f"Trade closed ({exit_reason}) "
                f"PnL ₹{pnl:.2f}"
            ),
            source="ENGINE",
            payload={"exit_reason": exit_reason, "pnl": pnl},
        )

    # --------------------------------------------------

    def record_story(self, story):
        """
        Attach a news story to every company it
        mentions. Defensive: works with any story
        object shape.
        """
        # Bug fix: MarketStory's field is
        # affected_symbols, not symbols.
        symbols = (
            getattr(story, "affected_symbols", None)
            or getattr(story, "symbols", None)
            or []
        )

        if isinstance(symbols, str):
            symbols = [symbols]

        headline = (
            getattr(story, "name", "")
            or getattr(story, "headline", "")
        )

        for symbol in symbols:
            if symbol:
                self.record_event(
                    symbol=symbol,
                    event_type="NEWS",
                    headline=str(headline)[:300],
                    source="NEWS_ENGINE",
                    payload={
                        "sector": getattr(story, "sector", ""),
                        "theme": getattr(story, "theme", ""),
                        "confidence": getattr(
                            story, "confidence", 0
                        ),
                    },
                )

    # --------------------------------------------------
    # PUBLIC : Living Profile Evolution
    # --------------------------------------------------

    def update_from_event(self, event):
        """
        Called by Event Intelligence for every
        structured event — the profile EVOLVES with
        every new piece of information. Nothing
        remains static.
        """
        symbol = event.get("symbol", "")

        if not symbol:
            return

        profile = self.get_profile(symbol)

        from datetime import datetime

        profile["last_catalyst"] = (
            event.get("catalyst", "")
            or profile.get("last_catalyst", "")
        )
        profile["last_event_type"] = event.get(
            "event_type", ""
        )
        profile["last_event_at"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )
        profile["catalyst_count"] = (
            profile.get("catalyst_count", 0) + 1
        )
        profile["profile_updated_at"] = (
            profile["last_event_at"]
        )

    # --------------------------------------------------
    # PUBLIC : Evidence
    # --------------------------------------------------

    def build_evidence(self, symbol):
        """
        Company context as Evidence. v1 emits evidence
        only when the company has meaningful history.
        """
        if self.repository is None:
            return []

        try:
            stats = self.repository.symbol_trade_stats(symbol)
        except Exception:
            return []

        trades = stats.get("trades", 0)
        win_rate = stats.get("win_rate")

        if trades < 5 or win_rate is None:
            return []

        if win_rate >= 60:
            recommendation = "BUY"
            reason = (
                f"Our own history with {symbol}: "
                f"{win_rate}% win rate over {trades} trades"
            )
        elif win_rate <= 30:
            recommendation = "AVOID"
            reason = (
                f"Our own history with {symbol}: "
                f"only {win_rate}% win rate over {trades} trades"
            )
        else:
            return []

        return [
            Evidence(
                provider="COMPANY",
                symbol=symbol,
                recommendation=recommendation,
                score=min(85, abs(win_rate)),
                confidence=min(85, 40 + trades * 3),
                reason=reason,
                facts={
                    "trades": trades,
                    "win_rate": win_rate,
                    "total_pnl": stats.get("total_pnl", 0),
                },
            )
        ]

    # --------------------------------------------------

    def report(self, symbol):
        """
        Human-readable dossier
        (used by Telegram /company command).
        """
        profile = self.get_full_profile(symbol)

        lines = [
            f"COMPANY DOSSIER : {symbol}",
            "",
            f"Name     : {profile.get('company_name', '')}",
            f"Business : {profile.get('core_business', '')[:120]}",
            f"Sector   : {profile.get('sector', '')}",
            f"Industry : {profile.get('industry', '')}",
            f"Themes   : {', '.join(profile.get('themes', [])) or '—'}",
            f"F&O      : {profile.get('fno', '—')}",
        ]

        # Living intelligence
        if profile.get("last_event_at"):
            lines += [
                "",
                f"Last Event : [{profile.get('last_event_type', '?')}] "
                f"{profile.get('last_catalyst', '')[:60]}",
                f"Event Time : {profile.get('last_event_at', '')}",
                f"Catalysts  : {profile.get('catalyst_count', 0)} recorded",
            ]

        if self.repository is not None:
            try:
                type_counts = (
                    self.repository.company_event_type_counts(
                        symbol.upper()
                    )
                )
                if type_counts:
                    top = list(type_counts.items())[:4]
                    lines.append(
                        "Event Mix  : "
                        + ", ".join(
                            f"{t}×{c}" for t, c in top
                        )
                    )
            except Exception:
                pass

        trade_stats = profile.get("trade_stats") or {}
        if trade_stats.get("trades"):
            lines += [
                "",
                f"Our Trades : {trade_stats['trades']} "
                f"(win rate {trade_stats.get('win_rate', 'N/A')}%)",
                f"Total PnL  : ₹{trade_stats.get('total_pnl', 0)}",
            ]

        events = profile.get("recent_events") or []
        if events:
            lines += ["", "Recent Events:"]
            for event in events[:5]:
                lines.append(
                    f"• [{event['event_type']}] "
                    f"{event['headline'][:80]}"
                )

        return "\n".join(lines)
