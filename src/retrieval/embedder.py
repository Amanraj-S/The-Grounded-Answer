from sentence_transformers import SentenceTransformer


class PolicyEmbedder:
    """
    Converts policy provisions and user questions
    into semantic vector embeddings.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        self.model = SentenceTransformer(model_name)

    def encode_documents(self, texts):
        """
        Convert policy provision texts into embeddings.
        """
        return self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True
        )

    def encode_query(self, query: str):
        """
        Convert a user question into a single embedding.
        """
        return self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )