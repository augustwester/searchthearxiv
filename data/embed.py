import argparse
import logging
import os

import tiktoken
from helpers import (
    embed_and_upsert,
    estimate_embedding_price,
    load_data,
    pinecone_embedding_count,
)
from models import EMBEDDING_ADA_002
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # parse command line flag
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-confirmation", action="store_true")
    args = parser.parse_args()
    no_confirmation = args.no_confirmation

    index_name = os.environ["PINECONE_INDEX_NAME"]

    # define constants
    JSON_FILE_PATH = "arxiv-metadata-oai-snapshot.json"
    CATEGORIES = ["cs.cv", "cs.lg", "cs.cl", "cs.ai", "cs.ne", "cs.ro"]
    START_YEAR = 2012

    logger.info("Loading data...")
    papers = list(load_data(JSON_FILE_PATH, CATEGORIES, START_YEAR))

    # tokenize each paper and filter out those exceeding the model's token limit
    enc = tiktoken.get_encoding(EMBEDDING_ADA_002.tokenizer)
    filtered_papers = []
    token_counts = []
    num_skipped = 0

    for paper in tqdm(papers, desc="Tokenizing"):
        count = len(enc.encode(paper.embedding_text, disallowed_special=()))
        if count > EMBEDDING_ADA_002.max_tokens:
            num_skipped += 1
        else:
            filtered_papers.append(paper)
            token_counts.append(count)

    papers = filtered_papers

    if num_skipped > 0:
        logger.info(
            "Skipped %d papers exceeding %d token limit",
            num_skipped,
            EMBEDDING_ADA_002.max_tokens,
        )

    # estimate the number of new papers by comparing the total number of
    # papers to the number already in Pinecone. any duplicates will be
    # overwritten on upsert, so exact deduplication is not necessary.
    num_new = len(papers) - pinecone_embedding_count(index_name)
    assert num_new > 0, "No new papers. Aborting..."
    papers = papers[-num_new:]
    token_counts = token_counts[-num_new:]

    # estimate embedding cost from pre-computed token counts
    est_num_tokens, est_price = estimate_embedding_price(
        token_counts, EMBEDDING_ADA_002
    )

    logger.info("Embedding %d new papers...", num_new)
    logger.info("Estimated tokens: %d", est_num_tokens)
    logger.info("Estimated price: $%s", est_price)

    if not no_confirmation:
        confirm = input("Type 'yes' if you wish to continue: ")
        assert confirm == "yes"

    logger.info("Embedding and upserting...")
    embed_and_upsert(papers, index_name, EMBEDDING_ADA_002)

    logger.info("Retrieved and stored embeddings in Pinecone database")
