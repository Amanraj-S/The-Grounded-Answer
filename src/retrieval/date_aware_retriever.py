from datetime import date
from typing import Dict, List, Optional

from src.policy.effective_policy import EffectivePolicyResolver


class DateAwareRetriever:
    """
    Combines the real FAISS PolicyRetriever with
    date-aware policy resolution.

    FAISS determines WHICH provisions are relevant.

    EffectivePolicyResolver determines WHICH VERSION
    of those provisions applies.
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
        # 1. REAL FAISS RETRIEVAL
        # ---------------------------------------------

        retrieved = self.retriever.search(
            question,
            top_k=top_k,
        )

        effective_results = []

        # ---------------------------------------------
        # 2. APPLY EFFECTIVE POLICY VERSION
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
                    "id": result["id"],
                    "citation": effective.citation,
                    "text": effective.text,

                    # REAL FAISS SCORE
                    "score": result["score"],

                    "source": effective.source,
                    "version": effective.version,
                }
            )

        return effective_results