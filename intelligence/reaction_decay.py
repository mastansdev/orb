"""
==========================================================
Reaction Decay Engine
==========================================================

The idea, in the user's words:

    "1st shock triggers massive bearishness. 2nd triggers
     less than the 1st, because it is known to the market
     prior, and so on."

This is the ANTICIPATION EFFECT: as an event type recurs
and the market learns to expect it, the abnormal (market-
adjusted) price reaction SHRINKS. The first USFDA warning
on a stock is a bloodbath; the fifth is a shrug.

This engine measures that decay from the bot's own graded
history (abnormal_move per event type, oldest → newest)
and gives the Brain two things:

    1. expected_magnitude(event_type)
       — how big should the NEXT shock of this type be,
         given the decay trend?

    2. decay_multiplier(event_type)
       — a 0..1 scaler applied to fresh evidence of this
         type, so a "known" recurring catalyst carries
         LESS conviction than a first-of-kind shock.

Method
------
For each event type, take the chronological series of
|abnormal_move| values. Fit the trend: compare the mean
of the FIRST third vs the LAST third. If later shocks are
smaller, the type is DECAYING (priced-in over time) and
the multiplier drops toward a floor. If later shocks are
as big or bigger, the type stays fully weighted (a
genuinely repricing catalyst that the market never
fully anticipates).

Honest gating: needs a minimum sample; below it, returns
neutral (multiplier 1.0, "insufficient history"). Never
invents a trend.

This engine NEVER trades.

Author : H&M ORB AUTO TRADER
==========================================================
"""


class ReactionDecayEngine:

    MIN_SAMPLES = 4
    DECAY_FLOOR = 0.35     # a known catalyst still carries ≥35%
    RECENCY_WEIGHT = 0.6   # weight on the recent-third mean

    def __init__(self, repository):
        self.repository = repository

    # --------------------------------------------------

    def _series(self, event_type):
        if self.repository is None or not event_type:
            return []

        try:
            rows = self.repository.event_type_abnormal_series(
                event_type
            )
        except Exception:
            return []

        return [
            abs(float(r["abnormal_move"]))
            for r in rows
            if r.get("abnormal_move") is not None
        ]

    # --------------------------------------------------

    def model(self, event_type):
        """
        Full reaction model for one event type.
        """
        series = self._series(event_type)
        n = len(series)

        if n < self.MIN_SAMPLES:
            return {
                "event_type": event_type,
                "samples": n,
                "status": "INSUFFICIENT",
                "first_mean": None,
                "recent_mean": None,
                "decay_ratio": None,
                "expected_magnitude": None,
                "multiplier": 1.0,
            }

        third = max(1, n // 3)
        first_third = series[:third]
        recent_third = series[-third:]

        first_mean = sum(first_third) / len(first_third)
        recent_mean = sum(recent_third) / len(recent_third)
        overall_mean = sum(series) / n

        # Decay ratio: recent vs first. <1 = shocks shrinking.
        decay_ratio = (
            recent_mean / first_mean
            if first_mean > 1e-9 else 1.0
        )

        # Expected next magnitude: recency-weighted blend
        expected = (
            self.RECENCY_WEIGHT * recent_mean
            + (1 - self.RECENCY_WEIGHT) * overall_mean
        )

        # Evidence multiplier: if reactions are decaying,
        # scale conviction down toward the floor.
        if decay_ratio >= 1.0:
            multiplier = 1.0
            status = "STABLE"
        else:
            # decay_ratio in (0,1): map to (floor,1)
            multiplier = max(
                self.DECAY_FLOOR,
                self.DECAY_FLOOR
                + (1 - self.DECAY_FLOOR) * decay_ratio
            )
            status = "DECAYING"

        return {
            "event_type": event_type,
            "samples": n,
            "status": status,
            "first_mean": round(first_mean, 2),
            "recent_mean": round(recent_mean, 2),
            "decay_ratio": round(decay_ratio, 2),
            "expected_magnitude": round(expected, 2),
            "multiplier": round(multiplier, 2),
        }

    # --------------------------------------------------

    def multiplier(self, event_type):
        """0..1 conviction scaler for fresh evidence."""
        return self.model(event_type)["multiplier"]

    # --------------------------------------------------

    def expected_magnitude(self, event_type):
        """Expected |abnormal move| of the next such shock."""
        return self.model(event_type)["expected_magnitude"]

    # --------------------------------------------------

    def report(self, event_type=None):
        if event_type:
            m = self.model(event_type)
            if m["status"] == "INSUFFICIENT":
                return (
                    f"REACTION DECAY : {event_type}\n\n"
                    f"Insufficient history "
                    f"({m['samples']}/{self.MIN_SAMPLES} "
                    f"graded). Builds as events recur and "
                    f"get graded at /eod."
                )
            if m["status"] == "DECAYING":
                arrow = "↓ decaying"
                interp = (
                    "moves the stock LESS than the first "
                    "one did — the market has priced it in."
                )
            else:
                arrow = "→ stable"
                interp = (
                    "moves the stock as much as ever — the "
                    "market never fully anticipates it."
                )

            return (
                f"REACTION DECAY : {event_type}\n\n"
                f"Samples        : {m['samples']}\n"
                f"First shocks   : {m['first_mean']}% avg\n"
                f"Recent shocks  : {m['recent_mean']}% avg\n"
                f"Trend          : {arrow} "
                f"(ratio {m['decay_ratio']})\n"
                f"Next expected  : ~{m['expected_magnitude']}%\n"
                f"Evidence weight: ×{m['multiplier']}\n\n"
                f"Interpretation : a fresh {event_type} now "
                f"{interp}"
            )

        # Overview of all modelled types
        try:
            types = self.repository.known_event_types(
                self.MIN_SAMPLES
            )
        except Exception:
            types = []

        if not types:
            return (
                "SHOCK DECAY MODEL\n\nNo event type has "
                f"{self.MIN_SAMPLES}+ graded reactions yet. "
                "Models build automatically as events recur "
                "and are graded each /eod."
            )

        lines = ["SHOCK DECAY MODEL", ""]
        for t in types[:15]:
            m = self.model(t["event_type"])
            if m["status"] == "INSUFFICIENT":
                continue
            arrow = "↓" if m["status"] == "DECAYING" else "→"
            lines.append(
                f"{arrow} {m['event_type']}: "
                f"{m['first_mean']}%→{m['recent_mean']}% "
                f"(×{m['multiplier']}, n={m['samples']})"
            )

        lines.append("")
        lines.append(
            "↓ = each new shock smaller (priced-in). "
            "Evidence weight scales down accordingly."
        )
        return "\n".join(lines)
