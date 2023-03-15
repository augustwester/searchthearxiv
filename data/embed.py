import argparse
import json
import openai
import os
import tiktoken
import pinecone
from tqdm import tqdm
from paper import Paper

def load_data(file_path, categories, start_year):
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
    json_file = open(file_path, "r", encoding="utf-8")
    papers = (Paper(json.loads(line)) for line in json_file)
    papers = (paper for paper in papers
              if paper.has_category(categories) and paper.has_valid_id)
    return (paper for paper in papers if paper.year >= start_year)

def pinecone_embedding_count(index_name):
    """
    Helper function to get the total number of embeddings stored in the Pinecone
    index with the name specified in `index_name`.
    
    Args:
        index_name: The name of the Pinecone index
        
    Returns:
        The total number of embeddings stored in the Pinecone index.
    """
    index = pinecone.Index(index_name)
    return index.describe_index_stats()["total_vector_count"]

def estimate_embedding_price(papers, price_per_1k):
    """
    Estimates the price of embedding the papers in `papers` using OpenAI's
    tiktoken tokenizer.
    
    Args:
        papers: A list of `Paper` objects
        price_per_1k: Price per 1000 tokens
    
    Returns:
        A tuple containing the estimated number of tokens and a price.
    """
    enc = tiktoken.get_encoding("gpt2")
    num_tokens = 0
    for paper in tqdm(papers):
        num_tokens += len(enc.encode(paper.embedding_text))
    price = num_tokens / 1000 * price_per_1k
    return num_tokens, price

def get_embeddings(texts, model="text-embedding-ada-002"):
    """
    Returns a list of embeddings for each string in `texts` using the OpenAI
    embedding model specified in `model`.
    
    Args:
        texts: A list of strings to embed
        model: The name of the OpenAI embedding model to use
        
    Returns:
        A list of embeddings.
    """
    embed_data = openai.Embedding.create(input=texts, model=model)
    return embed_data["data"]

def embed_and_upsert(papers, index_name, model, batch_size=100):
    """
    Embeds the embedding text of each paper in `papers` using the embedding
    model specified in `model`. The embeddings are then upserted to the Pinecone
    index with name `index_name` in batches of size `batch_size`.
    
    Args:
        papers: The list of papers for which to embed their embedding text
        index_name: The name of the index in which the embeddings will be upserted
        model: The name of the OpenAI embedding model to use
        batch_size: The batch size to use when upserting embeddings to Pinecone
    """
    with pinecone.Index(index_name, pool_threads=5) as index:
        for i in tqdm(range(0, len(papers), batch_size)):
            batch = papers[i:i+batch_size]
            texts = [paper.embedding_text for paper in batch]
            embed_data = get_embeddings(texts, model)
        
            pc_data = [(p.id, e["embedding"], p.metadata)
                       for p, e in zip(batch, embed_data)]
            index.upsert(pc_data)

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
