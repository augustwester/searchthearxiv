import json
import os
from collections.abc import Generator
from typing import Any

from models import EmbeddingModel
from openai import OpenAI
from paper import Paper
from pinecone import Pinecone
from tqdm import tqdm


def load_data(
    file_path: str, categories: list[str], start_year: int
) -> Generator[Paper]:
    """
    Returns a generator over the papers contained in `file_path`, belonging to
    the categories in `categories`, and published in or after `start_year`.

    Args:
        file_path: The path to the JSON file containing the arXiv data
        categories: A list of category strings
        start_year: An integer specifying the earliest year to include

    Returns:
        A generator over the papers satisfying the criteria.
    """
    with open(file_path, encoding="utf-8") as json_file:
        papers = (Paper(json.loads(line)) for line in json_file)
        filtered = (
            paper
            for paper in papers
            if paper.has_category(categories) and paper.has_valid_id
        )
        yield from (paper for paper in filtered if paper.year >= start_year)


def pinecone_embedding_count(index_name: str) -> int:
    """
    Helper function to get the total number of embeddings stored in the Pinecone
    index with the name specified in `index_name`.

    Args:
        index_name: The name of the Pinecone index

    Returns:
        The total number of embeddings stored in the Pinecone index.
    """
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index = pc.Index(index_name)
    return index.describe_index_stats()["total_vector_count"]


def estimate_embedding_price(
    token_counts: list[int], model: EmbeddingModel
) -> tuple[int, float]:
    """
    Estimates the price of embedding papers from pre-computed token counts.

    Args:
        token_counts: A list of token counts per paper
        model: An `EmbeddingModel` instance

    Returns:
        A tuple containing the total number of tokens and estimated price.
    """
    num_tokens = sum(token_counts)
    price = num_tokens / 1000 * model.price_per_1k_tokens
    return num_tokens, price


def get_embeddings(texts: list[str], model: EmbeddingModel) -> list[Any]:
    """
    Returns a list of embeddings for each string in `texts` using the OpenAI
    embedding model specified in `model`.

    Args:
        texts: A list of strings to embed
        model: An `EmbeddingModel` instance

    Returns:
        A list of embeddings.
    """
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return client.embeddings.create(input=texts, model=model.name).data


def embed_and_upsert(
    papers: list[Paper],
    index_name: str,
    model: EmbeddingModel,
    batch_size: int = 50,
) -> None:
    """
    Embeds the embedding text of each paper in `papers` using the embedding
    model specified in `model`. The embeddings are then upserted to the Pinecone
    index with name `index_name` in batches of size `batch_size`.

    Args:
        papers: The list of papers for which to embed their embedding text
        index_name: The name of the index in which the embeddings will be upserted
        model: An `EmbeddingModel` instance
        batch_size: The batch size to use when upserting embeddings to Pinecone
    """
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    with pc.Index(index_name, pool_threads=5) as index:
        for i in tqdm(range(0, len(papers), batch_size)):
            batch = papers[i : i + batch_size]
            texts = [paper.embedding_text for paper in batch]
            embed_data = get_embeddings(texts, model)

            pc_data = [
                (p.id, e.embedding, p.metadata)
                for p, e in zip(batch, embed_data, strict=True)
            ]
            index.upsert(pc_data)
