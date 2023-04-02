import os
import json
import pinecone
from paper import Paper
from helpers import pinecone_embedding_count
from tqdm import tqdm

print("Preparing Kaggle dataset update...")

# define constants
ARXIV_FILE_PATH = "arxiv-metadata-oai-snapshot.json"
EMBEDDING_FILE_PATH = "ml-arxiv-embeddings.json"
CATEGORIES = ["cs.cv", "cs.lg", "cs.cl", "cs.ai", "cs.ne", "cs.ro"]
START_YEAR = 2012

# infer number of new papers
num_kaggle = sum(1 for _ in open(EMBEDDING_FILE_PATH))
index_name = os.environ["PINECONE_INDEX_NAME"]
num_pinecone = pinecone_embedding_count(index_name)
num_new = num_pinecone - num_kaggle
print(f"Found {num_new} new papers")

print("Loading metadata for new papers...")
arxiv_file = open(ARXIV_FILE_PATH, "r", encoding="utf-8")
papers = (json.loads(line) for line in arxiv_file)
papers = (paper for paper in papers
          if Paper(paper).has_category(CATEGORIES) and Paper(paper).has_valid_id)
papers = list(papers)[-num_new:]

print("Adding new metadata and embeddings to dataset...")
chunk_size = 1000
chunks = [papers[i:i+chunk_size] for i in range(0, len(papers), chunk_size)]
index = pinecone.Index(index_name)
for chunk in chunks:
    embeds = index.fetch([p["id"] for p in chunk])["vectors"]
    for paper in tqdm(chunk):
        embed = embeds[paper["id"]]["values"]
        paper["embedding"] = embed

with open(EMBEDDING_FILE_PATH, "a") as file:
    for paper in tqdm(papers):
        print(json.dumps(paper), file=file)

print("✅ Added new metadata and embeddings to dataset")