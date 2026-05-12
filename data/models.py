from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingModel:
    name: str
    tokenizer: str
    max_tokens: int
    price_per_1k_tokens: float


EMBEDDING_3_SMALL = EmbeddingModel(
    name="text-embedding-3-small",
    tokenizer="cl100k_base",
    max_tokens=8192,
    price_per_1k_tokens=0.00002,
)
