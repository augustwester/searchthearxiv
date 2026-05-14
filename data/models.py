from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingModel:
    name: str
    tokenizer: str
    max_tokens: int
    price_per_1k_tokens: float


EMBEDDING_ADA_002 = EmbeddingModel(
    name="text-embedding-ada-002",
    tokenizer="cl100k_base",
    max_tokens=8191,
    price_per_1k_tokens=0.0001,
)
