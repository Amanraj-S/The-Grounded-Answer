import re

from dataclasses import dataclass
from typing import Dict, List, Optional, Set


@dataclass
class EvidenceDecision:
    """
    Represents the decision made by the evidence layer.

    Possible decisions:

        ANSWER
            Strong and directly relevant evidence was found.

        NOT_COVERED
            The retrieved policy evidence is related to the
            question but does not directly support an answer.

        REFUSE
            The evidence contains a problem that prevents
            a reliable answer, such as a contradiction.
    """

    decision: str
    reason: str
    evidence: List[Dict]


class EvidenceEvaluator:
    """
    Determines whether retrieved policy evidence is
    sufficiently relevant and strong enough to support
    an answer.

    This layer does NOT:

    - generate the final answer
    - select policy versions
    - detect contradictions

    Contradiction detection remains handled separately by
    ContradictionDetector.

    The evaluator now performs two levels of validation:

        1. Semantic relevance
           ------------------
           FAISS retrieval score must be sufficiently strong.

        2. Direct textual support
           -----------------------
           Retrieved evidence must contain meaningful
           concepts related to the actual question.

    This prevents semantically related but unsupported
    questions from being incorrectly answered.
    """

    # ---------------------------------------------------------
    # Common words that should not count as evidence overlap.
    # ---------------------------------------------------------

    STOP_WORDS: Set[str] = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "to",
        "of",
        "in",
        "on",
        "for",
        "from",
        "with",
        "under",
        "after",
        "before",
        "what",
        "when",
        "where",
        "which",
        "who",
        "how",
        "why",
        "does",
        "do",
        "did",
        "can",
        "could",
        "would",
        "should",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "my",
        "me",
        "i",
        "we",
        "you",
        "your",
        "it",
        "this",
        "that",
        "these",
        "those",
        "their",
        "they",
        "them",
        "have",
        "has",
        "had",
        "must",
        "may",
        "shall",
        "will",
        "within",
        "required",
        "according",
        "under",
    }

    # ---------------------------------------------------------
    # Important policy concepts.
    #
    # These are concepts rather than complete answers.
    # They help determine whether retrieved evidence is
    # discussing the same subject as the question.
    # ---------------------------------------------------------

    CONCEPT_GROUPS = {

        "reporting": {
            "report",
            "reporting",
            "reported",
            "change",
            "changes",
            "income",
            "circumstance",
            "circumstances",
            "notification",
        },

        "income_threshold": {
            "income",
            "threshold",
            "limit",
            "household",
            "monthly",
            "earnings",
        },

        "earnings_disregard": {
            "earnings",
            "disregard",
            "disregarded",
            "employment",
            "household",
        },

        "sanction": {
            "sanction",
            "sanctions",
            "reduction",
            "award",
            "percentage",
            "period",
        },

        "overpayment": {
            "overpayment",
            "overpaid",
            "recoverable",
            "recovery",
            "report",
            "change",
        },

        # These concepts are intentionally independent.
        #
        # A document talking about household support does
        # NOT automatically support a question about loans
        # or childcare.
        "childcare": {
            "childcare",
            "child",
            "children",
            "nursery",
            "daycare",
        },

        "loan": {
            "loan",
            "loans",
            "lending",
            "borrow",
            "borrowing",
            "debt",
        },

        "legal_representation": {
            "legal",
            "lawyer",
            "solicitor",
            "representation",
            "representative",
            "counsel",
        },
    }

    def __init__(
        self,
        minimum_score: float = 0.45,
        strong_score: float = 0.50,
        minimum_keyword_overlap: float = 0.12,
        minimum_concept_overlap: float = 1.0,
    ):
        self.minimum_score = minimum_score
        self.strong_score = strong_score
        self.minimum_keyword_overlap = (
            minimum_keyword_overlap
        )
        self.minimum_concept_overlap = (
            minimum_concept_overlap
        )

    # =========================================================
    # MAIN EVALUATION
    # =========================================================

    def evaluate(
        self,
        results: List[Dict],
        question: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> EvidenceDecision:

        # -----------------------------------------------------
        # 1. No evidence
        # -----------------------------------------------------

        if not results:

            return EvidenceDecision(
                decision="NOT_COVERED",
                reason=(
                    "No relevant policy evidence was "
                    "retrieved for the question."
                ),
                evidence=[],
            )

        # -----------------------------------------------------
        # 2. Remove weak semantic evidence
        # -----------------------------------------------------

        relevant_results = [
            result
            for result in results
            if result.get("score", 0.0)
            >= self.minimum_score
        ]

        if not relevant_results:

            return EvidenceDecision(
                decision="NOT_COVERED",
                reason=(
                    "The retrieved policy provisions are "
                    "not relevant enough to support an answer. "
                    "The policy manual may not cover this question."
                ),
                evidence=[],
            )

        # -----------------------------------------------------
        # 3. If the caller does not provide the question,
        #    preserve the original score-based behaviour.
        #
        # This keeps the component backward compatible with
        # existing tests and direct callers.
        # -----------------------------------------------------

        if not question:

            strongest_score = max(
                result.get("score", 0.0)
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

            return EvidenceDecision(
                decision="NOT_COVERED",
                reason=(
                    "The retrieved policy evidence is too weak "
                    "to establish that the policy manual covers "
                    "this question."
                ),
                evidence=relevant_results,
            )

        # -----------------------------------------------------
        # 4. Direct-support evaluation
        # -----------------------------------------------------

        directly_supported = []

        for result in relevant_results:

            support_score = (
                self._direct_support_score(
                    question=question,
                    evidence=result.get(
                        "text",
                        "",
                    ),
                    topic=topic,
                )
            )

            result_copy = result.copy()

            result_copy[
                "direct_support_score"
            ] = support_score

            if self._is_directly_supported(
                question=question,
                evidence=result.get(
                    "text",
                    "",
                ),
                topic=topic,
                support_score=support_score,
            ):

                directly_supported.append(
                    result_copy
                )

        # -----------------------------------------------------
        # 5. No direct support
        #
        # This is the important protection against:
        #
        # "loan" -> general recipient obligations
        # "childcare" -> general household support description
        #
        # being incorrectly converted into ANSWER.
        # -----------------------------------------------------

        if not directly_supported:

            return EvidenceDecision(
                decision="NOT_COVERED",
                reason=(
                    "The retrieved policy provisions are "
                    "semantically related to the question, "
                    "but they do not directly support the "
                    "specific claim being asked."
                ),
                evidence=relevant_results,
            )

        # -----------------------------------------------------
        # 6. Strong semantic + direct evidence
        # -----------------------------------------------------

        strongest_direct_score = max(
            result.get(
                "score",
                0.0,
            )
            for result in directly_supported
        )

        if strongest_direct_score >= self.strong_score:

            return EvidenceDecision(
                decision="ANSWER",
                reason=(
                    "Strong policy evidence was retrieved "
                    "and the evidence directly supports the "
                    "subject of the question."
                ),
                evidence=directly_supported,
            )

        # -----------------------------------------------------
        # 7. Evidence is related but insufficiently strong
        # -----------------------------------------------------

        return EvidenceDecision(
            decision="NOT_COVERED",
            reason=(
                "The retrieved evidence discusses the "
                "question's subject but is not strong enough "
                "to establish a reliable policy answer."
            ),
            evidence=directly_supported,
        )

    # =========================================================
    # DIRECT SUPPORT
    # =========================================================

    def _is_directly_supported(
        self,
        question: str,
        evidence: str,
        topic: Optional[str],
        support_score: float,
    ) -> bool:

        if not evidence.strip():
            return False

        # -----------------------------------------------------
        # Explicit section reference.
        #
        # If the user asks for §10.5.2 and the evidence is
        # actually §10.5.2, that is strong direct evidence.
        # -----------------------------------------------------

        requested_sections = self._extract_sections(
            question
        )

        evidence_sections = self._extract_sections(
            evidence
        )

        if requested_sections:

            if requested_sections.intersection(
                evidence_sections
            ):

                return True

        # -----------------------------------------------------
        # Concept matching.
        # -----------------------------------------------------

        question_concepts = (
            self._extract_concepts(
                question
            )
        )

        evidence_concepts = (
            self._extract_concepts(
                evidence
            )
        )

        # If the question contains a specific concept such
        # as "loan", "childcare", or "legal representation",
        # evidence must contain that concept.
        #
        # This is the main false-positive protection.
        # -----------------------------------------------------

        specific_concepts = (
            question_concepts
            & {
                "childcare",
                "loan",
                "legal_representation",
            }
        )

        if specific_concepts:

            if not specific_concepts.intersection(
                evidence_concepts
            ):
                return False

        # -----------------------------------------------------
        # Topic-aware support.
        # -----------------------------------------------------

        if topic:

            expected_concepts = (
                self._topic_concepts(topic)
            )

            if expected_concepts:

                concept_overlap = (
                    expected_concepts
                    & evidence_concepts
                )

                if not concept_overlap:
                    return False

        # -----------------------------------------------------
        # Keyword overlap.
        # -----------------------------------------------------

        keyword_overlap = (
            self._keyword_overlap(
                question,
                evidence,
            )
        )

        if keyword_overlap >= self.minimum_keyword_overlap:
            return True

        # -----------------------------------------------------
        # Concept overlap can still establish support when
        # wording differs.
        # -----------------------------------------------------

        if support_score >= self.minimum_concept_overlap:
            return True

        return False

    # =========================================================
    # SUPPORT SCORE
    # =========================================================

    def _direct_support_score(
        self,
        question: str,
        evidence: str,
        topic: Optional[str],
    ) -> float:

        question_words = self._keywords(
            question
        )

        evidence_words = self._keywords(
            evidence
        )

        if not question_words:
            return 0.0

        common_words = (
            question_words
            & evidence_words
        )

        keyword_ratio = (
            len(common_words)
            / len(question_words)
        )

        question_concepts = (
            self._extract_concepts(
                question
            )
        )

        evidence_concepts = (
            self._extract_concepts(
                evidence
            )
        )

        concept_overlap = len(
            question_concepts
            & evidence_concepts
        )

        # -----------------------------------------------------
        # Combine lexical and conceptual evidence.
        # -----------------------------------------------------

        return (
            keyword_ratio
            + float(concept_overlap)
        )

    # =========================================================
    # KEYWORD EXTRACTION
    # =========================================================

    def _keywords(
        self,
        text: str,
    ) -> Set[str]:

        tokens = re.findall(
            r"[a-zA-Z][a-zA-Z0-9_-]*",
            text.lower(),
        )

        return {
            token
            for token in tokens
            if token not in self.STOP_WORDS
            and len(token) > 2
        }

    # =========================================================
    # CONCEPT EXTRACTION
    # =========================================================

    @classmethod
    def _extract_concepts(
        cls,
        text: str,
    ) -> Set[str]:

        text_lower = text.lower()

        concepts = set()

        for concept, terms in (
            cls.CONCEPT_GROUPS.items()
        ):

            if any(
                term in text_lower
                for term in terms
            ):

                concepts.add(
                    concept
                )

        return concepts

    # =========================================================
    # TOPIC → CONCEPTS
    # =========================================================

    @classmethod
    def _topic_concepts(
        cls,
        topic: str,
    ) -> Set[str]:

        mapping = {

            "reporting_change": {
                "reporting",
            },

            "income_threshold": {
                "income_threshold",
            },

            "earnings_disregard": {
                "earnings_disregard",
            },

            "sanction": {
                "sanction",
            },

            "general": set(),
        }

        return mapping.get(
            topic,
            set(),
        )

    # =========================================================
    # KEYWORD OVERLAP
    # =========================================================

    def _keyword_overlap(
        self,
        question: str,
        evidence: str,
    ) -> float:

        question_words = self._keywords(
            question
        )

        evidence_words = self._keywords(
            evidence
        )

        if not question_words:
            return 0.0

        common = (
            question_words
            & evidence_words
        )

        return (
            len(common)
            / len(question_words)
        )

    # =========================================================
    # SECTION EXTRACTION
    # =========================================================

    @staticmethod
    def _extract_sections(
        text: str,
    ) -> Set[str]:

        matches = re.findall(
            r"§\s*\d+(?:\.\d+)+",
            text,
        )

        return {
            re.sub(
                r"\s+",
                "",
                match,
            ).lower()
            for match in matches
        }