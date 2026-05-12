import argparse
import os
import tiktoken
from tqdm import tqdm
from helpers import load_data, pinecone_embedding_count, estimate_embedding_price, embed_and_upsert
from models import EMBEDDING_3_SMALL

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

    print("Loading data...")
    papers = list(load_data(JSON_FILE_PATH, CATEGORIES, START_YEAR))
    
    # tokenize each paper and filter out those exceeding the model's token limit
    enc = tiktoken.get_encoding(EMBEDDING_3_SMALL.tokenizer)
    filtered_papers = []
    token_counts = []
    num_skipped = 0

    for paper in tqdm(papers, desc="Tokenizing"):
        count = len(enc.encode(paper.embedding_text, disallowed_special=()))
        if count > EMBEDDING_3_SMALL.max_tokens:
            num_skipped += 1
        else:
            filtered_papers.append(paper)
            token_counts.append(count)

    papers = filtered_papers

    if num_skipped > 0:
        print(f"Skipped {num_skipped} papers exceeding {EMBEDDING_3_SMALL.max_tokens} token limit")
    
    # estimate the number of new papers by comparing the total number of
    # papers to the number already in Pinecone. any duplicates will be
    # overwritten on upsert, so exact deduplication is not necessary.
    num_new = len(papers) - pinecone_embedding_count(index_name)
    assert num_new > 0, "No new papers. Aborting..."
    papers = papers[-num_new:]
    token_counts = token_counts[-num_new:]
    
    # estimate embedding cost from pre-computed token counts
    est_num_tokens, est_price = estimate_embedding_price(token_counts, EMBEDDING_3_SMALL)
    
    print(f"Embedding {num_new} new papers...")
    print(f"Estimated tokens: {est_num_tokens}")
    print(f"Estimated price: ${est_price}")
    
    if not no_confirmation:
        confirm = input("Type 'yes' if you wish to continue: ")
        assert confirm == "yes"
        
    print("Embedding and upserting...")
    embed_and_upsert(papers, index_name, EMBEDDING_3_SMALL)
    
    print("✅ Retrieved and stored embeddings in Pinecone database")
