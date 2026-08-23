import json
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
    """

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

        self.index = faiss.read_index(
            str(INDEX_PATH)
        )

        with open(
            METADATA_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            self.metadata = json.load(file)

        self.embedder = PolicyEmbedder()

    def search(
        self,
        question: str,
        top_k: int = 5
    ):

        query_embedding = self.embedder.encode_query(
            question
        )

        query_embedding = np.asarray(
            query_embedding,
            dtype="float32"
        )

        scores, indices = self.index.search(
            query_embedding,
            top_k
        )

        results = []

        for score, index_position in zip(
            scores[0],
            indices[0]
        ):

            if index_position < 0:
                continue

            provision = self.metadata[
                int(index_position)
            ].copy()

            provision["score"] = float(score)

            results.append(provision)

        return results


if __name__ == "__main__":

    retriever = PolicyRetriever()

    question = input(
        "\nAsk a policy question: "
    )

    results = retriever.search(
        question,
        top_k=5
    )

    print("\n========================================")
    print("RETRIEVED POLICY PROVISIONS")
    print("========================================")

    for result in results:

        print(
            f"\n{result['citation']} "
            f"(score={result['score']:.4f})"
        )

        print(result["text"][:500])