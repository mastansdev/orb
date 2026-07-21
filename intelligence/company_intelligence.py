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

from intelligence.evidence import Evidence
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

                # Per-stock sensitivity tags (added 2026-07-21).
                # These two columns exist in the master database
                # but were never read anywhere before -- confirmed
                # real coverage: ECONOMIC_SENSITIVITY populated for
                # 604/750 rows (81%), COMMODITY_EXPOSURE for 135/750
                # (18%, i.e. only the stocks with a genuine direct
                # commodity link are tagged -- most aren't, correctly).
                # Both are pipe-separated free text with a small,
                # closed vocabulary (confirmed by inspecting all
                # distinct values, not guessed):
                #   ECONOMIC_SENSITIVITY: CONSUMER DRIVEN,
                #     EXPORT ORIENTED, GOVERNMENT SPENDING,
                #     IMPORT DEPENDENT, INTEREST RATE SENSITIVE,
                #     HOUSING (combos joined with "|")
                #   COMMODITY_EXPOSURE: specific commodity names
                #     (ALUMINIUM, COPPER, CRUDE OIL, COAL, COTTON,
                #     GOLD, LIMESTONE, NATURAL GAS, PHOSPHATES,
                #     STEEL, SUGAR, UREA, ZINC, LEAD, SILVER)
                commodity_exposure = [
                    c.strip().upper()
                    for c in re.split(
                        r"[|,]",
                        str(row.get("COMMODITY_EXPOSURE", ""))
                    )
                    if c.strip()
                ]

                economic_sensitivity = [
                    e.strip().upper()
                    for e in re.split(
                        r"[|,]",
                        str(row.get("ECONOMIC_SENSITIVITY", ""))
                    )
                    if e.strip()
                ]

                self.profiles[symbol].update({
                    "company_name": row.get("COMPANY NAME", ""),
                    "core_business": row.get("CORE BUSINESS", ""),
                    "sector": row.get("SECTOR", ""),
                    "industry": row.get("INDUSTRY", ""),
                    "themes": themes,
                    "keywords": keywords,
                    "fno": row.get("FNO", ""),
                    "lot_size": row.get("LOT SIZE", ""),
                    "business_type": row.get("BUSINESS_TYPE", ""),
                    "ownership": row.get("OWNERSHIP", ""),
                    "commodity_exposure": commodity_exposure,
                    "economic_sensitivity": economic_sensitivity,
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
            "business_type": "",
            "ownership": "",
            "commodity_exposure": [],
            "economic_sensitivity": [],

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

        # Free, already-available enrichment (2026-07-21):
        # peer group + sector macro sensitivity. Both come
        # from data the bot already has loaded -- no new
        # source, no network call, safe to compute on every
        # dossier request.
        try:
            profile["competitors"] = self.get_competitors(symbol)
        except Exception:
            profile["competitors"] = []

        try:
            profile["sensitivity"] = self.get_sensitivity(symbol)
        except Exception:
            profile["sensitivity"] = {}

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
    # PUBLIC : Competitors / Peer Group  (added 2026-07-21)
    # --------------------------------------------------
    #
    # Free, already-available data: the sector/industry
    # mapping for all 750 stocks already lives in
    # master_loader (loaded from Masterdata/master_database
    # .xlsx). This was never exposed as a per-stock
    # "competitors" list before -- no new data source
    # needed, just wiring what's already there.

    def get_competitors(self, symbol, limit=10):
        """
        Peer companies for `symbol`. Prefers the tighter
        industry grouping (e.g. "Private Banks") over the
        broader sector (e.g. "Banking") when available,
        since industry peers are more genuinely comparable.
        Never fabricates a peer list for an unmapped symbol
        -- returns [] instead.
        """
        from core.master_loader import master_loader

        symbol = symbol.upper()
        industry = master_loader.get_industry(symbol)
        sector = master_loader.get_sector(symbol)

        peers = []
        if industry:
            peers = master_loader.get_industry_symbols(industry)
        if not peers and sector:
            peers = master_loader.get_sector_symbols(sector)

        return [
            p for p in peers
            if p.upper() != symbol
        ][:limit]

    # --------------------------------------------------
    # PUBLIC : Per-Stock Sensitivity
    # (sector-level added 2026-07-21, per-stock layer
    # added same day after the sector-only version was
    # found too coarse)
    # --------------------------------------------------
    #
    # Commodity/currency/government/rate sensitivity, per
    # STOCK -- built by layering the master database's own
    # per-stock tags (COMMODITY_EXPOSURE, ECONOMIC_SENSITIVITY,
    # BUSINESS_TYPE) on top of the curated sector/industry
    # taxonomy in intelligence/sector_sensitivity.py. See the
    # full reasoning in the method docstring below.

    def get_sensitivity(self, symbol):
        """
        Per-stock sensitivity, built by layering the master
        database's own per-stock tags (COMMODITY_EXPOSURE,
        ECONOMIC_SENSITIVITY, BUSINESS_TYPE) on top of the
        sector/industry taxonomy (sector_sensitivity.py).

        Why layered rather than sector-only (2026-07-21): the
        sector taxonomy is a reasonable generalization but is
        genuinely wrong at the edges -- e.g. every CAPITAL GOODS
        stock was treated as steel+copper+aluminium cost-exposed,
        even ones with no real exposure to two of the three. The
        master database's COMMODITY_EXPOSURE column tags each
        stock with ONLY the commodities it's actually linked to
        (135/750 rows populated -- most stocks correctly have
        none), so where it's populated it REPLACES the sector
        commodity list with the stock's real, narrower one rather
        than adding to it. Direction (cost vs revenue) still
        comes from the sector/industry entry when that commodity
        is already known there (that reasoning doesn't change
        per-stock); for a commodity tagged on the stock but not
        in the sector dict, direction is inferred from
        BUSINESS_TYPE: MINING (a producer) = revenue, anything
        else = cost (a purchaser/consumer of the input) -- the
        same producer/consumer logic already used to write the
        sector table, just applied per stock instead of assumed
        uniformly across the whole sector.

        ECONOMIC_SENSITIVITY (81% populated) similarly overrides
        the sector-level USD/INR guess with the stock's own
        EXPORT ORIENTED / IMPORT DEPENDENT tag when present, and
        adds two trigger flags the sector taxonomy never had:
        rate_sensitive (INTEREST RATE SENSITIVE or HOUSING) and
        govt_spending_sensitive (GOVERNMENT SPENDING) -- both
        consumed by TradeSelectionEngine._sensitivity_fanout()
        for RBI-rate and budget/capex news. CONSUMER DRIVEN is
        deliberately NOT wired to a news trigger yet -- there's
        no reliable, unambiguous headline pattern for "consumer
        demand rose/fell" the way there is for a rate cut/hike,
        and guessing one would be exactly the kind of fabrication
        this file avoids elsewhere.
        """
        from intelligence.sector_sensitivity import (
            get_sensitivity as _sector_sensitivity,
        )

        profile = self.get_profile(symbol)
        base = _sector_sensitivity(
            profile.get("sector", ""),
            profile.get("industry", ""),
        )

        commodity_exposure = profile.get("commodity_exposure") or []
        economic_sensitivity = profile.get("economic_sensitivity") or []
        business_type = str(profile.get("business_type", "")).strip().upper()

        result = {
            "commodities": dict(base.get("commodities", {})),
            "currencies": dict(base.get("currencies", {})),
            "government": base.get("government", ""),
            "notes": base.get("notes", ""),
            "rate_sensitive": False,
            "govt_spending_sensitive": False,
        }

        # --------------------------------------------------
        # Per-stock commodity override (narrows to only the
        # commodities THIS stock is actually tagged with).
        # --------------------------------------------------
        if commodity_exposure:
            narrowed = {}
            for tag in commodity_exposure:
                key = tag.strip().lower()
                if not key:
                    continue

                # MINING business type means THIS stock is a
                # producer of the commodity it's tagged with --
                # that always means revenue-side, even if the
                # sector table's entry for the same commodity
                # name was written with a different kind of
                # company in mind (e.g. METALS & MINING's
                # "coal": "cost" was reasoned for steel/aluminium
                # smelters buying coal as furnace fuel -- wrong
                # for a coal producer like Coal India, which is
                # also tagged coal exposure but SELLS it).
                if business_type == "MINING":
                    narrowed[key] = "revenue"
                    continue

                # Otherwise prefer the sector/industry-reasoned
                # direction for this exact commodity if known.
                if key in result["commodities"]:
                    narrowed[key] = result["commodities"][key]
                    continue

                # Not in the sector table and not a producer --
                # default to cost (a purchaser/consumer of the
                # input), the more common case for a company
                # explicitly tagged with a commodity exposure.
                narrowed[key] = "cost"

            result["commodities"] = narrowed

        # --------------------------------------------------
        # Per-stock currency override (EXPORT ORIENTED /
        # IMPORT DEPENDENT are stock-specific facts, more
        # reliable than a sector-wide guess). Overwrites EVERY
        # currency key the sector table had (usd/inr, dollar,
        # euro, gbp, yuan, yen are all just alternate headline
        # phrasings of the same USD/INR relationship in this
        # taxonomy) so a stock's own tag can't be contradicted
        # by a stale sector-level entry for a different phrasing
        # of the same pair -- e.g. without this, a stock overridden
        # to "importer" via usd/inr could still carry the sector's
        # old "dollar": "exporter" entry untouched, and a headline
        # saying "dollar strengthens" would silently give the
        # wrong-direction signal.
        # --------------------------------------------------
        if "EXPORT ORIENTED" in economic_sensitivity:
            result["currencies"] = {
                k: "exporter" for k in result["currencies"]
            } or {"usd/inr": "exporter"}
        elif "IMPORT DEPENDENT" in economic_sensitivity:
            result["currencies"] = {
                k: "importer" for k in result["currencies"]
            } or {"usd/inr": "importer"}

        # --------------------------------------------------
        # New per-stock trigger flags (no sector equivalent).
        # --------------------------------------------------
        if (
            "INTEREST RATE SENSITIVE" in economic_sensitivity
            or "HOUSING" in economic_sensitivity
        ):
            result["rate_sensitive"] = True

        if "GOVERNMENT SPENDING" in economic_sensitivity:
            result["govt_spending_sensitive"] = True

        return result

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

        competitors = profile.get("competitors") or []
        if competitors:
            lines.append(
                f"Peers    : {', '.join(competitors[:8])}"
            )

        sensitivity = profile.get("sensitivity") or {}
        sens_parts = []
        if sensitivity.get("commodities"):
            sens_parts.append(
                "commodities: "
                + ", ".join(sensitivity["commodities"])
            )
        if sensitivity.get("currencies"):
            sens_parts.append(
                "currencies: "
                + ", ".join(sensitivity["currencies"])
            )
        if sensitivity.get("government"):
            sens_parts.append(
                f"government: {sensitivity['government']}"
            )
        if sensitivity.get("rate_sensitive"):
            sens_parts.append("RBI rate moves")
        if sensitivity.get("govt_spending_sensitive"):
            sens_parts.append("govt capex/budget")
        if sens_parts:
            lines.append(
                "Sensitive to : " + " | ".join(sens_parts)
            )

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
