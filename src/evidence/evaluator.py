from dataclasses import dataclass
from typing import List, Dict

from src.evidence.contradiction import ContradictionDetector


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
    It decides whether answering is appropriate.

    Contradictory evidence always takes priority over
    the relevance score.
    """

    def __init__(
        self,
        minimum_score: float = 0.45,
        strong_score: float = 0.50,
    ):
        self.minimum_score = minimum_score
        self.strong_score = strong_score

        # Create the contradiction detector once
        self.contradiction_detector = ContradictionDetector()

    def evaluate(
        self,
        results: List[Dict]
    ) -> EvidenceDecision:

        # --------------------------------------------------
        # 1. No evidence
        # --------------------------------------------------

        if not results:
            return EvidenceDecision(
                decision="REFUSE",
                reason="No policy evidence was retrieved.",
                evidence=[]
            )

        # --------------------------------------------------
        # 2. Remove weakly relevant evidence
        # --------------------------------------------------

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

        # --------------------------------------------------
        # 3. Check for contradiction
        # --------------------------------------------------

        contradiction = self.contradiction_detector.detect(
            relevant_results
        )

        if contradiction.conflict:

            return EvidenceDecision(
                decision="REFUSE",
                reason=(
                    "The retrieved policy provisions contain "
                    "a potential contradiction. A definitive "
                    "answer cannot be given from the manual."
                ),
                evidence=contradiction.clauses
            )

        # --------------------------------------------------
        # 4. Check evidence strength
        # --------------------------------------------------

        strongest_score = relevant_results[0]["score"]

        if strongest_score >= self.strong_score:

            return EvidenceDecision(
                decision="ANSWER",
                reason=(
                    "Sufficiently relevant policy evidence "
                    "was retrieved and no contradiction "
                    "was detected."
                ),
                evidence=relevant_results
            )

        # --------------------------------------------------
        # 5. Evidence is too weak
        # --------------------------------------------------

        return EvidenceDecision(
            decision="REFUSE",
            reason=(
                "The retrieved evidence is too weak to "
                "support a reliable answer."
            ),
            evidence=relevant_results
        )