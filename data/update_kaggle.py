import json
import logging
import os

from helpers import pinecone_embedding_count
from paper import Paper
from pinecone import Pinecone
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

logger.info("Preparing Kaggle dataset update...")

# define constants
ARXIV_FILE_PATH = "arxiv-metadata-oai-snapshot.json"
EMBEDDING_FILE_PATH = "ml-arxiv-embeddings.json"
CATEGORIES = ["cs.cv", "cs.lg", "cs.cl", "cs.ai", "cs.ne", "cs.ro"]
START_YEAR = 2012

# infer number of new papers
with open(EMBEDDING_FILE_PATH) as f:
    num_kaggle = sum(1 for _ in f)
index_name = os.environ["PINECONE_INDEX_NAME"]
num_pinecone = pinecone_embedding_count(index_name)
num_new = num_pinecone - num_kaggle
logger.info("Found %d new papers", num_new)

logger.info("Loading metadata for new papers...")
with open(ARXIV_FILE_PATH, encoding="utf-8") as arxiv_file:
    papers_gen = (json.loads(line) for line in arxiv_file)
    papers_filtered = (
        paper
        for paper in papers_gen
        if Paper(paper).has_category(CATEGORIES) and Paper(paper).has_valid_id
    )
    papers = list(papers_filtered)[-num_new:]

logger.info("Adding new metadata and embeddings to dataset...")
chunk_size = 1000
chunks = [papers[i : i + chunk_size] for i in range(0, len(papers), chunk_size)]

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index(index_name)

for chunk in chunks:
    embeds = index.fetch([p["id"] for p in chunk]).vectors
    for paper in tqdm(chunk):
        if paper["id"] in embeds:
            embed = embeds[paper["id"]]["values"]
            paper["embedding"] = embed
        else:
            logger.warning(
                "Unable to find paper with id '%s' in Pinecone",
                paper["id"],
            )

with open(EMBEDDING_FILE_PATH, "a") as file:
    for paper in tqdm(papers):
        print(json.dumps(paper), file=file)

logger.info("Added new metadata and embeddings to dataset")
