"""
==========================================================
Event Intelligence Engine
==========================================================

Mission
-------
Convert every Market Story into STRUCTURED, PERMANENT
institutional intelligence — per stock.

    "L&T wins order" is a headline.
    {event_type, symbol, importance, severity,
     confidence, horizon, direction, similar-history}
    is intelligence.

Responsibilities
----------------
1. Transform stories into StructuredEvent records
2. Persist one record per (event, affected symbol)
   → this is the per-stock event memory
3. Attach historical similarity (same event type before)
4. Emit EVENT evidence for candidate evaluation

This engine NEVER:
    • trades
    • sizes positions
    • collects news itself

Author : H&M ORB AUTO TRADER
==========================================================
"""

from datetime import datetime

from evidence import Evidence


class EventIntelligence:

    # Story direction → evidence recommendation
    POSITIVE_DIRECTIONS = ("STRENGTHENING", "POSITIVE", "BULLISH")
    NEGATIVE_DIRECTIONS = (
        "WEAKENING", "CONTRADICTED", "NEGATIVE", "BEARISH"
    )

    # Evidence relevance window for intraday decisions
    EVIDENCE_MAX_AGE_DAYS = 2

    def __init__(self, repository, company_intelligence=None):
        self.repository = repository
        self.company_intelligence = company_intelligence

        # story_id → processed guard (session dedup)
        self._processed_stories = set()

        self.events_created = 0

    # --------------------------------------------------
    # Story → Structured Events
    # --------------------------------------------------

    def process_story(self, story):
        """
        Convert one MarketStory into structured events
        (one per affected symbol; one market-wide record
        when no symbols are mapped).

        Returns the list of created event dicts.
        """
        story_id = getattr(story, "story_id", None) or ""

        if story_id and story_id in self._processed_stories:
            return []

        if story_id:
            self._processed_stories.add(story_id)

        symbols = (
            getattr(story, "affected_symbols", None)
            or getattr(story, "symbols", None)
            or []
        )
        if isinstance(symbols, str):
            symbols = [symbols]

        base = {
            "event_type": getattr(story, "event_type", "") or "",
            "catalyst": getattr(story, "catalyst", "") or "",
            "sector": getattr(story, "sector", "") or "",
            "industry": getattr(story, "industry", "") or "",
            "theme": getattr(story, "theme", "") or "",
            "direction": getattr(story, "story_direction", "") or "",
            "importance": self._importance(story),
            "severity": float(
                getattr(story, "story_strength", 0) or 0
            ),
            "confidence": float(
                getattr(story, "confidence", 0) or 0
            ),
            "horizon": getattr(story, "expected_duration", "") or "",
            "headline": (getattr(story, "name", "") or "")[:300],
            "story_id": story_id,
        }

        created = []

        targets = [s for s in symbols if s] or [""]

        for symbol in targets:
            event = dict(base)
            event["symbol"] = str(symbol).upper()

            if self.repository is not None:
                try:
                    self.repository.save_structured_event(
                        event
                    )
                except Exception as e:
                    print(f"[EVENT] Persist failed: {e}")

            # Living company profile update
            if (
                event["symbol"]
                and self.company_intelligence is not None
            ):
                try:
                    self.company_intelligence.update_from_event(
                        event
                    )
                except Exception:
                    pass

            created.append(event)
            self.events_created += 1

        return created

    # --------------------------------------------------

    def _importance(self, story):
        """
        Importance = priority × confidence, 0-100.
        """
        priority = float(getattr(story, "priority", 0) or 0)
        confidence = float(getattr(story, "confidence", 0) or 0)

        return round(
            min(100.0, priority * (confidence / 100.0)),
            1
        )

    # --------------------------------------------------
    # Historical Similarity
    # --------------------------------------------------

    def expected_reaction(self, event_type):
        """
        Historical reaction distribution for this event
        type (only speaks with ≥ 5 graded samples —
        'insufficient history' is a legitimate answer).
        """
        if self.repository is None or not event_type:
            return None

        try:
            stats = (
                self.repository
                    .event_type_reaction_stats(event_type)
            )
        except Exception:
            return None

        if stats.get("samples", 0) < 5:
            return None

        return stats

    # --------------------------------------------------

    def write_outcomes(self, price_change_lookup):
        """
        EOD outcome write-back (called by the Engine).
        """
        if self.repository is None:
            return 0

        try:
            return self.repository.write_event_outcomes(
                price_change_lookup
            )
        except Exception as e:
            print(f"[EVENT] Outcome write-back failed: {e}")
            return 0

    # --------------------------------------------------

    def similar_history(self, event_type, limit=20):
        """
        'This event type has occurred before — what
        happened?' Returns prior instances (with
        realized moves once outcome write-back exists).
        """
        if self.repository is None or not event_type:
            return []

        try:
            return self.repository.event_type_history(
                event_type, limit
            )
        except Exception:
            return []

    # --------------------------------------------------
    # Evidence
    # --------------------------------------------------

    def build_evidence(self, symbol):
        """
        EVENT evidence for one candidate symbol:
        recent (≤ 2 days) structured events on the
        symbol, strongest first.
        """
        if self.repository is None:
            return []

        try:
            events = self.repository.symbol_structured_events(
                symbol, limit=5
            )
        except Exception:
            return []

        evidence_list = []

        for event in events:

            if not self._is_fresh(event.get("created_at", "")):
                continue

            direction = str(
                event.get("direction", "")
            ).upper()

            if direction in self.NEGATIVE_DIRECTIONS:
                recommendation = "SELL"
            elif direction in self.POSITIVE_DIRECTIONS:
                recommendation = "BUY"
            else:
                recommendation = "WAIT"

            importance = float(event.get("importance", 0) or 0)

            if importance < 20:
                continue

            history = self.similar_history(
                event.get("event_type", "")
            )

            # Predictive memory: what happened after
            # similar events (if enough graded samples)
            reaction = self.expected_reaction(
                event.get("event_type", "")
            )

            reason = (
                f"{event.get('event_type', 'EVENT')}: "
                f"{event.get('headline', '')[:80]} "
                f"(seen {len(history)}x before)"
            )

            facts = {
                "event_type": event.get("event_type"),
                "catalyst": event.get("catalyst"),
                "importance": importance,
                "horizon": event.get("horizon"),
                "historical_instances": len(history),
            }

            if reaction:
                reason += (
                    f" | hist avg move "
                    f"{reaction['avg_move']:+.1f}% "
                    f"±{reaction['std_move']:.1f} "
                    f"(n={reaction['samples']}, "
                    f"{reaction['positive_rate']}% up)"
                )
                facts["expected_reaction"] = reaction

            evidence_list.append(
                Evidence(
                    provider="EVENT",
                    symbol=symbol,
                    recommendation=recommendation,
                    score=min(100.0, importance),
                    confidence=float(
                        event.get("confidence", 0) or 0
                    ),
                    reason=reason,
                    facts=facts,
                )
            )

        return evidence_list

    # --------------------------------------------------

    def _is_fresh(self, created_at):
        try:
            created = datetime.strptime(
                created_at, "%Y-%m-%d %H:%M:%S"
            )
            age_days = (datetime.now() - created).days
            return age_days <= self.EVIDENCE_MAX_AGE_DAYS
        except Exception:
            return False

    # --------------------------------------------------
    # Reports
    # --------------------------------------------------

    def report(self, symbol=None, limit=8):
        """
        Human-readable event report
        (Telegram /events command).
        """
        if self.repository is None:
            return "Event memory unavailable."

        if symbol:
            events = self.repository.symbol_structured_events(
                symbol.upper(), limit
            )
            title = f"EVENT MEMORY : {symbol.upper()}"
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            events = self.repository.recent_structured_events(
                today, limit
            )
            title = "EVENTS TODAY"

        if not events:
            return f"{title}\n\nNo events recorded."

        lines = [title, ""]

        for event in events:
            lines.append(
                f"• [{event.get('event_type', '?')}] "
                f"{event.get('headline', '')[:70]}"
            )
            lines.append(
                f"   imp {event.get('importance', 0)} | "
                f"conf {event.get('confidence', 0)} | "
                f"{event.get('direction', '') or '—'}"
            )

        return "\n".join(lines)
