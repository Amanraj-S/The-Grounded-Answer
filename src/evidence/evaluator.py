from dataclasses import dataclass
from typing import Dict, List


@dataclass
class EvidenceDecision:
    """
    Represents the decision made by the evidence layer.
    """

    decision: str
    reason: str
    evidence: List[Dict]


class EvidenceEvaluator:
    """
    Determines whether retrieved policy evidence is
    sufficiently relevant and strong enough to proceed.

    This layer does NOT detect contradictions.

    Contradiction detection is handled separately by
    ContradictionDetector.
    """

    def __init__(
        self,
        minimum_score: float = 0.45,
        strong_score: float = 0.50,
    ):
        self.minimum_score = minimum_score
        self.strong_score = strong_score

    def evaluate(
        self,
        results: List[Dict],
    ) -> EvidenceDecision:

        # ---------------------------------------------
        # 1. No evidence
        # ---------------------------------------------

        if not results:

            return EvidenceDecision(
                decision="REFUSE",
                reason=(
                    "No policy evidence was retrieved."
                ),
                evidence=[],
            )

        # ---------------------------------------------
        # 2. Remove weak evidence
        # ---------------------------------------------

        relevant_results = [
            result
            for result in results
            if result["score"] >= self.minimum_score
        ]

        if not relevant_results:

            return EvidenceDecision(
                decision="REFUSE",
                reason=(
                    "The retrieved policy provisions are "
                    "not relevant enough to support an answer."
                ),
                evidence=[],
            )

        # ---------------------------------------------
        # 3. Check strongest evidence
        # ---------------------------------------------

        strongest_score = max(
            result["score"]
            for result in relevant_results
        )

        if strongest_score >= self.strong_score:

            return EvidenceDecision(
                decision="ANSWER",
                reason=(
                    "Sufficiently relevant policy evidence "
                    "was retrieved."
                ),
                evidence=relevant_results,
            )

        # ---------------------------------------------
        # 4. Evidence is too weak
        # ---------------------------------------------

        return EvidenceDecision(
            decision="REFUSE",
            reason=(
                "The retrieved evidence is too weak "
                "to support a reliable answer."
            ),
            evidence=relevant_results,
        )