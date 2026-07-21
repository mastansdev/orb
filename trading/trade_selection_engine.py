from config import MIN_ORB_RANGE_PERCENT
from config import (
    CATALYST_GATE_ENABLED,
    CATALYST_PROVIDERS,
    CATALYST_MIN_SCORE,
)
from intelligence.evidence_builder import EvidenceBuilder
from intelligence.evidence_validator import EvidenceValidator
from intelligence.conviction_engine import ConvictionEngine
from intelligence.brain import Brain, DecisionAction
from tools.decision_trace import DecisionTrace
from intelligence.opportunity_pool_engine import opportunity_pool

class TradeSelectionEngine:

    def __init__(self):
        self.breakouts = 0
        self.selected = 0
        self.skipped = 0

        self.evidence_builder = EvidenceBuilder()
        self.evidence_validator = EvidenceValidator()
        self.conviction_engine = ConvictionEngine()
        self.brain = Brain()
        self.decision_trace = DecisionTrace()
        self.opportunity_pool = opportunity_pool

        # Attached later by the Engine (optional layers)
        self.pattern_engine = None
        self.company_intelligence = None
        self.event_intelligence = None
        self.fno_engine = None
        self.knowledge_graph = None
        self.results_calendar = None
        self.news_watchlist = None

        # Rolling spillovers from recent events
        self._recent_spillovers = []

        # News pipeline health counters
        self.stories_received = 0
        self.last_story_time = None

        # Rolling cache of MARKET_STORY evidence built by
        # timer-driven ingest cycles between breakouts, so
        # a breakout evaluated minutes later still sees the
        # narrative evidence (30-min freshness window).
        self._news_evidence_cache = []   # (datetime, Evidence)

    # --------------------------------------------------

    def ingest_news(self):
        """
        Pull new Railway stories and push them through EVERY
        intelligence layer: company memory, results calendar,
        structured events, F&O catalyst watchlist, causal
        chains, knowledge-graph spillover.

        Fix (2026-07-21): this used to live inline in
        evaluate(), so news was ONLY ingested when a breakout
        was already being evaluated — no breakout, no
        watchlist, ever. Now the Engine calls this on a timer
        (every NEWS_INGEST_SECONDS) from the tick loop, so
        the watchlist builds continuously all day.

        Returns fresh news evidence (newly built + cached
        from recent cycles, 30-minute window).
        """
        from datetime import datetime as _dt, timedelta as _td

        self.brain.update_intelligence()

        new_evidence = self.brain.build_news_evidence()
        if new_evidence:
            print(
                f"[BRAIN] News Evidence Loaded : "
                f"{len(new_evidence)}"
            )

        # Pipeline health: prove the Railway → Brain
        # link is alive (consumed by /news + alarm)
        if self.brain.pending_stories:
            self.stories_received += len(
                self.brain.pending_stories
            )
            self.last_story_time = _dt.now()

        # Company Memory : record stories
        if self.company_intelligence is not None:
            for story in self.brain.pending_stories:
                try:
                    self.company_intelligence.record_story(story)
                except Exception:
                    pass

        # News Watchlist : which symbols currently have a live
        # story attached (dashboard + /newswatch visibility).
        # Same affected_symbols fan-out as Brain.build_news_
        # evidence() -- only symbols the story actually named,
        # never a sector-wide guess.
        if self.news_watchlist is not None:
            for story in self.brain.pending_stories:
                try:
                    symbols = getattr(
                        story, "affected_symbols", None
                    ) or []
                    for symbol in symbols:
                        self.news_watchlist.on_story(
                            str(symbol).upper(), story
                        )
                except Exception as e:
                    print(f"[NEWS WATCHLIST] {e}")

        # Calendar Harvester : board-meeting
        # intimations → results calendar
        if self.calendar_harvester is not None:
            for story in self.brain.pending_stories:
                try:
                    self.calendar_harvester.harvest_story(
                        story
                    )
                except Exception:
                    pass

        # Event Intelligence : stories →
        # structured events → F&O watchlist
        if self.event_intelligence is not None:
            for story in self.brain.pending_stories:
                try:
                    events = (
                        self.event_intelligence.process_story(
                            story
                        )
                    )

                    for event in events:

                        if self.fno_engine is not None:
                            self.fno_engine.ingest_event(
                                event
                            )

                        # Results watchlist: flip a
                        # results-day stock WATCHING →
                        # ANNOUNCED when its result lands.
                        rw = getattr(
                            self, "results_watchlist", None
                        )
                        if rw is not None:
                            rw.on_event(event)

                        # Causal reasoning: activate
                        # institutional cause-effect chains
                        if self.causal_engine is not None:
                            self.causal_engine.analyze(
                                event
                            )

                        # Knowledge-graph spillover:
                        # who else does this event touch?
                        if self.knowledge_graph is not None:
                            spillovers = (
                                self.knowledge_graph
                                    .propagate(event)
                            )
                            if spillovers:
                                self._recent_spillovers = (
                                    self._recent_spillovers
                                    + spillovers
                                )[-100:]
                except Exception as e:
                    print(f"[EVENT] {e}")

        # ---------------------------------
        # Sector-sensitivity fan-out (2026-07-21)
        # ---------------------------------
        # MACRO/COMMODITY stories almost never match a specific
        # symbol (event_intelligence.process_story creates a
        # symbol="" market-wide record for these, which nothing
        # else consumes -- a broad "crude oil surges" story was
        # simply going nowhere). This is where it actually goes
        # somewhere: check the story against every stock's
        # sector sensitivity (intelligence/sector_sensitivity.py)
        # and fan out DIRECTIONAL evidence to the stocks it's
        # genuinely relevant to. Never guesses -- both a matched
        # commodity/currency keyword AND a clearly-stated
        # direction (rising/falling, dollar strengthening/
        # weakening) are required, or nothing is emitted.
        if self.company_intelligence is not None:
            for story in self.brain.pending_stories:
                try:
                    new_evidence.extend(
                        self._sensitivity_fanout(story)
                    )
                except Exception as e:
                    print(f"[SENSITIVITY] {e}")

        # Refresh the rolling cache (30-min window)
        now = _dt.now()
        self._news_evidence_cache = [
            (t, ev) for t, ev in self._news_evidence_cache
            if now - t <= _td(minutes=30)
        ] + [(now, ev) for ev in new_evidence]

        return [ev for _, ev in self._news_evidence_cache]

    # --------------------------------------------------
    # Read-only opinion snapshot (2026-07-21)
    # --------------------------------------------------
    # For the dashboard's "check now" / "schedule a check"
    # interactive controls. Deliberately NOT evaluate() --
    # evaluate() is the real breakout pipeline: it counts
    # attempts, gates on ORB structure, and (further down,
    # outside this class) can lead to an actual order. This
    # method only ever READS whatever real evidence already
    # exists for the symbol right now (the same rolling news
    # cache, the same company/event/F&O evidence builders used
    # for real trades) and scores it with the same
    # ConvictionEngine -- so the number shown is honestly
    # computed, not fabricated -- but nothing here can ever
    # place a trade, touch the opportunity pool, or affect
    # portfolio risk state.

    def snapshot_opinion(self, symbol):
        symbol = str(symbol).upper().strip()
        evidence = []

        # News: read the existing rolling cache directly rather
        # than calling ingest_news() again -- that method has
        # real side effects (pulls fresh stories, records company
        # events, harvests the calendar, feeds F&O/causal/graph)
        # that should only run on the engine's own timer, not
        # once per manual dashboard click.
        try:
            evidence += [
                ev for _, ev in self._news_evidence_cache
                if ev.symbol.upper() == symbol
            ]
        except Exception as e:
            print(f"[SNAPSHOT] news cache: {e}")

        if self.company_intelligence is not None:
            try:
                evidence += self.company_intelligence.build_evidence(
                    symbol
                )
            except Exception as e:
                print(f"[SNAPSHOT] company evidence: {e}")

        if self.event_intelligence is not None:
            try:
                evidence += self.event_intelligence.build_evidence(
                    symbol
                )
            except Exception as e:
                print(f"[SNAPSHOT] event evidence: {e}")

        if self.fno_engine is not None:
            try:
                evidence += self.fno_engine.build_evidence(symbol)
            except Exception as e:
                print(f"[SNAPSHOT] fno evidence: {e}")

        results_state = None
        rw = getattr(self, "results_watchlist", None)
        if rw is not None:
            try:
                if rw.is_watching(symbol):
                    results_state = (
                        "WATCHING (reports today, entries blocked)"
                    )
                elif rw.is_announced(symbol):
                    results_state = "ANNOUNCED (live catalyst)"
            except Exception:
                pass

        news_state = None
        if self.news_watchlist is not None:
            try:
                entry = self.news_watchlist.get(symbol)
                if entry:
                    news_state = dict(entry)
                    news_state["since"] = entry["since"].isoformat()
            except Exception:
                pass

        try:
            conviction = self.conviction_engine.evaluate(evidence)
        except Exception as e:
            conviction = {
                "score": 0, "grade": "N/A",
                "summary": f"scoring failed: {e}",
            }

        from datetime import datetime as _dt2
        return {
            "symbol": symbol,
            "checked_at": _dt2.now().isoformat(),
            "evidence_count": len(evidence),
            "conviction": conviction,
            "results_state": results_state,
            "news_state": news_state,
            "note": (
                "Read-only preview -- evidence that already "
                "exists right now, scored the same way real "
                "trades are. Not a live breakout evaluation "
                "(no ORB gate) and can never place an order."
            ),
        }

    # --------------------------------------------------
    # Sector-sensitivity fan-out helpers (2026-07-21)
    # --------------------------------------------------

    _COMMODITY_UP = (
        "surge", "surges", "surging", "jump", "jumps", "jumping",
        "rally", "rallies", "rallying", "soar", "soars", "soaring",
        "spike", "spikes", "spiking", "rise", "rises", "rising",
        "climb", "climbs", "climbing", "hits high", "record high",
        "hits a high", "at a high",
    )
    _COMMODITY_DOWN = (
        "crash", "crashes", "crashing", "plunge", "plunges",
        "plunging", "tumble", "tumbles", "tumbling", "slump",
        "slumps", "slumping", "fall", "falls", "falling",
        "decline", "declines", "declining", "drop", "drops",
        "dropping", "sink", "sinks", "sinking", "hits low",
        "record low", "hits a low", "at a low",
    )

    # USD/INR direction (the dominant, most-covered pair in
    # Indian financial news).
    _DOLLAR_UP = (
        "dollar strengthens", "dollar rises", "dollar gains",
        "dollar surges", "dollar firms", "rupee weakens",
        "rupee falls", "rupee depreciates", "rupee slips",
        "rupee slides", "rupee tumbles", "rupee hits low",
        "rupee at record low", "rupee declines",
    )
    _DOLLAR_DOWN = (
        "dollar weakens", "dollar falls", "dollar declines",
        "dollar slips", "rupee strengthens", "rupee gains",
        "rupee appreciates", "rupee rises", "rupee firms",
        "rupee hits high", "rupee climbs",
    )

    # Euro, GBP, yen, yuan direction (added 2026-07-21). These
    # were deliberately left undetected until now -- see the
    # git history note this replaces: guessing a currency's
    # direction from invented keywords would be fabrication.
    # These aren't invented, though -- "euro strengthens",
    # "yen weakens", "pound gains", "yuan devalues" are the
    # same standard, universal financial-journalism phrasing
    # already proven for the dollar/rupee pair above, just
    # applied to the other three currencies the sector taxonomy
    # (sector_sensitivity.py) already maps exposure for --
    # IT's euro/GBP billing, automobile's yen component
    # imports, chemicals'/consumer durables' yuan exposure.
    # Every one of those was sitting completely unreachable
    # before this: the exposure was mapped, but nothing could
    # ever detect the direction to react to it.
    _EURO_UP = (
        "euro strengthens", "euro rises", "euro gains",
        "euro surges", "euro firms", "euro rallies",
        "euro climbs",
    )
    _EURO_DOWN = (
        "euro weakens", "euro falls", "euro declines",
        "euro slips", "euro slides", "euro tumbles",
    )
    _GBP_UP = (
        "pound strengthens", "pound rises", "pound gains",
        "pound firms", "pound rallies", "sterling strengthens",
        "sterling rises", "sterling gains",
    )
    _GBP_DOWN = (
        "pound weakens", "pound falls", "pound declines",
        "pound slips", "sterling weakens", "sterling falls",
        "sterling declines",
    )
    _YEN_UP = (
        "yen strengthens", "yen rises", "yen gains",
        "yen firms", "yen rallies", "yen appreciates",
    )
    _YEN_DOWN = (
        "yen weakens", "yen falls", "yen declines",
        "yen slips", "yen slides", "yen depreciates",
    )
    _YUAN_UP = (
        "yuan strengthens", "yuan rises", "yuan gains",
        "yuan firms", "yuan appreciates",
        "renminbi strengthens", "renminbi rises",
        "renminbi gains", "renminbi appreciates",
    )
    _YUAN_DOWN = (
        "yuan weakens", "yuan falls", "yuan declines",
        "yuan depreciates", "yuan devalues",
        "yuan devaluation", "renminbi weakens",
        "renminbi falls", "renminbi depreciates",
    )

    # Factor-key -> real headline aliases (added 2026-07-21,
    # found by testing before declaring this done): sector_
    # sensitivity.py's factor keys are FX-code-style ("gbp",
    # "yuan"), but real headlines almost never write "GBP" --
    # they say "pound" or "sterling". Without this, the "gbp"
    # factor could never match any realistic headline even
    # though direction detection worked fine, since the raw
    # factor-in-text check only looked for the literal key
    # string. Commodity/dollar factor keys already read
    # naturally (e.g. "crude oil", "dollar") so they don't need
    # an alias list -- only added where testing showed a gap.
    _CURRENCY_FACTOR_ALIASES = {
        "gbp": ("gbp", "pound", "sterling"),
        "yuan": ("yuan", "renminbi", "rmb"),
    }

    # RBI repo rate direction (added 2026-07-21, wired to the
    # per-stock "rate_sensitive" flag from ECONOMIC_SENSITIVITY
    # = INTEREST RATE SENSITIVE / HOUSING). "MACRO" category
    # already covers "repo rate"/"rbi"/"interest rate" keywords
    # (news/news_taxonomy.py) -- this only adds direction on
    # top of a story already known to be about rates.
    _RATE_CUT = (
        "repo rate cut", "rbi cuts", "cuts repo rate",
        "cuts rates", "rate cut", "lowers repo rate",
        "eases rate", "rbi eases", "slashes repo rate",
        "reduces repo rate",
    )
    _RATE_HIKE = (
        "repo rate hike", "rbi hikes", "hikes repo rate",
        "hikes rates", "rate hike", "raises repo rate",
        "rbi raises", "tightens rate", "increases repo rate",
    )

    # Government capex/budget direction (wired to the per-stock
    # "govt_spending_sensitive" flag = GOVERNMENT SPENDING).
    _GOVT_SPENDING_UP = (
        "capex allocation increased", "boosts capex",
        "raises capex", "infrastructure push",
        "increases infra spending", "record capex allocation",
        "hikes capex", "budget allocation increased",
        "allocates more", "capex outlay raised",
    )
    _GOVT_SPENDING_DOWN = (
        "cuts capex", "reduces budget allocation",
        "slashes spending", "budget cut", "spending cut",
        "reduces capex", "lowers capex allocation",
    )

    def _detect_rate_direction(self, text):
        if any(kw in text for kw in self._RATE_CUT):
            return "cut"
        if any(kw in text for kw in self._RATE_HIKE):
            return "hike"
        return None

    def _detect_govt_spending_direction(self, text):
        if any(kw in text for kw in self._GOVT_SPENDING_UP):
            return "up"
        if any(kw in text for kw in self._GOVT_SPENDING_DOWN):
            return "down"
        return None

    def _detect_commodity_direction(self, text):
        if any(kw in text for kw in self._COMMODITY_UP):
            return "up"
        if any(kw in text for kw in self._COMMODITY_DOWN):
            return "down"
        return None

    def _detect_dollar_direction(self, text):
        if any(kw in text for kw in self._DOLLAR_UP):
            return "up"
        if any(kw in text for kw in self._DOLLAR_DOWN):
            return "down"
        return None

    def _detect_euro_direction(self, text):
        if any(kw in text for kw in self._EURO_UP):
            return "up"
        if any(kw in text for kw in self._EURO_DOWN):
            return "down"
        return None

    def _detect_gbp_direction(self, text):
        if any(kw in text for kw in self._GBP_UP):
            return "up"
        if any(kw in text for kw in self._GBP_DOWN):
            return "down"
        return None

    def _detect_yen_direction(self, text):
        if any(kw in text for kw in self._YEN_UP):
            return "up"
        if any(kw in text for kw in self._YEN_DOWN):
            return "down"
        return None

    def _detect_yuan_direction(self, text):
        if any(kw in text for kw in self._YUAN_UP):
            return "up"
        if any(kw in text for kw in self._YUAN_DOWN):
            return "down"
        return None

    def _sensitivity_fanout(self, story):
        """
        For one MACRO/COMMODITY-category story, fan out
        directional evidence to every stock whose sector/
        industry sensitivity (see sector_sensitivity.py)
        matches a commodity/currency mentioned in the story
        AND has a clearly-stated direction. Returns a list of
        Evidence (possibly empty -- most stories won't match
        anything, and that's the correct, honest outcome).
        """
        from intelligence.evidence import Evidence

        category = str(getattr(story, "category", "") or "").upper()
        if category not in ("MACRO", "COMMODITY"):
            return []

        text = str(getattr(story, "name", "") or "").lower()
        if not text:
            return []

        commodity_dir = self._detect_commodity_direction(text)
        dollar_dir = self._detect_dollar_direction(text)
        euro_dir = self._detect_euro_direction(text)
        gbp_dir = self._detect_gbp_direction(text)
        yen_dir = self._detect_yen_direction(text)
        yuan_dir = self._detect_yuan_direction(text)
        rate_dir = self._detect_rate_direction(text)
        govt_dir = self._detect_govt_spending_direction(text)

        # Route each currency pair's own detected direction to
        # the matching factor key in a stock's currencies dict
        # (sector_sensitivity.py uses "usd/inr"/"dollar"/"rupee"
        # for the dollar pair, and "euro"/"gbp"/"yen"/"yuan" for
        # the others) -- added 2026-07-21 alongside the euro/
        # gbp/yen/yuan detectors above. Before this, a single
        # dollar_dir variable was applied to WHATEVER currency
        # factor a stock had mapped, which only happened to be
        # correct because no other pair could ever be detected.
        currency_directions = {
            "usd/inr": dollar_dir,
            "dollar": dollar_dir,
            "rupee": dollar_dir,
            "euro": euro_dir,
            "gbp": gbp_dir,
            "yen": yen_dir,
            "yuan": yuan_dir,
        }
        any_currency_dir = any(
            d is not None for d in currency_directions.values()
        )

        if (
            commodity_dir is None
            and not any_currency_dir
            and rate_dir is None
            and govt_dir is None
        ):
            return []

        headline = (getattr(story, "name", "") or "")[:150]
        confidence = float(getattr(story, "confidence", 50) or 50)

        out = []

        for symbol, profile in self.company_intelligence.profiles.items():
            sector = profile.get("sector", "")
            industry = profile.get("industry", "")
            if not sector:
                continue

            sens = self.company_intelligence.get_sensitivity(symbol)

            stock_direction = None
            matched_factor = None

            if commodity_dir is not None:
                for factor, exposure in sens.get("commodities", {}).items():
                    if factor not in text:
                        continue
                    # cost side: rising commodity = headwind (SELL-leaning)
                    # revenue side: rising commodity = tailwind (BUY-leaning)
                    if exposure == "cost":
                        stock_direction = (
                            "SELL" if commodity_dir == "up" else "BUY"
                        )
                    elif exposure == "revenue":
                        stock_direction = (
                            "BUY" if commodity_dir == "up" else "SELL"
                        )
                    matched_factor = factor
                    break

            if stock_direction is None and any_currency_dir:
                for factor, exposure in sens.get("currencies", {}).items():
                    aliases = self._CURRENCY_FACTOR_ALIASES.get(
                        factor, (factor,)
                    )
                    if not any(alias in text for alias in aliases):
                        continue
                    pair_dir = currency_directions.get(factor)
                    if pair_dir is None:
                        continue
                    # exporter: this currency strengthening (INR
                    # weakening against it) = tailwind
                    # importer: this currency strengthening = headwind
                    if exposure == "exporter":
                        stock_direction = (
                            "BUY" if pair_dir == "up" else "SELL"
                        )
                    elif exposure == "importer":
                        stock_direction = (
                            "SELL" if pair_dir == "up" else "BUY"
                        )
                    matched_factor = factor
                    break

            # Interest-rate-sensitive stocks (per-stock flag from
            # ECONOMIC_SENSITIVITY = INTEREST RATE SENSITIVE /
            # HOUSING) -- a repo rate cut lowers borrowing cost
            # and boosts loan/housing demand (tailwind); a hike
            # does the opposite.
            if stock_direction is None and rate_dir is not None:
                if sens.get("rate_sensitive"):
                    stock_direction = (
                        "BUY" if rate_dir == "cut" else "SELL"
                    )
                    matched_factor = "RBI repo rate"

            # Government-capex-sensitive stocks (per-stock flag
            # from ECONOMIC_SENSITIVITY = GOVERNMENT SPENDING) --
            # infra/capital-goods/defence names whose order book
            # tracks budget/capex announcements directly.
            if stock_direction is None and govt_dir is not None:
                if sens.get("govt_spending_sensitive"):
                    stock_direction = (
                        "BUY" if govt_dir == "up" else "SELL"
                    )
                    matched_factor = "government capex/budget"

            if stock_direction is None:
                continue

            out.append(
                Evidence(
                    provider="SENSITIVITY",
                    symbol=symbol,
                    recommendation=stock_direction,
                    score=min(60, confidence * 0.6),
                    confidence=min(60, confidence * 0.6),
                    reason=(
                        f"{sector} sector sensitivity to "
                        f"'{matched_factor}': {headline}"
                    ),
                    facts={
                        "sector": sector,
                        "industry": industry,
                        "matched_factor": matched_factor,
                        "story_category": category,
                    },
                )
            )

        if out:
            print(
                f"[SENSITIVITY] '{headline[:60]}' fanned out to "
                f"{len(out)} stock(s)"
            )

        return out

    # --------------------------------------------------

    def attach_intelligence(
        self,
        pattern_engine=None,
        company_intelligence=None,
        event_intelligence=None,
        fno_engine=None,
        knowledge_graph=None,
        results_calendar=None,
        calendar_harvester=None,
        causal_engine=None
    ):
        """
        Called by the Engine after construction to wire
        memory-driven intelligence layers.
        """
        self.pattern_engine = pattern_engine
        self.company_intelligence = company_intelligence
        self.event_intelligence = event_intelligence
        self.fno_engine = fno_engine
        self.knowledge_graph = knowledge_graph
        self.results_calendar = results_calendar
        self.calendar_harvester = calendar_harvester
        self.causal_engine = causal_engine

    # --------------------------------------------------

    def _market_scan_rank(self, symbol):
        """
        ACTIVE MARKET SCANNER (2026-07-21).

        Returns the symbol's 1-based rank among today's top
        gainers if it qualifies as a market leader, else None.

        Qualifies when BOTH hold:
          • up ≥ MARKET_SCAN_MIN_CHANGE_PCT vs prev close
          • within the top MARKET_SCAN_TOP_N of the whole
            universe by % change (live ticks)

        This arms genuine stocks-in-play even when no news
        story was matched — the tape itself is the evidence.
        """
        from config import (
            MARKET_SCAN_ENABLED,
            MARKET_SCAN_TOP_N,
            MARKET_SCAN_MIN_CHANGE_PCT,
        )

        if not MARKET_SCAN_ENABLED:
            return None

        from intelligence.price_engine import price_engine

        my_change = price_engine.get_change(symbol)
        if (
            my_change is None
            or my_change < MARKET_SCAN_MIN_CHANGE_PCT
        ):
            return None

        stronger = 0
        for other, data in price_engine.prices.items():
            if other == symbol:
                continue
            ch = data.get("change")
            if ch is not None and ch > my_change:
                stronger += 1
                if stronger >= MARKET_SCAN_TOP_N:
                    return None

        return stronger + 1

    # --------------------------------------------------

    def evaluate(
        self,
        symbol,
        ltp,
        orb,
        intelligence,
        entry_mode="ORB"
    ):
        self.breakouts += 1

        # ---------------------------------
        # Structural ORB Validation (Early Gate)
        # EVENT entries (Rule-001 catalyst override)
        # bypass the ORB structure gate — their gate
        # is the higher conviction bar downstream.
        # ---------------------------------
        if entry_mode != "EVENT":
            orb_result = self._score_orb(orb)
            if not orb_result["passed"]:
                self.skipped += 1
                return self._build_decision(
                    selected=False,
                    score=0,
                    reasons=[orb_result["reason"]],
                    brain_decision=None
                )

        # ---------------------------------
        # Institutional Decision Pipeline
        # ---------------------------------
        evidence = self.evidence_builder.build(intelligence)

        # Pull anything new that arrived since the last
        # ingest cycle (the engine also calls ingest_news
        # on a timer — see Engine.process_tick — so the
        # watchlist builds even on days with no breakouts).
        #
        # Fix (2026-07-21): ingest_news() returns the GLOBAL
        # 30-min rolling cache across ALL symbols -- filter
        # to just this symbol's own news here. Before the
        # symbol-tagging fix upstream (Brain.build_news_
        # evidence / NewsEvidenceBuilder.build), this filter
        # would have silently dropped everything, since every
        # item carried symbol="". Now that evidence is
        # correctly tagged, this is what actually scopes news
        # to the stock it's about instead of applying any
        # recent news to every stock being evaluated.
        symbol_upper = symbol.upper()
        news_evidence = [
            ev for ev in self.ingest_news()
            if ev.symbol.upper() == symbol_upper
        ]

        # ---------------------------------
        # Pattern Evidence (memory-driven)
        # ---------------------------------
        pattern_evidence = []
        company_evidence = []

        sector_name = ""
        try:
            sector_snapshot = (
                intelligence.get("symbol", {}).get("sector")
                or {}
            )
            sector_name = sector_snapshot.get("sector_name", "") \
                or sector_snapshot.get("name", "")
        except Exception:
            pass

        if self.pattern_engine is not None:
            try:
                pattern_evidence = self.pattern_engine.build_evidence(
                    symbol,
                    sector_name
                )
            except Exception as e:
                print(f"[PATTERN] {e}")

        if self.company_intelligence is not None:
            try:
                company_evidence = (
                    self.company_intelligence.build_evidence(symbol)
                )
            except Exception as e:
                print(f"[COMPANY] {e}")

        # ---------------------------------
        # Event + F&O catalyst evidence
        # ---------------------------------
        event_evidence = []
        fno_evidence = []

        if self.event_intelligence is not None:
            try:
                event_evidence = (
                    self.event_intelligence.build_evidence(
                        symbol
                    )
                )

                # Reaction-decay scaling: a recurring
                # catalyst the market has learned to
                # anticipate carries LESS conviction than
                # a first-of-kind shock (1st big, 2nd
                # smaller). Scale each event's score by
                # its event-type decay multiplier.
                if (
                    self.reaction_decay is not None
                    and event_evidence
                ):
                    for ev in event_evidence:
                        etype = ev.facts.get("event_type")
                        if not etype:
                            continue
                        mult = self.reaction_decay.multiplier(
                            etype
                        )
                        if mult < 1.0:
                            ev._data["score"] = round(
                                ev.score * mult, 1
                            )
                            ev._data["reason"] += (
                                f" | decay ×{mult} "
                                f"(shock priced-in over time)"
                            )
            except Exception as e:
                print(f"[EVENT] {e}")

        if self.fno_engine is not None:
            try:
                fno_evidence = (
                    self.fno_engine.build_evidence(symbol)
                )
            except Exception as e:
                print(f"[FNO] {e}")

        # ---------------------------------
        # Results-day handling:
        #   WATCHING (result not out)  → BLOCK entry
        #   ANNOUNCED (result is out)  → live catalyst
        # ---------------------------------
        event_risk_evidence = []
        results_live_evidence = []

        rw = getattr(self, "results_watchlist", None)

        if rw is not None:
            try:
                # Pre-result: hard block (binary-event risk)
                if rw.is_watching(symbol):
                    from config import RESULTS_DAY_BLOCK
                    if RESULTS_DAY_BLOCK:
                        self.skipped += 1
                        return self._build_decision(
                            selected=False,
                            score=0,
                            reasons=[
                                f"{symbol}: reports TODAY, "
                                f"result not out yet — "
                                f"no new risk into binary "
                                f"event (watching)"
                            ],
                            brain_decision=None
                        )

                # Post-result: positive catalyst boost
                results_live_evidence = rw.build_evidence(
                    symbol
                )
            except Exception as e:
                print(f"[WATCHLIST] {e}")

        elif self.results_calendar is not None:
            # Fallback if watchlist not attached
            try:
                event_risk_evidence = (
                    self.results_calendar.build_evidence(
                        symbol
                    )
                )
                from config import RESULTS_DAY_BLOCK
                if RESULTS_DAY_BLOCK and event_risk_evidence:
                    self.skipped += 1
                    return self._build_decision(
                        selected=False,
                        score=0,
                        reasons=[
                            f"{symbol}: results today — "
                            f"binary event block"
                        ],
                        brain_decision=None
                    )
            except Exception as e:
                print(f"[CALENDAR] {e}")

        # ---------------------------------
        # Sympathy spillover from graph
        # ---------------------------------
        sympathy_evidence = []

        if self.knowledge_graph is not None:
            try:
                sympathy_evidence = (
                    self.knowledge_graph
                        .build_sympathy_evidence(
                            symbol,
                            self._recent_spillovers
                        )
                )
            except Exception as e:
                print(f"[GRAPH] {e}")

        # ---------------------------------
        # Causal chain evidence
        # ---------------------------------
        causal_evidence = []

        if self.causal_engine is not None:
            try:
                causal_evidence = (
                    self.causal_engine.build_evidence(
                        symbol
                    )
                )
            except Exception as e:
                print(f"[CAUSAL] {e}")

        # ---------------------------------
        # News evidence is now part of the live
        # decision flow (structural + news + memory
        # + events + F&O catalysts + graph spillover
        # + binary-event risk).
        # ---------------------------------
        all_evidence = (
            evidence
            + news_evidence
            + pattern_evidence
            + company_evidence
            + event_evidence
            + fno_evidence
            + event_risk_evidence
            + results_live_evidence
            + sympathy_evidence
            + causal_evidence
        )

        validated_evidence = self.evidence_validator.validate(
            all_evidence
        )

        # ---------------------------------
        # CATALYST / MARKET-SCAN EVIDENCE (2026-07-21 rewrite)
        #
        # ORIGINAL BEHAVIOUR (removed): a HARD BLOCK — any ORB
        # breakout without a matched catalyst or market-scan
        # rank was rejected outright, no matter how strong the
        # structural breakout. Result: 100+ genuine breakouts
        # on 07-21 captured ZERO trades. This contradicted the
        # bot's own motto ("Evidence contributes; Conviction
        # decides; Risk authorizes; Execution acts") by turning
        # evidence into a hard requirement instead of a booster.
        #
        # NEW BEHAVIOUR: catalyst/scan status is additional
        # EVIDENCE that boosts conviction — it no longer gates
        # entry. A genuine ORB breakout is evaluated by the
        # Brain regardless of catalyst status; CONVICTION_MIN_
        # SCORE (already enforced downstream by Brain.evaluate)
        # is the real filter, using ALL available evidence
        # (sector strength, pattern history, relative strength,
        # news, F&O catalysts, results, causal chains, sympathy
        # — and now market-scan leader status too).
        # ---------------------------------
        if CATALYST_GATE_ENABLED and entry_mode != "EVENT":
            catalysts = [
                ev for ev in validated_evidence
                if ev.provider in CATALYST_PROVIDERS
                and str(ev.recommendation).upper() not in (
                    "SELL", "AVOID"
                )
                and ev.score >= CATALYST_MIN_SCORE
            ]

            # Second arming signal: ACTIVE MARKET SCAN. If the
            # stock is one of today's true leaders (top N of
            # the whole universe by % change on live ticks),
            # that is itself evidence worth feeding to
            # conviction — the tape is the evidence, even with
            # no matched news story yet.
            scan_rank = self._market_scan_rank(symbol)

            if catalysts:
                print(
                    f"[CATALYST] {symbol} boosted by: "
                    + "; ".join(
                        f"{ev.provider}({ev.score:.0f})"
                        for ev in catalysts[:3]
                    )
                )

            if scan_rank is not None:
                from intelligence.price_engine import (
                    price_engine as _pe,
                )
                from intelligence.evidence import Evidence

                scan_score = max(30, 70 - (scan_rank - 1) * 2)
                change = _pe.get_change(symbol)
                validated_evidence.append(
                    Evidence(
                        provider="MARKET_SCAN",
                        symbol=symbol,
                        recommendation="BUY",
                        score=scan_score,
                        confidence=60,
                        reason=(
                            f"#{scan_rank} strongest in market "
                            f"today ({change:+.2f}% vs prev "
                            f"close) — active leader"
                        ),
                        facts={
                            "scan_rank": scan_rank,
                            "change_pct": change,
                        },
                    )
                )
                print(
                    f"[MARKET SCAN] {symbol}: #{scan_rank} "
                    f"strongest in market ({change:+.2f}%) — "
                    f"added as evidence"
                )

            if not catalysts and scan_rank is None:
                print(
                    f"[{symbol}] no catalyst/scan evidence — "
                    f"still evaluated on structural evidence "
                    f"alone (sector/pattern/RS); Brain decides."
                )

        conviction = self.conviction_engine.evaluate(validated_evidence)

        if conviction.get("summary"):
            print(f"[CONVICTION] {conviction['summary']}")

        # ---------------------------------
        # Brain Evaluation (Shadow Mode)
        # ---------------------------------
        brain_decision = self.brain.evaluate(
            symbol=symbol,
            evidence_list=validated_evidence,
            conviction_snapshot=conviction
        )

        selected = (
            brain_decision.action == DecisionAction.BUY
        )
        if selected:
            self.opportunity_pool.add(
                symbol=symbol,
                conviction=brain_decision.score,
                quality=brain_decision.score,
                orb=orb,
                intelligence=intelligence,
                evidence=validated_evidence,
                brain_decision=brain_decision,
            )
            self.selected += 1
        else:
            self.skipped += 1

        # Wrapped tracer call in try-except block to guarantee zero trading disruption
        try:
            self.decision_trace.trace(
                symbol=symbol,
                orb=orb,
                intelligence=intelligence,
                evidence=validated_evidence,
                conviction=conviction,
                brain_decision=brain_decision,
                final_decision="BUY" if selected else "REJECT",
            )
        except Exception as e:
            print(f"[DecisionTrace] {e}")

        return self._build_decision(
            selected=selected,
            score=brain_decision.score,
            reasons=brain_decision.reasons,
            brain_decision=brain_decision
        )

    # --------------------------------------------------

    def score_symbol(self, symbol, intelligence):
        """
        READ-ONLY current conviction for a symbol —
        no brain, no pool, no side effects. Used by the
        HOLD brain to re-evaluate open-position theses.
        Returns a 0-100 conviction score, or None if the
        rebuild itself failed (distinct from a genuine 0 —
        see the except block below for why that distinction
        matters).

        Fix (2026-07-21): this used to rebuild evidence from
        only 5 of the 10 sources evaluate() uses at entry --
        missing news (MARKET_STORY + SENSITIVITY), the post-
        results catalyst, knowledge-graph sympathy spillover,
        and causal-chain evidence entirely. Two real problems
        followed from that: (1) "current" was never a fair
        comparison to entry_conviction, since half the
        evidence a position entered on wasn't being rebuilt --
        biasing every thesis check toward looking artificially
        decayed even when nothing had changed; (2) worse, if a
        position entered partly on a news catalyst, the HOLD
        brain was structurally blind to that catalyst fading or
        reversing -- exactly the scenario this engine's own
        docstring says it exists to catch ("catalyst fades is a
        dead trade"). Now rebuilds the SAME evidence set
        evaluate() does, symmetrically, minus the two things
        that only make sense at entry (the ORB structure gate
        and the catalyst hard-block, both entry-timing checks,
        not thesis-quality checks).
        """
        try:
            evidence = self.evidence_builder.build(
                intelligence
            )

            symbol_upper = symbol.upper()
            try:
                evidence += [
                    ev for _, ev in self._news_evidence_cache
                    if ev.symbol.upper() == symbol_upper
                ]
            except Exception:
                pass

            for engine in (
                self.pattern_engine,
                self.company_intelligence,
                self.event_intelligence,
                self.fno_engine,
            ):
                if engine is None:
                    continue
                try:
                    evidence += engine.build_evidence(symbol)
                except Exception:
                    pass

            rw = getattr(self, "results_watchlist", None)
            if rw is not None:
                try:
                    evidence += rw.build_evidence(symbol)
                except Exception:
                    pass

            if self.knowledge_graph is not None:
                try:
                    evidence += (
                        self.knowledge_graph
                        .build_sympathy_evidence(
                            symbol, self._recent_spillovers
                        )
                    )
                except Exception:
                    pass

            if self.causal_engine is not None:
                try:
                    evidence += self.causal_engine.build_evidence(
                        symbol
                    )
                except Exception:
                    pass

            validated = self.evidence_validator.validate(
                evidence
            )
            snapshot = self.conviction_engine.evaluate(
                validated
            )
            return float(snapshot.get("score") or 0)
        except Exception as e:
            # Fix (2026-07-21): this used to return 0.0 here,
            # identically to a stock that genuinely has zero
            # conviction left. Since 0.0 is always below
            # entry_conviction * THESIS_DECAY_FRACTION, a plain
            # code bug (evidence_builder/validator/conviction_
            # engine throwing) was indistinguishable from "the
            # thesis genuinely died" -- it would silently force
            # a real THESIS_EXIT on a live position, with a
            # confident-looking "thesis decayed" message and
            # zero trace of the actual failure. Return None
            # instead so the caller (PositionThesisEngine.advise)
            # can tell "no real answer" apart from "real answer
            # is zero" and fall back to HOLD, and print the
            # real reason so it isn't silent either.
            print(f"[SCORE_SYMBOL] {symbol}: {e}")
            return None

    # --------------------------------------------------

    def _build_decision(
        self,
        selected,
        score,
        reasons,
        brain_decision=None
    ):
        return {
            "selected": selected,
            "queued": selected,
            "score": score,
            "reasons": reasons,
            "brain_decision": brain_decision
        }

    # --------------------------------------------------

    def _score_orb(
        self,
        orb
    ):
        if not orb or orb.get("high") is None or orb.get("low") is None:
            return {
                "passed": False,
                "score": 0,
                "reason": "ORB data unavailable"
            }

        orb_range_percent = ((orb["high"] - orb["low"]) / orb["low"]) * 100

        if orb_range_percent < MIN_ORB_RANGE_PERCENT:
            return {
                "passed": False,
                "score": 0,
                "reason": f"Weak ORB ({orb_range_percent:.2f}%)"
            }

        return {
            "passed": True,
            "score": 100,
            "reason": f"ORB Range {orb_range_percent:.2f}%"
        }

    # --------------------------------------------------

    def stats(self):
        return {
            "breakouts": self.breakouts,
            "selected": self.selected,
            "skipped": self.skipped
        }