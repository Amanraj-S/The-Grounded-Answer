import json
import re
from pathlib import Path

import faiss
import numpy as np

from src.retrieval.embedder import PolicyEmbedder


INDEX_PATH = Path("index/policy.index")
METADATA_PATH = Path("index/metadata.json")


class PolicyRetriever:
    """
    Retrieves the most semantically relevant
    policy provisions for a user question.

    FAISS remains the primary semantic retrieval engine.

    Additional ranking adjustments are applied only when
    the user's question explicitly identifies:
        1. a policy section, or
        2. a specific policy concept.

    These adjustments do not replace FAISS retrieval.
    """

    # ---------------------------------------------------------
    # Explicit policy section references
    #
    # Examples:
    #   §10.5.2
    #   §6.4.1
    #   §4.3.2
    # ---------------------------------------------------------

    SECTION_PATTERN = re.compile(
        r"§\s*\d+(?:\.\d+)+"
    )

    # ---------------------------------------------------------
    # Policy concepts
    # ---------------------------------------------------------

    CONCEPT_PATTERNS = {
        "earnings_disregard": [
            "earnings disregard",
            "earnings are disregarded",
            "earnings disregarded",
            "disregarded per month",
            "how much of household earnings",
            "how much are earnings disregarded",
        ],

        "income_threshold": [
            "income threshold",
            "income thresholds",
            "monthly threshold",
            "monthly income threshold",
        ],

        "sanction": [
            "sanction percentage",
            "sanction rate",
            "sanction amount",
            "sanction",
        ],

        "reporting_change": [
            "report a change",
            "reporting a change",
            "report any change",
            "change of circumstances",
            "change in income",
        ],

        "overpayment": [
            "overpayment",
            "overpayment protection",
        ],
    }

    # ---------------------------------------------------------
    # Small ranking boosts.
    #
    # Explicit section references are strongest because the
    # user directly identified a policy provision.
    #
    # Concept matches receive a smaller boost.
    # ---------------------------------------------------------

    SECTION_BOOST = 0.15
    CONCEPT_BOOST = 0.08

    def __init__(self):

        if not INDEX_PATH.exists():
            raise FileNotFoundError(
                "FAISS index not found. "
                "Run: python -m src.retrieval.index"
            )

        if not METADATA_PATH.exists():
            raise FileNotFoundError(
                "Metadata not found. "
                "Run: python -m src.retrieval.index"
            )

        # -----------------------------------------------------
        # Load existing FAISS index
        # -----------------------------------------------------

        self.index = faiss.read_index(
            str(INDEX_PATH)
        )

        # -----------------------------------------------------
        # Load existing metadata
        # -----------------------------------------------------

        with open(
            METADATA_PATH,
            "r",
            encoding="utf-8",
        ) as file:

            self.metadata = json.load(file)

        # -----------------------------------------------------
        # Existing embedding model
        # -----------------------------------------------------

        self.embedder = PolicyEmbedder()

    def search(
        self,
        question: str,
        top_k: int = 5,
    ):
        """
        Retrieve policy provisions using the existing
        FAISS semantic retrieval engine.

        Explicit section references and policy concepts
        receive small ranking boosts.
        """

        # =====================================================
        # 1. FAISS semantic retrieval
        # =====================================================

        query_embedding = self.embedder.encode_query(
            question
        )

        query_embedding = np.asarray(
            query_embedding,
            dtype="float32",
        )

        # Retrieve a larger candidate pool before ranking.
        candidate_k = max(
            top_k * 3,
            10,
        )

        scores, indices = self.index.search(
            query_embedding,
            candidate_k,
        )

        results = []

        for score, index_position in zip(
            scores[0],
            indices[0],
        ):

            if index_position < 0:
                continue

            provision = self.metadata[
                int(index_position)
            ].copy()

            provision["score"] = float(score)

            results.append(
                provision
            )

        # =====================================================
        # 2. Detect explicit section references
        # =====================================================

        requested_sections = {
            self._normalize_section(section)
            for section in self.SECTION_PATTERN.findall(
                question
            )
        }

        # =====================================================
        # 3. Detect policy concepts in the question
        # =====================================================

        requested_concepts = self._detect_concepts(
            question
        )

        # =====================================================
        # 4. Apply targeted ranking boosts
        #
        # FAISS remains the primary retrieval mechanism.
        # =====================================================

        for result in results:

            citation = self._normalize_section(
                result.get(
                    "citation",
                    "",
                )
            )

            text = result.get(
                "text",
                "",
            ).lower()

            # -------------------------------------------------
            # Explicit section boost
            # -------------------------------------------------

            if citation in requested_sections:

                result["score"] += (
                    self.SECTION_BOOST
                )

            # -------------------------------------------------
            # Policy concept boost
            # -------------------------------------------------

            if requested_concepts:

                matched_concepts = (
                    self._matching_concepts(
                        text,
                        requested_concepts,
                    )
                )

                if matched_concepts:

                    result["score"] += (
                        self.CONCEPT_BOOST
                    )

        # =====================================================
        # 5. Sort by final score
        # =====================================================

        results.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        # =====================================================
        # 6. Return requested number of provisions
        # =====================================================

        return results[:top_k]

    # ---------------------------------------------------------
    # Detect concepts requested by the user.
    # ---------------------------------------------------------

    @classmethod
    def _detect_concepts(
        cls,
        question: str,
    ) -> set:

        question_lower = question.lower()

        concepts = set()

        for concept, phrases in (
            cls.CONCEPT_PATTERNS.items()
        ):

            if any(
                phrase in question_lower
                for phrase in phrases
            ):

                concepts.add(
                    concept
                )

        return concepts

    # ---------------------------------------------------------
    # Find which requested concepts are actually present
    # in a retrieved provision.
    # ---------------------------------------------------------

    @classmethod
    def _matching_concepts(
        cls,
        text: str,
        requested_concepts: set,
    ) -> set:

        matched = set()

        for concept in requested_concepts:

            phrases = cls.CONCEPT_PATTERNS.get(
                concept,
                [],
            )

            if any(
                phrase in text
                for phrase in phrases
            ):

                matched.add(
                    concept
                )

        return matched

    # ---------------------------------------------------------
    # Normalize policy section references.
    # ---------------------------------------------------------

    @staticmethod
    def _normalize_section(
        section: str,
    ) -> str:

        return re.sub(
            r"\s+",
            "",
            section.strip(),
        ).lower()


if __name__ == "__main__":

    retriever = PolicyRetriever()

    question = input(
        "\nAsk a policy question: "
    )

    results = retriever.search(
        question,
        top_k=5,
    )

    print(
        "\n========================================"
    )

    print(
        "RETRIEVED POLICY PROVISIONS"
    )

    print(
        "========================================"
    )

    for result in results:

        print(
            f"\n{result['citation']} "
            f"(score={result['score']:.4f})"
        )

        print(
            result["text"][:500]
        )