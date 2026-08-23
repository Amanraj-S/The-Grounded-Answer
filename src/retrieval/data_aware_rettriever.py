from datetime import date
from typing import Dict, List, Optional

from src.policy.effective_policy import EffectivePolicyResolver


class DateAwareRetriever:
    """
    Combines the existing FAISS retriever with the
    date-aware policy layer.

    FAISS finds the relevant policy provisions.

    EffectivePolicyResolver determines whether the
    original or amended wording applies.
    """

    def __init__(
        self,
        retriever,
        provisions: List[Dict],
        amendments,
    ):

        self.retriever = retriever

        self.effective_policy = EffectivePolicyResolver(
            provisions=provisions,
            amendments=amendments,
        )

    def search(
        self,
        question: str,
        topic: str,
        change_date: Optional[date] = None,
        determination_date: Optional[date] = None,
        top_k: int = 5,
    ) -> List[Dict]:

        # ---------------------------------------------
        # STEP 1
        # Let FAISS retrieve the relevant provisions.
        # ---------------------------------------------

        retrieved = self.retriever.search(
            question,
            top_k=top_k,
        )

        effective_results = []

        # ---------------------------------------------
        # STEP 2
        # Apply the correct policy version to each
        # retrieved provision.
        # ---------------------------------------------

        for result in retrieved:

            section = result["id"]

            effective = self.effective_policy.get_provision(
                section=section,
                topic=topic,
                change_date=change_date,
                determination_date=determination_date,
            )

            effective_results.append(
                {
                    "id": effective.citation.replace(
                        "§",
                        ""
                    ),

                    "citation": effective.citation,

                    "text": effective.text,

                    # IMPORTANT:
                    # This is the REAL FAISS score.
                    "score": result["score"],

                    "source": effective.source,

                    "version": effective.version,
                }
            )

        return effective_results