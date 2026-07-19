"""
==========================================================
Causal Reasoning Engine
==========================================================

Mission
-------
Make the Brain reason like an institutional PM:

    Event
      → match causal models (knowledge base)
      → activate chains (1st/2nd/3rd order, damped)
      → resolve targets to actual symbols
      → merge with historical reaction memory
      → emit CAUSAL evidence with the full chain
        as the explanation

The Brain never reasons from scratch: every event is
interpreted through permanent institutional knowledge
(causal_knowledge.py) plus its own graded history
(event_type_reaction_stats).

Chains are restart-safe: rebuilt from the last 2 days
of persisted structured events on startup.

This engine NEVER:
    • trades
    • sizes positions
    • overrides the Risk Governor

Author : H&M ORB AUTO TRADER
==========================================================
"""

from datetime import datetime, timedelta

from intelligence.evidence import Evidence
from intelligence.causal_knowledge import CAUSAL_MODELS


class CausalReasoningEngine:

    # Order damping: 2nd order = half, 3rd = quarter
    ORDER_DAMPING = {1: 1.0, 2: 0.5, 3: 0.25}

    # Chain lifetime by model horizon
    HORIZON_HOURS = {
        "INTRADAY": 8,
        "SHORT": 48,
        "MEDIUM": 24 * 7,
        "LONG": 24 * 30,
    }

    # Minimum damped strength worth keeping
    MATERIALITY_FLOOR = 12.0

    def __init__(
        self,
        company_intelligence,
        repository=None
    ):
        self.company_intelligence = company_intelligence
        self.repository = repository

        # Active chains: list of dicts
        self.active_chains = []

        self.events_analyzed = 0

        self._rebuild_from_memory()

    # --------------------------------------------------
    # Matching
    # --------------------------------------------------

    @staticmethod
    def _event_text(event):
        return " ".join(
            str(event.get(field, "") or "")
            for field in (
                "event_type", "catalyst", "headline",
                "sector", "theme",
            )
        ).lower()

    # --------------------------------------------------

    def match_models(self, event):
        """
        Which causal models does this event activate?
        """
        text = self._event_text(event)

        if not text.strip():
            return []

        matched = []

        for model in CAUSAL_MODELS:
            for trigger in model["triggers"]:
                if trigger in text:
                    matched.append(model)
                    break

        return matched

    # --------------------------------------------------
    # Analysis
    # --------------------------------------------------

    def analyze(self, event):
        """
        Convert one structured event into active causal
        chains. Returns the chains created.
        """
        models = self.match_models(event)

        if not models:
            return []

        importance = float(
            event.get("importance", 50) or 50
        )
        importance_factor = min(
            1.5, max(0.4, importance / 60.0)
        )

        created = []

        for model in models:

            expires_at = datetime.now() + timedelta(
                hours=self.HORIZON_HOURS.get(
                    model["horizon"], 48
                )
            )

            # Historical self-knowledge: how has this
            # event type actually behaved for us?
            history = self._history_context(
                event.get("event_type", "")
            )

            for effect in model["effects"]:

                damped = (
                    effect["strength"]
                    * self.ORDER_DAMPING.get(
                        effect["order"], 0.25
                    )
                    * importance_factor
                )

                if damped < self.MATERIALITY_FLOOR:
                    continue

                chain = {
                    "model_key": model["key"],
                    "category": model["category"],
                    "target": effect["target"].upper(),
                    "sign": effect["sign"],
                    "order": effect["order"],
                    "strength": round(min(100.0, damped), 1),
                    "confidence": model["base_confidence"],
                    "horizon": model["horizon"],
                    "root_cause": model["root_cause"],
                    "monitor": model["monitor"],
                    "source_headline": (
                        event.get("headline", "")[:100]
                    ),
                    "history": history,
                    "created_at": datetime.now(),
                    "expires_at": expires_at,
                }

                self.active_chains.append(chain)
                created.append(chain)

        if created:
            self.events_analyzed += 1
            print(
                f"[CAUSAL] {len(created)} chain(s) from "
                f"{[m['key'] for m in models]}"
            )

        # Bound memory
        self.active_chains = self.active_chains[-300:]

        return created

    # --------------------------------------------------

    def _history_context(self, event_type):
        """
        Own graded history for this event type
        (never reasons from scratch).
        """
        if self.repository is None or not event_type:
            return None

        try:
            stats = (
                self.repository
                    .event_type_reaction_stats(event_type)
            )
            if stats.get("samples", 0) >= 5:
                return stats
        except Exception:
            pass

        return None

    # --------------------------------------------------

    def _rebuild_from_memory(self):
        if self.repository is None:
            return

        try:
            since = (
                datetime.now() - timedelta(days=2)
            ).strftime("%Y-%m-%d")

            events = (
                self.repository
                    .recent_structured_events(since)
            )

            for event in events:
                self.analyze(event)

            if self.active_chains:
                print(
                    f"[CAUSAL] Rebuilt "
                    f"{len(self.active_chains)} chain(s) "
                    f"from memory"
                )

        except Exception as e:
            print(f"[CAUSAL] Rebuild failed: {e}")

    # --------------------------------------------------
    # Expiry
    # --------------------------------------------------

    def _prune(self):
        now = datetime.now()
        self.active_chains = [
            c for c in self.active_chains
            if c["expires_at"] > now
        ]

    # --------------------------------------------------
    # Symbol Resolution
    # --------------------------------------------------

    def _symbol_matches_target(self, symbol, target):
        """
        Does this company belong to the chain's target
        group? Matched against sector, industry, themes,
        and keywords (uppercase substring).
        """
        try:
            profile = (
                self.company_intelligence.get_profile(
                    symbol
                )
            )
        except Exception:
            return False

        haystack = " ".join([
            str(profile.get("sector", "")),
            str(profile.get("industry", "")),
            " ".join(profile.get("themes", []) or []),
            " ".join(profile.get("keywords", []) or []),
            str(profile.get("core_business", ""))[:200],
        ]).upper()

        return target in haystack

    # --------------------------------------------------

    def chains_for_symbol(self, symbol):
        self._prune()

        symbol = str(symbol).upper()
        matched = []

        for chain in self.active_chains:
            # Generic targets (AFFECTED / PROTECTED /
            # USER INDUSTRY / CHALLENGER / HIGH DEBT)
            # need entity-level mapping we don't have —
            # they surface in reports, not evidence.
            if chain["target"] in (
                "AFFECTED", "PROTECTED",
                "USER INDUSTRY", "CHALLENGER",
                "HIGH DEBT",
            ):
                continue

            if self._symbol_matches_target(
                symbol, chain["target"]
            ):
                matched.append(chain)

        return matched

    # --------------------------------------------------
    # Evidence
    # --------------------------------------------------

    def build_evidence(self, symbol):
        """
        CAUSAL evidence: the strongest active chain
        touching this symbol, with the full reasoning
        as explanation.
        """
        chains = self.chains_for_symbol(symbol)

        if not chains:
            return []

        # Net the chains: same symbol may sit in
        # positive and negative chains simultaneously
        net = sum(
            c["sign"] * c["strength"] for c in chains
        )

        strongest = max(
            chains, key=lambda c: c["strength"]
        )

        if abs(net) < self.MATERIALITY_FLOOR:
            return []

        recommendation = "BUY" if net > 0 else "SELL"

        reason = (
            f"Causal[{strongest['model_key']}] "
            f"O{strongest['order']} "
            f"{'+' if strongest['sign'] > 0 else '−'}"
            f"{strongest['target']}: "
            f"{strongest['root_cause'][:90]}"
        )

        if strongest.get("history"):
            h = strongest["history"]
            reason += (
                f" | own history: {h['avg_move']:+.1f}% "
                f"avg (n={h['samples']})"
            )

        confidence = strongest["confidence"]
        if len(chains) > 1:
            # Multiple independent chains agreeing/net
            confidence = min(90, confidence + 5 * (
                len(chains) - 1
            ))

        return [
            Evidence(
                provider="CAUSAL",
                symbol=symbol,
                recommendation=recommendation,
                score=min(100.0, abs(net)),
                confidence=confidence,
                reason=reason,
                facts={
                    "net_impact": round(net, 1),
                    "chains": len(chains),
                    "model": strongest["model_key"],
                    "order": strongest["order"],
                    "horizon": strongest["horizon"],
                    "monitor": strongest["monitor"][:150],
                },
            )
        ]

    # --------------------------------------------------
    # Reports
    # --------------------------------------------------

    def report(self, symbol=None):
        self._prune()

        if symbol:
            chains = self.chains_for_symbol(symbol)
            title = f"CAUSAL CHAINS : {symbol.upper()}"
        else:
            chains = sorted(
                self.active_chains,
                key=lambda c: -c["strength"],
            )
            title = "ACTIVE CAUSAL CHAINS"

        if not chains:
            return (
                f"{title}\n\nNone active. Chains activate "
                f"when macro/policy/commodity events hit "
                f"the news flow."
            )

        lines = [title, ""]

        seen_models = set()

        for chain in chains[:12]:
            sign = "▲" if chain["sign"] > 0 else "▼"
            lines.append(
                f"{sign} {chain['target']} "
                f"({chain['strength']:.0f}, "
                f"O{chain['order']}, {chain['horizon']}) "
                f"— {chain['model_key']}"
            )

            if chain["model_key"] not in seen_models:
                seen_models.add(chain["model_key"])
                lines.append(
                    f"   why: {chain['root_cause'][:100]}"
                )
                lines.append(
                    f"   watch: {chain['monitor'][:100]}"
                )

        lines.append("")
        lines.append(
            f"{len(chains)} chain(s) | "
            f"{len(CAUSAL_MODELS)} models in knowledge base"
        )

        return "\n".join(lines)

    # --------------------------------------------------

    def knowledge_summary(self):
        categories = {}
        for model in CAUSAL_MODELS:
            categories.setdefault(
                model["category"], 0
            )
            categories[model["category"]] += 1

        return {
            "models": len(CAUSAL_MODELS),
            "categories": categories,
        }
