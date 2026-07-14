from dataclasses import dataclass
from config import MIN_QTY, MIN_TRADE_VALUE


@dataclass
class TradePolicyDecision:
    approved: bool
    reason: str = ""


class TradePolicyManager:

    def __init__(self):
        pass

    # --------------------------------------------------

    def validate(
        self,
        quantity: int,
        trade_value: float
    ) -> TradePolicyDecision:
        """
        Validate account / broker / execution policies.

        This class NEVER evaluates market quality.
        It ONLY evaluates trading policies.
        """
        # ---------------------------------
        # Minimum Quantity
        # ---------------------------------
        if quantity < MIN_QTY:
            return TradePolicyDecision(
                approved=False,
                reason=(
                    f"Quantity ({quantity}) "
                    f"below minimum ({MIN_QTY})"
                )
            )

        # ---------------------------------
        # Minimum Trade Value
        # ---------------------------------
        if trade_value < MIN_TRADE_VALUE:
            return TradePolicyDecision(
                approved=False,
                reason=(
                    f"Trade Value ({trade_value:.2f}) "
                    f"below minimum ({MIN_TRADE_VALUE})"
                )
            )

        # ---------------------------------
        return TradePolicyDecision(
            approved=True,
            reason="Policy Approved"
        )