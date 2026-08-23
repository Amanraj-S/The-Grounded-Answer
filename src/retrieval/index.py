import json
from pathlib import Path

import faiss
import numpy as np

from src.ingestion.parser import parse_policy
from src.retrieval.embedder import PolicyEmbedder


DATA_PATH = "data/policy-manual.md"
INDEX_DIR = Path("index")

FAISS_PATH = INDEX_DIR / "policy.index"
METADATA_PATH = INDEX_DIR / "metadata.json"


def build_index():

    print("Loading policy manual...")

    provisions = parse_policy(DATA_PATH)

    if not provisions:
        raise RuntimeError(
            "No policy provisions were found."
        )

    print(
        f"Loaded {len(provisions)} policy provisions."
    )

    texts = [
        provision["text"]
        for provision in provisions
    ]

    print("Loading embedding model...")

    embedder = PolicyEmbedder()

    print("Creating embeddings...")

    embeddings = embedder.encode_documents(texts)

    embeddings = np.asarray(
        embeddings,
        dtype="float32"
    )

    dimension = embeddings.shape[1]

    print(
        f"Embedding dimension: {dimension}"
    )

    # Because embeddings are normalized,
    # inner product behaves like cosine similarity.
    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    INDEX_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    faiss.write_index(
        index,
        str(FAISS_PATH)
    )

    with open(
        METADATA_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            provisions,
            file,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("========================================")
    print("INDEX BUILD COMPLETE")
    print("========================================")
    print(f"Provisions: {len(provisions)}")
    print(f"FAISS index: {FAISS_PATH}")
    print(f"Metadata: {METADATA_PATH}")


if __name__ == "__main__":
    build_index()