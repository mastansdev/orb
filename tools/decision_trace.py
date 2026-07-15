from datetime import datetime


class DecisionTrace:
    """
    Records every decision made by the
    TradeSelectionEngine and Brain.

    Development Tool.
    """

    ENABLED = True
    BUY_ONLY = True

    def __init__(self):
        pass

    def trace(
        self,
        symbol,
        orb,
        intelligence,
        evidence,
        conviction,
        brain_decision,
        final_decision,
    ):
        if not self.ENABLED:
            return
        if self.BUY_ONLY and final_decision != "BUY":
            return

        print()
        print("=" * 80)
        print(f"SYMBOL : {symbol}")
        print("=" * 80)

        print(f"Time           : {datetime.now().strftime('%H:%M:%S')}")
        print(f"Decision       : {final_decision}")

        print()

        print("ORB")
        print("-" * 40)
        print(orb)

        print()

        print("INTELLIGENCE")
        print("-" * 40)
        print(intelligence)

        print()

        print("EVIDENCE")
        print("-" * 40)
        print(evidence)

        print()

        print("CONVICTION")
        print("-" * 40)
        print(conviction)

        print()

        print("BRAIN DECISION")
        print("-" * 40)
        print(brain_decision)

        print("=" * 80)