import argparse
import os
from pinecone import Pinecone
from helpers import load_data, pinecone_embedding_count, estimate_embedding_price, embed_and_upsert

if __name__ == "__main__":
    # parse command line flag
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-confirmation", action="store_true")
    args = parser.parse_args()
    no_confirmation = args.no_confirmation
    
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index_name = os.environ["PINECONE_INDEX_NAME"]
    
    # define constants
    JSON_FILE_PATH = "arxiv-metadata-oai-snapshot.json"
    CATEGORIES = ["cs.cv", "cs.lg", "cs.cl", "cs.ai", "cs.ne", "cs.ro"]
    START_YEAR = 2012
    EMBED_MODEL = "text-embedding-3-small"
    PRICE_PER_1K = 0.00002

    print("Loading data...")
    new_papers = list(load_data(JSON_FILE_PATH, CATEGORIES, START_YEAR))
    
    # a few papers are sometimes added to the dataset retroactively. since they
    # aren't appended to the file, identifying them are like finding a needle in
    # a haystack. here, we take the easy route and simply ignore them.
    existing_count = pinecone_embedding_count(index_name)
    est_num_new = len(new_papers) - existing_count
    assert est_num_new > 0, "No new papers. Aborting..."
    new_papers = new_papers[-est_num_new:]

    # if the index already has vectors, deduplicate by checking which papers
    # are already stored. skip this entirely for an empty index.
    if existing_count > 0:
        index = pc.Index(index_name)
        chunk_size, num_exist = 100, 0
        chunks = [new_papers[i:i+chunk_size] for i in range(0, len(new_papers), chunk_size)]
        for chunk in chunks:
            num_exist += len(index.fetch([p.id for p in chunk]).vectors)
        num_new = est_num_new - num_exist
        assert num_new > 0, "No new papers. Aborting..."
        new_papers = new_papers[-num_new:]
    else:
        num_new = est_num_new
    
    print(f"Estimating price of embedding {num_new} new papers...")
    est_num_tokens, est_price = estimate_embedding_price(new_papers, PRICE_PER_1K)
    
    print("Number of tokens for selected papers:", est_num_tokens)
    print(f"Estimated price: ${est_price}")
    
    if not no_confirmation:
        confirm = input("Type 'yes' if you wish to continue: ")
        assert confirm == "yes"
        
    print("Embedding and upserting...")
    embed_and_upsert(new_papers, index_name, EMBED_MODEL)
    
    print("✅ Retrieved and stored embeddings in Pinecone database")
