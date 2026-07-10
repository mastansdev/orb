"""
==========================================================
Position Intelligence Engine

Institutional Grade ORB Auto Trading Bot

Responsibilities
----------------
• Monitor intelligence events
• Match open positions
• Evaluate impact
• Recommend actions

This module NEVER executes trades.

Only the Brain is allowed to take trading decisions.
==========================================================
"""

from __future__ import annotations

from datetime import datetime


class PositionIntelligenceEngine:
    """
    Position Intelligence Engine

    Flow
    ----
    Intelligence Event
            ↓
    Match Open Positions
            ↓
    Evaluate Impact
            ↓
    Generate Recommendation
            ↓
    Brain
    """

    # ======================================================
    # Impact Levels
    # ======================================================

    CRITICAL_POSITIVE = "CRITICAL_POSITIVE"
    HIGH_POSITIVE = "HIGH_POSITIVE"
    MODERATE_POSITIVE = "MODERATE_POSITIVE"

    NEUTRAL = "NEUTRAL"

    MODERATE_NEGATIVE = "MODERATE_NEGATIVE"
    HIGH_NEGATIVE = "HIGH_NEGATIVE"
    CRITICAL_NEGATIVE = "CRITICAL_NEGATIVE"

    # ======================================================
    # Recommendations
    # ======================================================

    IGNORE = "IGNORE"
    WATCH = "WATCH"
    HOLD = "HOLD"
    PROTECT = "PROTECT"
    TRAIL = "TRAIL"
    PARTIAL_EXIT = "PARTIAL_EXIT"
    FULL_EXIT = "FULL_EXIT"
    HOLD_FOR_EXTENSION = "HOLD_FOR_EXTENSION"

    def __init__(self):
        self.events_processed = 0
        self.positions_matched = 0
        self.last_event = None
        self.last_processed = None

    # ======================================================
    # Public API
    # ======================================================

    def process_event(
        self,
        event,
        open_positions,
    ):
        """
        Main entry point.

        Parameters
        ----------
        event : dict
        open_positions : dict

        Returns
        -------
        dict
        """
        self.events_processed += 1
        self.last_event = event
        self.last_processed = datetime.now()

        matched = self.match_positions(
            event,
            open_positions,
        )

        recommendations = []

        for position in matched:
            impact = self.evaluate_impact(
                event,
                position,
            )

            recommendation = self.recommend_action(
                impact,
                position,
            )

            recommendations.append(recommendation)

        return {
            "event": event,
            "matched_positions": len(matched),
            "recommendations": recommendations,
        }

    # ======================================================
    # Position Matcher
    # ======================================================

    def match_positions(
        self,
        event,
        open_positions,
    ):
        """
        Match intelligence event against
        currently open positions.

        Parameters
        ----------
        event : dict
        open_positions : dict

        Returns
        -------
        list
        """
        matched = []

        if not event:
            return matched

        if not open_positions:
            return matched

        affected_symbols = event.get("symbols", [])

        if not affected_symbols:
            symbol = event.get("symbol")
            if symbol:
                affected_symbols = [symbol]

        affected_symbols = {str(symbol).upper() for symbol in affected_symbols}

        for security_id, position in open_positions.items():
            position_symbol = str(position.get("symbol", "")).upper()

            if position_symbol in affected_symbols:
                matched.append(position)

        self.positions_matched += len(matched)
        return matched

    # ======================================================
    # Impact Evaluation
    # ======================================================

    def evaluate_impact(
        self,
        event,
        position,
    ):
        """
        Evaluate how an intelligence event
        affects an existing position.

        Parameters
        ----------
        event : dict
        position : dict

        Returns
        -------
        dict
        """
        result = {
            "symbol": position.get("symbol"),
            "impact": self.NEUTRAL,
            "confidence": 0,
            "severity": 0,
            "recommendation_required": False,
            "reason": "",
        }

        classification = str(event.get("classification", "")).upper()
        severity = int(event.get("severity", 0))
        confidence = int(event.get("confidence", 0))

        result["severity"] = severity
        result["confidence"] = confidence

        # ----------------------------------------------
        if classification == "POSITIVE":
            if severity >= 8:
                result["impact"] = self.CRITICAL_POSITIVE
            elif severity >= 6:
                result["impact"] = self.HIGH_POSITIVE
            else:
                result["impact"] = self.MODERATE_POSITIVE

        # ----------------------------------------------
        elif classification == "NEGATIVE":
            if severity >= 8:
                result["impact"] = self.CRITICAL_NEGATIVE
            elif severity >= 6:
                result["impact"] = self.HIGH_NEGATIVE
            else:
                result["impact"] = self.MODERATE_NEGATIVE

        # ----------------------------------------------
        else:
            result["impact"] = self.NEUTRAL

        result["recommendation_required"] = result["impact"] != self.NEUTRAL
        result["reason"] = event.get("headline", "")

        return result

    # ======================================================
    # Recommendation Engine
    # ======================================================

    def recommend_action(
        self,
        impact,
        position,
    ):
        """
        Generate a recommendation for an
        open position.

        Parameters
        ----------
        impact : dict
        position : dict

        Returns
        -------
        dict
        """
        recommendation = {
            "symbol": position.get("symbol"),
            "action": self.IGNORE,
            "priority": 0,
            "reason": impact.get("reason", ""),
            "impact": impact.get("impact"),
        }

        impact_level = impact.get("impact")

        # --------------------------------------------------
        if impact_level == self.CRITICAL_NEGATIVE:
            recommendation["action"] = self.FULL_EXIT
            recommendation["priority"] = 100

        # --------------------------------------------------
        elif impact_level == self.HIGH_NEGATIVE:
            recommendation["action"] = self.PROTECT
            recommendation["priority"] = 90

        # --------------------------------------------------
        elif impact_level == self.MODERATE_NEGATIVE:
            recommendation["action"] = self.WATCH
            recommendation["priority"] = 70

        # --------------------------------------------------
        elif impact_level == self.CRITICAL_POSITIVE:
            recommendation["action"] = self.HOLD_FOR_EXTENSION
            recommendation["priority"] = 100

        # --------------------------------------------------
        elif impact_level == self.HIGH_POSITIVE:
            recommendation["action"] = self.TRAIL
            recommendation["priority"] = 90

        # --------------------------------------------------
        elif impact_level == self.MODERATE_POSITIVE:
            recommendation["action"] = self.HOLD
            recommendation["priority"] = 70

        # --------------------------------------------------
        else:
            recommendation["action"] = self.IGNORE
            recommendation["priority"] = 0

        return recommendation

    # ======================================================
    # Statistics
    # ======================================================

    def statistics(self):
        return {
            "events_processed": self.events_processed,
            "positions_matched": self.positions_matched,
            "last_processed": self.last_processed,
        }