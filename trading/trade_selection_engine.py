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

    # USD/INR direction only (the dominant, most-covered pair
    # in Indian financial news). Other currencies in the
    # taxonomy (yen, euro, gbp, yuan) deliberately have NO
    # direction detection yet -- guessing their direction from
    # generic keywords would be exactly the kind of fabrication
    # this codebase avoids. Extend this explicitly, pair by
    # pair, when there's a real headline pattern to test
    # against -- not before.
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

        if commodity_dir is None and dollar_dir is None:
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

            if stock_direction is None and dollar_dir is not None:
                for factor, exposure in sens.get("currencies", {}).items():
                    if factor not in text:
                        continue
                    # exporter: dollar strength (rupee weak) = tailwind
                    # importer: dollar strength (rupee weak) = headwind
                    if exposure == "exporter":
                        stock_direction = (
                            "BUY" if dollar_dir == "up" else "SELL"
                        )
                    elif exposure == "importer":
                        stock_direction = (
                            "SELL" if dollar_dir == "up" else "BUY"
                        )
                    matched_factor = factor
                    break

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
        Returns a 0-100 conviction score (0 on failure).
        """
        try:
            evidence = self.evidence_builder.build(
                intelligence
            )

            for engine, sym_arg in (
                (self.pattern_engine, True),
                (self.company_intelligence, True),
                (self.event_intelligence, True),
                (self.fno_engine, True),
            ):
                if engine is None:
                    continue
                try:
                    evidence += engine.build_evidence(symbol)
                except Exception:
                    pass

            validated = self.evidence_validator.validate(
                evidence
            )
            snapshot = self.conviction_engine.evaluate(
                validated
            )
            return float(snapshot.get("score") or 0)
        except Exception:
            return 0.0

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