from dataclasses import dataclass
from typing import List, Dict


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
    sufficient to proceed to answer generation.

    This layer does NOT generate the final answer.
    It only decides whether answering is appropriate.
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
        results: List[Dict]
    ) -> EvidenceDecision:

        if not results:
            return EvidenceDecision(
                decision="REFUSE",
                reason="No policy evidence was retrieved.",
                evidence=[]
            )

        # Remove results below the minimum relevance threshold.
        relevant_results = [
            result
            for result in results
            if result["score"] >= self.minimum_score
        ]

        if not relevant_results:
            return EvidenceDecision(
                decision="REFUSE",
                reason=(
                    "The retrieved policy provisions are not "
                    "relevant enough to support an answer."
                ),
                evidence=[]
            )

        # If the strongest result is sufficiently relevant,
        # allow the answer stage to continue.
        strongest_score = relevant_results[0]["score"]

        if strongest_score >= self.strong_score:
            return EvidenceDecision(
                decision="ANSWER",
                reason=(
                    "Sufficiently relevant policy evidence "
                    "was retrieved."
                ),
                evidence=relevant_results
            )

        return EvidenceDecision(
            decision="REFUSE",
            reason=(
                "The retrieved evidence is too weak to "
                "support a reliable answer."
            ),
            evidence=relevant_results
        )