import argparse
import openai
import os
import pinecone
from helpers import load_data, pinecone_embedding_count, estimate_embedding_price, embed_and_upsert

if __name__ == "__main__":
    # parse command line flag
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-confirmation", action="store_true")
    args = parser.parse_args()
    no_confirmation = args.no_confirmation
    
    # connect to OpenAI and Pinecone
    openai.api_key = os.environ["OPENAI_API_KEY"]
    pinecone.init(api_key=os.environ["PINECONE_API_KEY"])
    index_name = os.environ["PINECONE_INDEX_NAME"]
    
    # define constants
    JSON_FILE_PATH = "arxiv-metadata-oai-snapshot.json"
    CATEGORIES = ["cs.cv", "cs.lg", "cs.cl", "cs.ai", "cs.ne", "cs.ro"]
    START_YEAR = 2012
    EMBED_MODEL = "text-embedding-ada-002"
    PRICE_PER_1K = 0.0004

    print("Loading data...")
    papers = list(load_data(JSON_FILE_PATH, CATEGORIES, START_YEAR))
    
    # a few papers are sometimes added to the dataset retroactively. since they
    # aren't appended to the file, identifying them are like finding a needle in
    # a haystack. here, we take the easy route and simply ignore them.
    est_num_new = len(papers) - pinecone_embedding_count(index_name)
    assert est_num_new > 0, "No new papers. Aborting..."
    papers = papers[-est_num_new:]
    index = pinecone.Index(index_name)
    chunk_size, num_exist = 1000, 0
    chunks = [papers[i:i+chunk_size] for i in range(0, len(papers), chunk_size)]
    for chunk in chunks:
        num_exist += len(index.fetch([p.id for p in chunk])["vectors"])
    num_new = est_num_new - num_exist
    assert num_new > 0, "No new papers. Aborting..."
    papers = papers[-num_new:]
    
    print(f"Estimating price of embedding {num_new} new papers...")
    est_num_tokens, est_price = estimate_embedding_price(papers, PRICE_PER_1K)
    
    print("Number of tokens for selected papers:", est_num_tokens)
    print(f"Estimated price: ${est_price}")
    
    if not no_confirmation:
        confirm = input("Type 'yes' if you wish to continue: ")
        assert confirm == "yes"
        
    print("Embedding and upserting...")
    embed_and_upsert(papers, index_name, EMBED_MODEL)
    
    print("✅ Retrieved and stored embeddings in Pinecone database")
