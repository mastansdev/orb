from copy import deepcopy


class EvidenceValidator:
    """
    Institutional Evidence Validator

    Responsibility:
        • Validate evidence before conviction
        • Apply evidence lifecycle rules
        • Remove invalid evidence
        • Normalize validated evidence

    It NEVER:
        • calculates conviction
        • scores trades
        • executes trades
        • fetches market data
    """

    def __init__(self):
        pass

    # --------------------------------------------------

    def validate(
        self,
        evidence
    ):

        """
        Phase 1

        No validation rules yet.

        Simply returns the evidence unchanged.

        Future phases will evaluate:

        • Freshness
        • Validity
        • Expiration
        • Provider-specific lifecycle
        """

        return deepcopy(evidence)