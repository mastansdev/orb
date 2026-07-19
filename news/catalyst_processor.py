"""
==========================================================
Catalyst Processor
==========================================================

Mission
-------
Convert raw external events into structured Catalyst
objects understood by the Market Catalyst Engine.

Responsibilities
----------------
1. Normalize incoming events
2. Identify catalyst type
3. Build Catalyst object

Author : H&M ORB AUTO TRADER
==========================================================
"""

from datetime import datetime

from news.market_catalyst_engine import (
    Catalyst,
    CatalystType,
    Impact
)


class CatalystProcessor:

    def process_event(
        self,
        event: dict
    ) -> Catalyst:

        """
        Expected Event Format

        {
            "title": "...",
            "source": "...",
            "type": "...",
            "impact": "...",
            "reason": "...",
            "priority": 90
        }
        """

        catalyst = Catalyst(

            title=event.get("title", ""),

            source=event.get("source", "UNKNOWN"),

            timestamp=datetime.now(),

            catalyst_type=self._parse_type(

                event.get("type", "")

            ),

            impact=self._parse_impact(

                event.get("impact", "LOW")

            ),

            priority=event.get("priority", 0),

            reason=event.get("reason", "")

        )

        return catalyst

    # --------------------------------------------------

    def _parse_type(
        self,
        value: str
    ):

        value = value.upper()

        try:

            return CatalystType[value]

        except Exception:

            return CatalystType.UNKNOWN

    # --------------------------------------------------

    def _parse_impact(
        self,
        value: str
    ):

        value = value.upper()

        try:

            return Impact[value]

        except Exception:

            return Impact.LOW