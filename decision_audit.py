from copy import deepcopy
from datetime import datetime


class DecisionAudit:
    """
    Records the complete lifecycle of every trade decision.

    Responsibility:
        • Record decision snapshots
        • Record portfolio approval/rejection
        • Record execution details
        • Record trade outcome

    This module NEVER influences trading decisions.
    """

    def __init__(self):
        self.audit_log = {}

    # --------------------------------------------------
    # Decision Layer
    # --------------------------------------------------

    def record_decision(
        self,
        security_id,
        symbol,
        decision
    ):
        self.audit_log[security_id] = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "decision": deepcopy(decision),
            "portfolio": None,
            "execution": None,
            "result": None
        }

    # --------------------------------------------------
    # Portfolio Layer
    # --------------------------------------------------

    def record_portfolio_decision(
        self,
        security_id,
        portfolio_decision
    ):
        if security_id not in self.audit_log:
            return

        self.audit_log[security_id]["portfolio"] = deepcopy(
            portfolio_decision
        )

    # --------------------------------------------------
    # Execution Layer
    # --------------------------------------------------

    def record_execution(
        self,
        security_id,
        execution
    ):
        if security_id not in self.audit_log:
            return

        self.audit_log[security_id]["execution"] = deepcopy(
            execution
        )

    # --------------------------------------------------
    # Trade Result
    # --------------------------------------------------

    def record_result(
        self,
        security_id,
        result
    ):
        if security_id not in self.audit_log:
            return

        self.audit_log[security_id]["result"] = deepcopy(
            result
        )

    # --------------------------------------------------
    # Query APIs
    # --------------------------------------------------

    def get(self, security_id):
        return deepcopy(
            self.audit_log.get(security_id)
        )

    def all(self):
        return deepcopy(self.audit_log)

    def clear(self):
        self.audit_log.clear()