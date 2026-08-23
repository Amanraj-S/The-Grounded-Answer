from dataclasses import dataclass
from typing import Dict, List


@dataclass
class AnswerResult:
    """
    Represents the final answer produced from
    validated policy evidence.
    """

    answer: str
    citations: List[Dict]


class AnswerGenerator:
    """
    Generates a human-readable answer from evidence
    that has already passed the evidence and
    contradiction checks.

    This layer does NOT:
    - retrieve policy
    - choose policy versions
    - detect contradictions
    - make new policy decisions

    It only formats validated evidence into
    a grounded answer.
    """

    def generate(
        self,
        question: str,
        evidence: List[Dict],
    ) -> AnswerResult:

        # ---------------------------------------------
        # No validated evidence
        # ---------------------------------------------

        if not evidence:

            return AnswerResult(
                answer=(
                    "I cannot provide an answer because "
                    "no validated policy evidence is available."
                ),
                citations=[],
            )

        # ---------------------------------------------
        # Select the provision that best answers
        # the user's question.
        # ---------------------------------------------

        strongest = self._select_best_provision(
            question=question,
            evidence=evidence,
        )

        # ---------------------------------------------
        # Build grounded answer
        # ---------------------------------------------

        answer = self._build_answer(
            question=question,
            provision=strongest,
        )

        # ---------------------------------------------
        # Build citations
        # ---------------------------------------------

        citations = self._build_citations(
            evidence=evidence,
            primary=strongest,
        )

        return AnswerResult(
            answer=answer,
            citations=citations,
        )

    # =================================================
    # Select best provision
    # =================================================

    @staticmethod
    def _select_best_provision(
        question: str,
        evidence: List[Dict],
    ) -> Dict:
        """
        Select the most useful validated provision.

        Direct policy language receives priority.
        FAISS score is used as the fallback signal.
        """

        question_lower = question.lower()

        scored_provisions = []

        for provision in evidence:

            text_lower = provision["text"].lower()

            relevance_bonus = 0

            # -----------------------------------------
            # Reporting questions
            # -----------------------------------------

            if any(
                term in question_lower
                for term in [
                    "report",
                    "reporting",
                    "change",
                    "income change",
                    "salary change",
                ]
            ):

                if "report" in text_lower:
                    relevance_bonus += 0.20

                if "calendar days" in text_lower:
                    relevance_bonus += 0.20

                if "change" in text_lower:
                    relevance_bonus += 0.10

            # -----------------------------------------
            # Threshold questions
            # -----------------------------------------

            if any(
                term in question_lower
                for term in [
                    "threshold",
                    "income limit",
                    "eligible",
                ]
            ):

                if "threshold" in text_lower:
                    relevance_bonus += 0.20

                if "$" in text_lower:
                    relevance_bonus += 0.10

            # -----------------------------------------
            # Sanction questions
            # -----------------------------------------

            if any(
                term in question_lower
                for term in [
                    "sanction",
                    "penalty",
                ]
            ):

                if "sanction" in text_lower:
                    relevance_bonus += 0.30

            # -----------------------------------------
            # Earnings disregard questions
            # -----------------------------------------

            if any(
                term in question_lower
                for term in [
                    "earnings disregard",
                    "disregard",
                ]
            ):

                if "disregard" in text_lower:
                    relevance_bonus += 0.30

            final_score = (
                provision["score"]
                + relevance_bonus
            )

            scored_provisions.append(
                (
                    final_score,
                    provision,
                )
            )

        # Highest combined score wins.
        scored_provisions.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return scored_provisions[0][1]

    # =================================================
    # Build answer
    # =================================================

    @staticmethod
    def _build_answer(
        question: str,
        provision: Dict,
    ) -> str:
        """
        Creates a grounded answer directly from
        the validated policy provision.

        The policy text is not rewritten or altered.
        """

        return (
            "According to the applicable policy provision:\n\n"
            f"{provision['text']}"
        )

    # =================================================
    # Build citations
    # =================================================

    @staticmethod
    def _build_citations(
        evidence: List[Dict],
        primary: Dict,
    ) -> List[Dict]:
        """
        Build structured citation information.

        The primary provision is placed first.
        """

        citations = []

        # ---------------------------------------------
        # Primary citation
        # ---------------------------------------------

        citations.append(
            {
                "citation": primary["citation"],
                "source": primary["source"],
                "version": primary["version"],
                "score": primary["score"],
                "primary": True,
            }
        )

        # ---------------------------------------------
        # Supporting citations
        # ---------------------------------------------

        for provision in evidence:

            if (
                provision["citation"]
                == primary["citation"]
            ):
                continue

            citations.append(
                {
                    "citation": provision["citation"],
                    "source": provision["source"],
                    "version": provision["version"],
                    "score": provision["score"],
                    "primary": False,
                }
            )

        return citations