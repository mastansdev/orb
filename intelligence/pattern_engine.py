"""
==========================================================
Pattern Engine
==========================================================

Mission
-------
Find repeated patterns in the system's own history and
convert them into Evidence for the Brain.

PROJECT_BRAIN_V2.md:

    "This stock has already failed three ORB
     breakouts today."
    "This sector has been leading for the last
     5 trading days."

That is exactly what this module answers.

Patterns detected (v1)
----------------------
1. Repeated ORB failure today          → negative evidence
2. Historical ORB failure rate         → negative evidence
3. Historical symbol win rate          → positive/negative
4. Sector leadership streak            → positive evidence
5. Sector historical performance       → context

This engine NEVER:
    • decides trades
    • executes anything
    • collects market data

It reads memory and emits Evidence.

Author : H&M ORB AUTO TRADER
==========================================================
"""

from intelligence.evidence import Evidence
from config import MAX_ORB_FAILURES_PER_DAY


class PatternEngine:

    def __init__(self, market_memory):
        self.market_memory = market_memory

    # --------------------------------------------------

    def build_evidence(self, symbol, sector=""):
        """
        Return a list of PATTERN Evidence objects
        for this candidate.
        """
        evidence_list = []

        # ---------------------------------
        # 1. Failed breakouts TODAY
        # ---------------------------------
        failures_today = self.market_memory.orb_failures_today(
            symbol
        )

        if failures_today >= MAX_ORB_FAILURES_PER_DAY:
            evidence_list.append(
                Evidence(
                    provider="PATTERN",
                    symbol=symbol,
                    recommendation="AVOID",
                    score=min(100, 40 + failures_today * 20),
                    confidence=90,
                    reason=(
                        f"{symbol} already failed "
                        f"{failures_today} ORB breakout(s) today"
                    ),
                    facts={
                        "pattern": "REPEATED_ORB_FAILURE_TODAY",
                        "failures_today": failures_today,
                    },
                )
            )

        # ---------------------------------
        # 2. Historical ORB behaviour
        # ---------------------------------
        orb_stats = self.market_memory.orb_stats(symbol)
        samples = orb_stats.get("samples", 0)
        win_rate = orb_stats.get("win_rate")

        if samples >= 5 and win_rate is not None:

            if win_rate <= 30:
                evidence_list.append(
                    Evidence(
                        provider="PATTERN",
                        symbol=symbol,
                        recommendation="AVOID",
                        score=60,
                        confidence=min(90, 40 + samples * 5),
                        reason=(
                            f"{symbol} historical ORB win rate "
                            f"only {win_rate}% ({samples} samples)"
                        ),
                        facts={
                            "pattern": "POOR_ORB_HISTORY",
                            "win_rate": win_rate,
                            "samples": samples,
                        },
                    )
                )

            elif win_rate >= 60:
                evidence_list.append(
                    Evidence(
                        provider="PATTERN",
                        symbol=symbol,
                        recommendation="BUY",
                        score=min(80, win_rate),
                        confidence=min(90, 40 + samples * 5),
                        reason=(
                            f"{symbol} historical ORB win rate "
                            f"{win_rate}% ({samples} samples)"
                        ),
                        facts={
                            "pattern": "STRONG_ORB_HISTORY",
                            "win_rate": win_rate,
                            "samples": samples,
                        },
                    )
                )

        # ---------------------------------
        # 3. Sector leadership streak
        # ---------------------------------
        if sector:
            streak = self.market_memory.sector_leadership_streak(
                sector
            )

            if streak >= 3:
                evidence_list.append(
                    Evidence(
                        provider="PATTERN",
                        symbol=symbol,
                        recommendation="BUY",
                        score=min(85, 50 + streak * 7),
                        confidence=80,
                        reason=(
                            f"{sector} sector top-3 for "
                            f"{streak} consecutive day(s)"
                        ),
                        facts={
                            "pattern": "SECTOR_LEADERSHIP_STREAK",
                            "sector": sector,
                            "streak_days": streak,
                        },
                    )
                )

        return evidence_list

    # --------------------------------------------------

    def report(self, symbol, sector=""):
        """
        Human-readable pattern report
        (used by Telegram /memory command).
        """
        orb_stats = self.market_memory.orb_stats(symbol)
        trade_stats = self.market_memory.symbol_trade_stats(
            symbol
        )
        failures_today = self.market_memory.orb_failures_today(
            symbol
        )

        lines = [
            f"PATTERN MEMORY : {symbol}",
            "",
            f"ORB Failures Today : {failures_today}",
            f"ORB Samples        : {orb_stats.get('samples', 0)}",
            f"ORB Win Rate       : {orb_stats.get('win_rate', 'N/A')}",
            f"Trades Recorded    : {trade_stats.get('trades', 0)}",
            f"Trade Win Rate     : {trade_stats.get('win_rate', 'N/A')}",
            f"Total PnL          : ₹{trade_stats.get('total_pnl', 0)}",
        ]

        if sector:
            streak = self.market_memory.sector_leadership_streak(
                sector
            )
            lines.append(
                f"Sector Streak      : {sector} top-3 "
                f"for {streak} day(s)"
            )

        return "\n".join(lines)
